#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 文豪地図 完全統合パイプライン（改良版）
新データ追加時の自動品質管理対応

Features:
- 複数抽出器の統合
- AI文脈判断型Geocoding
- 自動品質管理
- 新データ検知とクリーンアップ
- 統計レポート
"""

import sqlite3
import time
import logging
import click
from typing import List, Dict, Optional

from bungo_map.extractors.simple_place_extractor import SimplePlaceExtractor
from bungo_map.extractors.enhanced_place_extractor import EnhancedPlaceExtractor  
from bungo_map.ai.extractors.precise_compound_extractor import PreciseCompoundExtractor
from bungo_map.ai.context_aware_geocoding import ContextAwareGeocodingService

# パッケージのルートディレクトリを追加
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger(__name__)

class FullPipeline:
    """完全統合パイプライン（改良版）"""
    
    def __init__(self, db_path: str = 'data/bungo_production.db'):
        """初期化"""
        self.db_path = db_path
        # self.db = Database(db_path)
        self.simple_extractor = SimplePlaceExtractor()
        self.enhanced_extractor = EnhancedPlaceExtractor()
        self.ai_extractor = PreciseCompoundExtractor()
        self.geocoding_service = ContextAwareGeocodingService()  # AI文脈判断型に変更
        self.batch_size = 10
        self.use_ai = True
        self.use_geocoding = True
        self.geocoding_confidence_threshold = 0.3
        
        # 🆕 品質管理システムの初期化
        try:
            from comprehensive_cleanup import ComprehensiveCleanup
            self.quality_manager = ComprehensiveCleanup(db_path)
        except ImportError:
            logger.warning("⚠️ 品質管理システムが見つかりません")
            self.quality_manager = None
        
        # 統計情報
        self.stats = {
            'total_works': 0,
            'processed_works': 0,
            'total_places': 0,
            'extraction_methods': {},
            'geocoding_success': 0,
            'geocoding_failed': 0,
            'geocoding_skipped': 0,
            'processing_time': 0,
            'quality_before': 0,
            'quality_after': 0,
            'quality_improvement': 0,
            'cleanup_actions': []
        }
    
    def reset_places_data(self) -> None:
        """placesテーブルを初期化"""
        click.echo("🧹 placesテーブル初期化中...")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM places")
            conn.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'places'")
            conn.commit()
        
        # VACUUMは別接続で実行
        conn = sqlite3.connect(self.db_path)
        conn.execute("VACUUM")
        conn.close()
        
        click.echo("✅ placesテーブル初期化完了")
    
    def get_works_for_processing(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        """処理対象作品の取得"""
        with sqlite3.connect(self.db_path) as conn:
            if limit:
                cursor = conn.execute("""
                    SELECT w.work_id, w.title, a.name as author_name, w.content, w.aozora_url 
                    FROM works w 
                    JOIN authors a ON w.author_id = a.author_id
                    WHERE w.content IS NOT NULL AND w.content != ''
                    ORDER BY w.work_id LIMIT ? OFFSET ?
                """, (limit, offset))
            else:
                cursor = conn.execute("""
                    SELECT w.work_id, w.title, a.name as author_name, w.content, w.aozora_url 
                    FROM works w 
                    JOIN authors a ON w.author_id = a.author_id
                    WHERE w.content IS NOT NULL AND w.content != ''
                    ORDER BY w.work_id
                """)
            
            works = [
                {
                    'work_id': row[0], 'title': row[1], 'author_name': row[2], 
                    'content': row[3], 'aozora_url': row[4]
                }
                for row in cursor.fetchall()
            ]
        
        self.stats['total_works'] = len(works)
        return works
    
    def extract_places_from_work(self, work_data: Dict, use_ai: bool = True) -> List:
        """作品から地名抽出"""
        work_id = work_data['work_id']
        title = work_data['title']
        content = work_data['content']
        all_places = []
        
        try:
            # 1. 強化版地名抽出（青空文庫処理 + 適切な文脈取得）
            enhanced_places = self.enhanced_extractor.extract_places_from_work(
                work_id, content
            )
            
            # 2. SimplePlaceと互換フォーマットに変換
            simple_places = self.enhanced_extractor.convert_to_simple_places(enhanced_places)
            all_places.extend(simple_places)
            
            # 3. AI複合地名抽出（青空文庫クリーナー統合済み）
            if use_ai:
                try:
                    ai_places = self.ai_extractor.extract_precise_places(work_id, content)
                    all_places.extend(ai_places)
                except Exception as e:
                    logger.warning(f"AI抽出エラー: {title} - {e}")
            
            # 統計更新
            for place in all_places:
                method = place.extraction_method
                self.stats['extraction_methods'][method] = self.stats['extraction_methods'].get(method, 0) + 1
            
            logger.info(f"✅ '{title}': {len(all_places)}件の地名抽出")
            
        except Exception as e:
            logger.error(f"❌ '{title}' 抽出エラー: {e}")
        
        return all_places
    
    def save_places_to_db(self, places: List) -> None:
        """地名データをデータベースに保存"""
        if not places:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            for place in places:
                conn.execute("""
                    INSERT INTO places (work_id, place_name, before_text, sentence, after_text, 
                                      aozora_url, confidence, extraction_method)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    place.work_id, place.place_name, place.before_text, place.sentence,
                    place.after_text, place.aozora_url, place.confidence, place.extraction_method
                ))
            conn.commit()
    
    def geocode_places(self, batch_size: int = 50, min_confidence: float = 0.5) -> None:
        """地名のGeocoding処理"""
        click.echo("🗺️ Geocoding処理開始...")
        
        # 対象地名取得
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT place_id, place_name, confidence 
                FROM places 
                WHERE lat IS NULL AND lng IS NULL
                AND confidence >= ?
                ORDER BY confidence DESC, LENGTH(place_name) DESC
            """, (min_confidence,))
            places_to_geocode = cursor.fetchall()
        
        if not places_to_geocode:
            click.echo("⏭️ Geocoding対象地名がありません")
            return
        
        total_places = len(places_to_geocode)
        total_batches = (total_places + batch_size - 1) // batch_size
        
        click.echo(f"📍 Geocoding対象: {total_places}件 ({total_batches}バッチ)")
        
        for i in range(0, total_places, batch_size):
            batch = places_to_geocode[i:i + batch_size]
            batch_num = i//batch_size + 1
            
            click.echo(f"📦 Geocodingバッチ {batch_num}/{total_batches} ({len(batch)}件)")
            
            batch_updates = []
            
            for place_id, place_name, confidence in batch:
                # 低信頼度や明らかに地名でないものはスキップ
                if len(place_name) <= 1 or confidence < 0.3:
                    self.stats['geocoding_skipped'] += 1
                    continue
                
                # 文脈情報を取得してAI文脈判断型Geocoding実行
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT sentence, before_text, after_text 
                        FROM places WHERE place_id = ?
                    """, (place_id,))
                    context_data = cursor.fetchone()
                
                if context_data:
                    sentence, before_text, after_text = context_data
                    geocoding_result = self.geocoding_service.geocode_place_sync(
                        place_name=place_name,
                        sentence=sentence or "",
                        before_text=before_text or "",
                        after_text=after_text or ""
                    )
                else:
                    geocoding_result = self.geocoding_service.geocode_place_sync(place_name)
                
                if geocoding_result:
                    batch_updates.append((
                        geocoding_result.latitude,
                        geocoding_result.longitude,
                        geocoding_result.confidence,
                        geocoding_result.source,
                        geocoding_result.prefecture,
                        geocoding_result.city,
                        place_id
                    ))
                    self.stats['geocoding_success'] += 1
                else:
                    self.stats['geocoding_failed'] += 1
            
            # バッチ更新
            if batch_updates:
                with sqlite3.connect(self.db_path) as conn:
                    conn.executemany("""
                        UPDATE places SET 
                            lat = ?, lng = ?, geocoding_confidence = ?, geocoding_source = ?,
                            prefecture = ?, city = ?
                        WHERE place_id = ?
                    """, batch_updates)
                    conn.commit()
                
                click.echo(f"  ✅ {len(batch_updates)}件のGeocoding完了")
            
            # 進捗表示
            processed = min(i + batch_size, total_places)
            progress = (processed / total_places) * 100
            click.echo(f"  📊 進捗: {processed}/{total_places} ({progress:.1f}%)")
    
    def run_quality_management(self, auto_cleanup: bool = True) -> Dict:
        """🆕 品質管理の実行"""
        
        if not self.quality_manager:
            click.echo("⚠️ 品質管理システム無効")
            return {'quality_improvement': 0, 'actions_taken': []}
        
        click.echo("🧠 品質管理システム実行中...")
        
        # 新データ検知
        data_status = self.quality_manager.detect_new_data()
        before_score = self.quality_manager.get_quality_score()
        
        self.stats['quality_before'] = before_score
        
        click.echo(f"  📊 品質スコア: {before_score:.1f}/100")
        click.echo(f"  📊 新データ検知: {data_status['new_data_detected']}")
        click.echo(f"  📊 変更件数: {data_status['change_count']}")
        
        # 適応型クリーンアップ実行
        if auto_cleanup:
            result = self.quality_manager.run_adaptive_cleanup()
            
            after_score = result['after_score']
            improvement = result['improvement']
            
            self.stats['quality_after'] = after_score
            self.stats['quality_improvement'] = improvement
            self.stats['cleanup_actions'] = result['actions_taken']
            
            if improvement > 0:
                click.echo(f"  ✅ 品質改善: +{improvement:.1f}点")
                click.echo(f"  ⚡ アクション: {len(result['actions_taken'])}件")
                for action in result['actions_taken']:
                    click.echo(f"    - {action}")
            else:
                click.echo("  ✅ 品質良好: クリーンアップ不要")
        
        return {
            'quality_improvement': self.stats['quality_improvement'],
            'actions_taken': self.stats['cleanup_actions']
        }
    
    def run_full_pipeline(self, 
                         reset_data: bool = True,
                         use_ai: bool = True, 
                         enable_geocoding: bool = True,
                         enable_quality_management: bool = True,
                         limit: Optional[int] = None,
                         batch_size: int = 5,
                         geocoding_min_confidence: float = 0.5) -> Dict:
        """完全統合パイプライン実行（改良版）"""
        
        pipeline_start = time.time()
        
        if reset_data:
            self.reset_places_data()
        
        works = self.get_works_for_processing(limit)
        total_works = len(works)
        
        if total_works == 0:
            click.echo("⚠️ 処理対象の作品がありません")
            return {'stats': self.stats}
        
        click.echo(f"🚀 パイプライン開始: {total_works}作品")
        
        # バッチ処理
        for i in range(0, total_works, batch_size):
            batch = works[i:i + batch_size]
            batch_num = i//batch_size + 1
            total_batches = (total_works + batch_size - 1)//batch_size
            
            click.echo(f"📦 バッチ {batch_num}/{total_batches} ({len(batch)}作品)")
            
            batch_places = []
            for work in batch:
                places = self.extract_places_from_work(work, use_ai)
                batch_places.extend(places)
                self.stats['processed_works'] += 1
            
            # バッチ保存
            self.save_places_to_db(batch_places)
            self.stats['total_places'] += len(batch_places)
            
            click.echo(f"  ✅ {len(batch_places)}件の地名保存完了")
        
        # Geocoding処理
        if enable_geocoding:
            self.geocode_places(min_confidence=geocoding_min_confidence)
        
        # 🆕 品質管理実行
        if enable_quality_management:
            quality_result = self.run_quality_management(auto_cleanup=True)
        
        # 統計計算
        processing_time = time.time() - pipeline_start
        self.stats['processing_time'] = processing_time
        
        return {'stats': self.stats}
    
    def display_final_stats(self) -> None:
        """最終統計表示（改良版）"""
        click.echo("\n" + "=" * 60)
        click.echo("🎉 完全統合パイプライン完了！")
        click.echo("=" * 60)
        
        click.echo(f"📊 処理統計:")
        click.echo(f"  ✅ 処理作品: {self.stats['processed_works']}/{self.stats['total_works']}")
        click.echo(f"  📍 抽出地名: {self.stats['total_places']}件")
        click.echo(f"  ⏱️  処理時間: {self.stats['processing_time']:.1f}秒")
        
        if self.stats['total_places'] > 0:
            speed = self.stats['total_places'] / self.stats['processing_time']
            click.echo(f"  🚀 処理速度: {speed:.1f}件/秒")
        
        if self.stats['extraction_methods']:
            click.echo(f"\n📋 抽出手法別統計:")
            for method, count in sorted(self.stats['extraction_methods'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / self.stats['total_places']) * 100
                click.echo(f"  {method}: {count}件 ({percentage:.1f}%)")
        
        # Geocoding統計
        geocoding_total = self.stats['geocoding_success'] + self.stats['geocoding_failed']
        if geocoding_total > 0:
            success_rate = (self.stats['geocoding_success'] / geocoding_total) * 100
            click.echo(f"\n🗺️ Geocoding統計:")
            click.echo(f"  ✅ 成功: {self.stats['geocoding_success']}件")
            click.echo(f"  ❌ 失敗: {self.stats['geocoding_failed']}件")
            click.echo(f"  ⏭️  スキップ: {self.stats['geocoding_skipped']}件")
            click.echo(f"  📊 成功率: {success_rate:.1f}%")
        
        # 🆕 品質管理統計
        if self.stats['quality_improvement'] != 0:
            click.echo(f"\n🧠 品質管理統計:")
            click.echo(f"  📊 改善前品質: {self.stats['quality_before']:.1f}/100")
            click.echo(f"  📊 改善後品質: {self.stats['quality_after']:.1f}/100")
            click.echo(f"  📈 品質改善: +{self.stats['quality_improvement']:.1f}点")
            if self.stats['cleanup_actions']:
                click.echo(f"  ⚡ クリーンアップ:")
                for action in self.stats['cleanup_actions']:
                    click.echo(f"    - {action}")

@click.command()
@click.option('--reset-data/--no-reset', default=True, help='placesテーブルを初期化')
@click.option('--use-ai/--no-ai', default=True, help='AI複合地名抽出を使用')
@click.option('--geocoding/--no-geocoding', default=True, help='Geocoding処理を実行')
@click.option('--quality-management/--no-quality', default=True, help='品質管理を実行')
@click.option('--limit', type=int, help='処理作品数の制限')
@click.option('--batch-size', type=int, default=5, help='抽出バッチサイズ')
@click.option('--geocoding-confidence', type=float, default=0.5, help='Geocoding最小信頼度')
def main(reset_data: bool, use_ai: bool, geocoding: bool, quality_management: bool,
         limit: Optional[int], batch_size: int, geocoding_confidence: float):
    """文豪地図完全統合パイプライン（改良版）"""
    pipeline = FullPipeline()
    result = pipeline.run_full_pipeline(
        reset_data=reset_data,
        use_ai=use_ai,
        enable_geocoding=geocoding,
        enable_quality_management=quality_management,
        limit=limit,
        batch_size=batch_size,
        geocoding_min_confidence=geocoding_confidence
    )
    
    # 🆕 最終統計表示
    pipeline.display_final_stats()

if __name__ == '__main__':
    main() 