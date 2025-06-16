#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
�� 青空文庫5作品→完全地名フロー最終版 v4

地名抽出エラーを修正し、正確な処理を実行
統合地名抽出・正規化システムを使用
"""

import sys
import os
import sqlite3
import requests
import re
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# v4パスを追加
sys.path.insert(0, '/app/bungo-map-v4')

# v4システムをインポート
from src.bungo_map.database.manager import DatabaseManager
from src.bungo_map.extractors_v4.unified_place_extractor import UnifiedPlaceExtractor
from src.bungo_map.extractors_v4.place_normalizer import PlaceNormalizer

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FinalWorkflowExecutor:
    """最終版完全フロー実行システム v4"""
    
    def __init__(self, db_path: str = '/app/bungo-map-v4/data/databases/bungo_v4.db'):
        self.db_path = db_path
        
        logger.info("🔧 最終版完全フロー実行システムv4初期化中...")
        
        # v4システム初期化
        self.db_manager = DatabaseManager(db_path)
        self.unified_extractor = UnifiedPlaceExtractor()
        self.normalizer = PlaceNormalizer()
        
        logger.info("✅ v4統合システム初期化完了")
    
    def execute_place_extraction_and_geocoding(self):
        """地名抽出とGeocodingの実行"""
        logger.info("🚀 最終版地名抽出+Geocoding実行開始")
        logger.info("=" * 80)
        
        # フェーズ1: 既存データの確認
        logger.info("\n📊 フェーズ1: 既存データ確認")
        logger.info("-" * 50)
        
        stats = self._get_current_statistics()
        logger.info(f"👥 作家数: {stats['authors']:,}")
        logger.info(f"📚 作品数: {stats['works']:,}")
        logger.info(f"📝 センテンス数: {stats['sentences']:,}")
        logger.info(f"🗺️ 既存地名数: {stats['places']:,}")
        logger.info(f"🔗 既存文-地名関係数: {stats['sentence_places']:,}")
        
        # フェーズ2: 地名抽出実行
        logger.info("\n🗺️ フェーズ2: 全センテンス地名抽出実行")
        logger.info("-" * 50)
        
        total_extracted = self._extract_all_places()
        logger.info(f"\n✅ フェーズ2完了: {total_extracted}件の新規地名抽出")
        
        # フェーズ3: 統計情報の更新
        logger.info("\n📊 フェーズ3: 統計情報更新")
        logger.info("-" * 50)
        
        self._update_all_statistics()
        logger.info("\n✅ フェーズ3完了: 統計情報更新完了")
        
        # 最終統計
        logger.info("\n📊 フェーズ4: 最終統計表示")
        logger.info("-" * 50)
        self._show_comprehensive_statistics()
        
        logger.info(f"\n🎉 最終版完全フロー実行完了！")
    
    def _get_current_statistics(self) -> Dict[str, int]:
        """現在の統計情報取得"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            cursor = conn.execute("SELECT COUNT(*) FROM authors")
            stats['authors'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM works")
            stats['works'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM sentences")
            stats['sentences'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM places_master")
            stats['places'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM sentence_places")
            stats['sentence_places'] = cursor.fetchone()[0]
            
            return stats
    
    def _extract_all_places(self) -> int:
        """全センテンスの地名抽出"""
        total_extracted = 0
        
        try:
            # 全センテンス取得
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT s.sentence_id, s.sentence_text, s.before_text, s.after_text, s.work_id, s.author_id
                    FROM sentences s
                    WHERE length(s.sentence_text) > 5
                    ORDER BY s.work_id, s.position_in_work
                """)
                all_sentences = cursor.fetchall()
                
                logger.info(f"📝 処理対象センテンス: {len(all_sentences):,}件")
            
            # 地名抽出処理
            for i, (sentence_id, sentence_text, before_text, after_text, work_id, author_id) in enumerate(all_sentences):
                if i > 0 and i % 1000 == 0:
                    logger.info(f"  📍 進捗: {i:,}/{len(all_sentences):,} ({i/len(all_sentences)*100:.1f}%)")
                
                try:
                    # 作品の処理
                    result = self.db_manager.process_work(
                        work_id=work_id,
                        text=sentence_text,
                        context_before=before_text,
                        context_after=after_text
                    )
                    
                    if result['success']:
                        total_extracted += len(result['saved_places'])
                        
                        if result['saved_places']:
                            place_names = [p['place_name'] for p in result['saved_places']]
                            logger.info(f"    🗺️ 抽出: {', '.join(place_names)}")
                
                except Exception as e:
                    logger.error(f"    ⚠️ センテンス処理エラー: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"❌ 地名抽出エラー: {e}")
        
        return total_extracted
    
    def _update_all_statistics(self):
        """全統計情報の更新"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 作品の統計更新
                cursor = conn.execute("SELECT work_id FROM works")
                work_ids = [row[0] for row in cursor.fetchall()]
                
                for work_id in work_ids:
                    try:
                        stats = self.db_manager.get_work_statistics(work_id)
                        if stats:
                            logger.info(f"  📚 作品統計更新: {stats['work_title']}")
                            logger.info(f"    地名数: {stats['unique_places']}, 言及回数: {stats['total_mentions']}")
                    except Exception as e:
                        logger.error(f"    ⚠️ 作品統計更新エラー (ID: {work_id}): {e}")
                
                # 作者の統計更新
                cursor = conn.execute("SELECT author_id FROM authors")
                author_ids = [row[0] for row in cursor.fetchall()]
                
                for author_id in author_ids:
                    try:
                        stats = self.db_manager.get_author_statistics(author_id)
                        if stats:
                            logger.info(f"  👤 作者統計更新: {stats['author_name']}")
                            logger.info(f"    作品数: {stats['work_count']}, 地名数: {stats['unique_places']}")
                    except Exception as e:
                        logger.error(f"    ⚠️ 作者統計更新エラー (ID: {author_id}): {e}")
        
        except Exception as e:
            logger.error(f"❌ 統計更新エラー: {e}")
    
    def _show_comprehensive_statistics(self):
        """包括的統計表示"""
        with sqlite3.connect(self.db_path) as conn:
            # 基本統計
            final_stats = self._get_current_statistics()
            
            # 作品別統計
            cursor = conn.execute("""
                SELECT 
                    a.author_name, w.work_title, w.sentence_count,
                    COUNT(DISTINCT pm.place_id) as unique_places,
                    COUNT(sp.id) as total_mentions
                FROM authors a
                JOIN works w ON a.author_id = w.author_id
                LEFT JOIN sentences s ON w.work_id = s.work_id
                LEFT JOIN sentence_places sp ON s.sentence_id = sp.sentence_id
                LEFT JOIN places_master pm ON sp.place_id = pm.place_id
                GROUP BY a.author_id, w.work_id
                ORDER BY w.created_at DESC
            """)
            work_stats = cursor.fetchall()
            
            # 頻出地名TOP10
            cursor = conn.execute("""
                SELECT 
                    pm.place_name, 
                    pm.canonical_name,
                    pm.place_type,
                    pm.prefecture,
                    pm.mention_count
                FROM places_master pm
                WHERE pm.mention_count > 0
                ORDER BY pm.mention_count DESC
                LIMIT 10
            """)
            top_places = cursor.fetchall()
        
        logger.info("📊 最終統計レポート")
        logger.info("=" * 60)
        logger.info(f"👥 作家数: {final_stats['authors']:,}")
        logger.info(f"📚 作品数: {final_stats['works']:,}")
        logger.info(f"📝 センテンス数: {final_stats['sentences']:,}")
        logger.info(f"🗺️ 総地名数: {final_stats['places']:,}")
        logger.info(f"🔗 文-地名関係数: {final_stats['sentence_places']:,}")
        
        logger.info(f"\n📖 作品別地名統計:")
        for author, title, sentences, unique_places, total_mentions in work_stats:
            if unique_places > 0:
                logger.info(f"  • {author} - {title}: {unique_places}地名, {total_mentions}回言及")
        
        if top_places:
            logger.info(f"\n🗺️ 頻出地名TOP10:")
            for place_name, canonical_name, place_type, prefecture, count in top_places:
                logger.info(f"  • {place_name} → {canonical_name}")
                logger.info(f"    タイプ: {place_type}")
                if prefecture:
                    logger.info(f"    都道府県: {prefecture}")
                logger.info(f"    言及回数: {count}回")


def main():
    """メイン実行関数"""
    logger.info("🗾 最終版青空文庫地名抽出+Geocoding実行")
    logger.info("=" * 80)
    
    executor = FinalWorkflowExecutor()
    executor.execute_place_extraction_and_geocoding()


if __name__ == "__main__":
    main() 