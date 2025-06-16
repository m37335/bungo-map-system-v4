#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベースマネージャー v4
地名抽出・正規化システムと連携したデータベース管理
"""

import sqlite3
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from ..extractors_v4.unified_place_extractor import UnifiedPlaceExtractor, UnifiedPlace
from ..extractors_v4.place_normalizer import PlaceNormalizer, NormalizedPlace
from .models import Work

logger = logging.getLogger(__name__)

class DatabaseManager:
    """データベースマネージャー v4"""
    
    def __init__(self, db_path: str = '/app/bungo-map-v4/data/databases/bungo_v4.db'):
        """初期化"""
        self.db_path = db_path
        logger.info(f"🌟 データベースマネージャーv4初期化: DBパス = {self.db_path}")
        self.unified_extractor = UnifiedPlaceExtractor()
        self.normalizer = PlaceNormalizer()
        logger.info("🌟 データベースマネージャーv4初期化完了")
    
    def process_work(self, work_id: int, text: str, context_before: str = "", context_after: str = "") -> Dict:
        """作品の処理"""
        try:
            # 地名抽出
            places = self.unified_extractor.extract_places(
                work_id, text, context_before, context_after
            )
            
            # データベースに保存
            saved_places = self._save_places(places)
            
            # 統計情報の更新
            self._update_statistics(work_id)
            
            return {
                'work_id': work_id,
                'total_places': len(places),
                'saved_places': saved_places,
                'success': True
            }
        
        except Exception as e:
            logger.error(f"作品処理エラー: {e}")
            return {
                'work_id': work_id,
                'error': str(e),
                'success': False
            }
    
    def _save_places(self, places: List[UnifiedPlace]) -> List[Dict]:
        """地名の保存"""
        saved_places = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                for place in places:
                    # places_masterに追加（重複チェック）
                    cursor = conn.execute("""
                        SELECT place_id FROM places_master 
                        WHERE canonical_name = ?
                    """, (place.canonical_name,))
                    
                    result = cursor.fetchone()
                    if result:
                        place_id = result[0]
                    else:
                        # 新規地名追加
                        cursor = conn.execute("""
                            INSERT INTO places_master (
                                place_name, canonical_name, place_type,
                                prefecture, confidence, verification_status,
                                created_at, updated_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            place.place_name,
                            place.canonical_name,
                            place.place_type,
                            place.prefecture,
                            place.confidence,
                            'pending',
                            place.created_at,
                            place.updated_at
                        ))
                        place_id = cursor.lastrowid
                    
                    # sentence_placesに追加
                    cursor = conn.execute("""
                        INSERT INTO sentence_places (
                            sentence_id, place_id, extraction_method,
                            confidence, context_before, context_after,
                            matched_text, verification_status,
                            quality_score, relevance_score,
                            created_at, updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                        place.work_id,  # sentence_idとしてwork_idを使用
                        place_id,
                        place.extraction_method,
                        place.confidence,
                        place.context_before,
                        place.context_after,
                        place.place_name,
                        'auto',
                        0.0,  # 初期品質スコア
                        0.0,  # 初期関連性スコア
                        place.created_at,
                        place.updated_at
                    ))
                    
                    saved_places.append({
                        'place_id': place_id,
                        'place_name': place.place_name,
                        'canonical_name': place.canonical_name,
                        'place_type': place.place_type,
                        'prefecture': place.prefecture,
                        'confidence': place.confidence
                    })
                
                conn.commit()
        
        except Exception as e:
            logger.error(f"地名保存エラー: {e}")
            raise
        
        return saved_places
    
    def _update_statistics(self, work_id: int):
        """統計情報の更新"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 作品の地名統計を更新
                conn.execute("""
                    UPDATE works 
                    SET place_count = (
                        SELECT COUNT(DISTINCT pm.place_id)
                FROM places_master pm
                JOIN sentence_places sp ON pm.place_id = sp.place_id
                WHERE sp.sentence_id = ?
                    ),
                    updated_at = ?
                    WHERE work_id = ?
                """, (work_id, datetime.now().isoformat(), work_id))
                
                # 作者の地名統計を更新
                conn.execute("""
                    UPDATE authors 
                    SET place_count = (
                        SELECT COUNT(DISTINCT pm.place_id)
                        FROM places_master pm
                        JOIN sentence_places sp ON pm.place_id = sp.place_id
                        JOIN works w ON sp.sentence_id = w.work_id
                        WHERE w.author_id = authors.author_id
                    ),
                    updated_at = ?
                    WHERE author_id = (
                        SELECT author_id FROM works WHERE work_id = ?
                    )
                """, (datetime.now().isoformat(), work_id))
                
                conn.commit()
        
        except Exception as e:
            logger.error(f"統計更新エラー: {e}")
            raise
    
    def get_work_statistics(self, work_id: int) -> Dict:
        """作品の統計情報取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        w.work_title,
                        w.place_count,
                        w.sentence_count,
                        a.author_name,
                        COUNT(DISTINCT pm.place_id) as unique_places,
                        COUNT(sp.id) as total_mentions
                    FROM works w
                    JOIN authors a ON w.author_id = a.author_id
                    LEFT JOIN sentence_places sp ON sp.sentence_id = w.work_id
                    LEFT JOIN places_master pm ON sp.place_id = pm.place_id
                    WHERE w.work_id = ?
                    GROUP BY w.work_id
                """, (work_id,))
                result = cursor.fetchone()
                if result:
                    return {
                        'work_title': result[0],
                        'place_count': result[1],
                        'sentence_count': result[2],
                        'author_name': result[3],
                        'unique_places': result[4],
                        'total_mentions': result[5]
                    }
                return {}
        except Exception as e:
            logger.error(f"統計取得エラー: {e}")
            return {}
    
    def get_author_statistics(self, author_id: int) -> Dict[str, int]:
        """作者の統計情報を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(DISTINCT s.sentence_id) as total_sentences,
                        COUNT(DISTINCT pm.place_id) as total_places,
                        COUNT(DISTINCT CASE WHEN pm.latitude IS NOT NULL THEN pm.place_id END) as geocoded_places
                    FROM authors a
                    LEFT JOIN works w ON a.author_id = w.author_id
                    LEFT JOIN sentences s ON w.work_id = s.work_id
                    LEFT JOIN sentence_places sp ON s.sentence_id = sp.sentence_id
                    LEFT JOIN places_master pm ON sp.place_id = pm.place_id
                    WHERE a.author_id = ?
                """, (author_id,))
                result = cursor.fetchone()
                if result:
                    return {
                        'total_sentences': result[0] or 0,
                        'total_places': result[1] or 0,
                        'geocoded_places': result[2] or 0
                    }
                return {
                    'total_sentences': 0,
                    'total_places': 0,
                    'geocoded_places': 0
                }
        except Exception as e:
            logger.error(f"作者統計取得エラー: {e}")
            return {
                'total_sentences': 0,
                'total_places': 0,
                'geocoded_places': 0
            }
    
    def save_author(self, author) -> Optional[int]:
        """作者情報を保存し、IDを返す。既存ならそのIDを返す"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT author_id FROM authors WHERE author_name = ?",
                    (author.author_name,)
                )
                result = cursor.fetchone()
                if result:
                    return result[0]
                # 新規作成
                cursor = conn.execute(
                    """
                    INSERT INTO authors (author_name, source_system, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        author.author_name,
                        getattr(author, 'source_system', 'aozora'),
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    )
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"作者保存エラー: {e}")
            return None

    def save_work(self, work: Work) -> Optional[int]:
        """作品情報を保存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO works (
                        work_title,
                        author_id,
                        aozora_url,
                        source_system,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    work.work_title,
                    work.author_id,
                    work.aozora_url,
                    work.source_system,
                    datetime.now(),
                    datetime.now()
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"作品保存エラー: {e}")
            return None

    def save_sentence(self, sentence) -> bool:
        """センテンスを保存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO sentences (
                        sentence_text, work_id, author_id, position_in_work,
                        sentence_length, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    sentence.sentence_text,
                    sentence.work_id,
                    sentence.author_id,
                    sentence.position_in_work,
                    sentence.sentence_length,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"センテンス保存エラー: {e}")
            return False

if __name__ == "__main__":
    # 簡単なテスト
    manager = DatabaseManager()
    
    test_work = {
        'work_id': 1,
        'text': '東京の銀座で買い物をした後、新宿へ移動した。',
        'context_before': '主人公は',
        'context_after': 'という一日を過ごした。'
    }
    
    result = manager.process_work(**test_work)
    
    print("✅ データベースマネージャーv4テスト完了")
    print(f"📊 処理結果:")
    print(f"  作品ID: {result['work_id']}")
    print(f"  抽出地名数: {result['total_places']}")
    print(f"  保存地名数: {len(result['saved_places'])}")
    
    if result['saved_places']:
        print("\n🗺️ 保存された地名:")
        for place in result['saved_places']:
            print(f"  • {place['place_name']} → {place['canonical_name']}")
            print(f"    タイプ: {place['place_type']}")
            if place['prefecture']:
                print(f"    都道府県: {place['prefecture']}")
            print(f"    信頼度: {place['confidence']:.2f}") 