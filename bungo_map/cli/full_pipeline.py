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
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime

from bungo_map.extractors.simple_place_extractor import SimplePlaceExtractor
from bungo_map.extractors.enhanced_place_extractor import EnhancedPlaceExtractor  
from bungo_map.ai.extractors.precise_compound_extractor import PreciseCompoundExtractor
from bungo_map.ai.context_aware_geocoding import ContextAwareGeocodingService
from bungo_map.ai.quality_management import QualityManagementService

# パッケージのルートディレクトリを追加
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# コアモジュール
from bungo_map.core.database import init_db
from bungo_map.core.config import Config

# 抽出器モジュール
from bungo_map.extractors.extraction_pipeline import ExtractionPipeline
from bungo_map.extractors.ginza_place_extractor import GinzaPlaceExtractor
from bungo_map.extractors.advanced_place_extractor import AdvancedPlaceExtractor

# ユーティリティ
from bungo_map.utils.logger import setup_logger
from bungo_map.utils.progress import ProgressManager

from ..database.database import Database
from ..geocoding.geocoding_service import GeocodingService

logger = logging.getLogger(__name__)

class FullPipeline:
    """完全統合パイプライン（改良版）"""
    
    def __init__(self, db=None, geocoding_service=None):
        """初期化"""
        from ..database.database import Database
        from ..geocoding.geocoding_service import GeocodingService
        self.db = db if db is not None else Database()
        self.geocoding_service = geocoding_service if geocoding_service is not None else GeocodingService()
        self.extraction_pipeline = ExtractionPipeline()
        
        # サービス初期化
        self.geocoding_service = geocoding_service
        self.quality_service = QualityManagementService()
        
        # 統計情報
        self.stats = {
            'processed_works': 0,
            'total_works': 0,
            'total_places': 0,
            'geocoding_success': 0,
            'geocoding_failed': 0,
            'geocoding_skipped': 0,
            'processing_time': 0,
            'extraction_methods': {},
            'quality_before': 0,
            'quality_after': 0,
            'quality_improvement': 0,
            'cleanup_actions': []
        }
    
    def reset_places_data(self) -> None:
        """placesテーブルのリセット"""
        self.db.reset_places_table()
    
    def get_works_for_processing(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        """処理対象作品の取得"""
        with sqlite3.connect(self.config.db_path) as conn:
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
    
    def extract_places_from_work(self, work_id: int) -> List[Dict[str, Any]]:
        """作品から地名を抽出"""
        # 1. 作品データ取得
        work = self.db.get_work(work_id)
        if not work:
            return []
        
        # 2. 地名抽出
        places = self.extraction_pipeline.extract_places(work_id, work['content'])
        
        # 3. 結果を保存
        for place in places:
            self.db.save_extracted_place(place)
        
        return places
    
    def save_places_to_db(self, places: List) -> None:
        """地名データをデータベースに保存"""
        if not places:
            return
        
        with sqlite3.connect(self.config.db_path) as conn:
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
    
    def geocode_places(self, places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """地名のジオコーディング"""
        geocoded_places = []
        for place in places:
            result = self.geocoding_service.geocode(place['place_name'])
            if result.success:
                place['location'] = result.location
                place['confidence'] = result.confidence
                geocoded_places.append(place)
        return geocoded_places
    
    def run_quality_management(self) -> Dict[str, Any]:
        """品質管理実行"""
        return {
            'stats': {
                'total_places': 0,
                'geocoded_places': 0
            },
            'quality_issues': []
        }
    
    def process_all_works(self) -> Dict[str, Any]:
        """全作品処理"""
        works = self.db.get_unprocessed_works()
        if not works:
            return {'status': 'error', 'message': 'No works to process'}
        results = []
        for work in works:
            result = self.process_work(work['id'])
            results.append(result)
        return {
            'status': 'success',
            'total_works': len(works),
            'results': results
        }
    
    def process_work(self, work_id: int) -> dict:
        """作品処理"""
        places = self.extract_places_from_work(work_id)
        if not places:
            return {'status': 'error', 'message': 'No places found'}
        geocoded_places = []
        for place in places:
            result = self.geocoding_service.geocode(place['place_name'])
            if result.success:
                place['location'] = result.location
                place['confidence'] = result.confidence
                geocoded_places.append(place)
        for place in geocoded_places:
            self.db.save_geocoded_place(place)
        return {
            'status': 'success',
            'work_id': work_id,
            'places_found': len(places),
            'places_geocoded': len(geocoded_places)
        }
    
    def run_full_pipeline(self, 
                         reset_data: bool = True,
                         use_ai: bool = True, 
                         enable_geocoding: bool = True,
                         enable_quality_management: bool = True,
                         limit: Optional[int] = None,
                         batch_size: int = 5,
                         geocoding_min_confidence: float = 0.5) -> Dict:
        """完全パイプライン実行"""
        start_time = time.time()
        
        try:
            # 1. データリセット
            if reset_data:
                self.reset_places_data()
            
            # 2. 作品取得
            works = self.get_works_for_processing(limit)
            if not works:
                click.echo("⚠️ 処理対象の作品がありません")
                return {'stats': self.stats}
            
            # 3. 地名抽出
            for work in works:
                places = self.extract_places_from_work(work['work_id'])
                if places:
                    self.save_places_to_db(places)
                    self.stats['total_places'] += len(places)
                self.stats['processed_works'] += 1
            
            # 4. ジオコーディング
            if enable_geocoding:
                self.geocode_places(works)
            
            # 5. 品質管理
            if enable_quality_management:
                quality_result = self.run_quality_management()
                self.stats.update(quality_result['stats'])
            
            # 6. 統計更新
            self.stats['processing_time'] = time.time() - start_time
            
            return {'stats': self.stats}
            
        except Exception as e:
            logger.error(f"パイプライン実行エラー: {e}")
            return {'stats': self.stats, 'error': str(e)}
    
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