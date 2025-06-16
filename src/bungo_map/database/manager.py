"""
データベースマネージャー

データベース操作を管理するクラス
"""

import sqlite3
import logging
from typing import Optional, List
from datetime import datetime
from .models import Author, Work, Sentence
from .connection import DatabaseConnection
from ..extractors_v4.unified_place_extractor import UnifiedPlaceExtractor
from ..extractors_v4.place_normalizer import PlaceNormalizer

logger = logging.getLogger(__name__)

class DatabaseManager:
    """データベースマネージャー v4"""
    
    def __init__(self, db_path: str = '/app/bungo-map-v4/data/databases/bungo_v4.db'):
        """初期化"""
        self.db_path = db_path
        self.unified_extractor = UnifiedPlaceExtractor()
        self.normalizer = PlaceNormalizer()
        logger.info("🌟 データベースマネージャーv4初期化完了")
    
    def save_author(self, author: Author) -> Optional[int]:
        """作者情報を保存"""
        try:
            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO authors (
                        author_name,
                        source_system,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?)
                """, (
                    author.author_name,
                    author.source_system,
                    datetime.now(),
                    datetime.now()
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"作者保存エラー: {e}")
            return None
    
    def save_work(self, work: Work) -> Optional[int]:
        """作品情報を保存"""
        try:
            with DatabaseConnection(self.db_path) as conn:
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
    
    def save_sentence(self, sentence: Sentence) -> bool:
        """センテンスを保存"""
        try:
            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO sentences (
                        sentence_text,
                        work_id,
                        author_id,
                        position_in_work,
                        sentence_length,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    sentence.sentence_text,
                    sentence.work_id,
                    sentence.author_id,
                    sentence.position_in_work,
                    sentence.sentence_length,
                    datetime.now(),
                    datetime.now()
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"センテンス保存エラー: {e}")
            return False
    
    def get_author(self, author_id: int) -> Optional[Author]:
        """作者情報を取得"""
        try:
            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM authors WHERE author_id = ?
                """, (author_id,))
                row = cursor.fetchone()
                if row:
                    return Author(
                        author_id=row['author_id'],
                        author_name=row['author_name'],
                        source_system=row['source_system'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    )
                return None
        except Exception as e:
            logger.error(f"作者取得エラー: {e}")
            return None
    
    def get_work(self, work_id: int) -> Optional[Work]:
        """作品情報を取得"""
        try:
            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM works WHERE work_id = ?
                """, (work_id,))
                row = cursor.fetchone()
                if row:
                    return Work(
                        work_id=row['work_id'],
                        work_title=row['work_title'],
                        author_id=row['author_id'],
                        aozora_url=row['aozora_url'],
                        source_system=row['source_system'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    )
                return None
        except Exception as e:
            logger.error(f"作品取得エラー: {e}")
            return None
    
    def get_sentences_by_work(self, work_id: int) -> List[Sentence]:
        """作品のセンテンス一覧を取得"""
        try:
            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM sentences 
                    WHERE work_id = ? 
                    ORDER BY position_in_work
                """, (work_id,))
                return [
                    Sentence(
                        sentence_id=row['sentence_id'],
                        sentence_text=row['sentence_text'],
                        work_id=row['work_id'],
                        author_id=row['author_id'],
                        position_in_work=row['position_in_work'],
                        sentence_length=row['sentence_length'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    )
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"センテンス取得エラー: {e}")
            return []

    def get_author_stats(self, author_name: str) -> dict:
        """作者の統計情報を取得"""
        try:
            with DatabaseConnection(self.db_path) as conn:
                # 作者IDを取得
                cursor = conn.execute("""
                    SELECT author_id FROM authors 
                    WHERE author_name = ?
                """, (author_name,))
                author_row = cursor.fetchone()
                if not author_row:
                    return {
                        'total_sentences': 0,
                        'extracted_places': 0,
                        'geocoded_places': 0
                    }
                
                author_id = author_row['author_id']
                
                # センテンス数を取得
                cursor = conn.execute("""
                    SELECT COUNT(*) as count FROM sentences 
                    WHERE author_id = ?
                """, (author_id,))
                sentences_row = cursor.fetchone()
                total_sentences = sentences_row['count'] if sentences_row else 0
                
                # 抽出地名数を取得
                cursor = conn.execute("""
                    SELECT COUNT(*) as count FROM extracted_places 
                    WHERE author_id = ?
                """, (author_id,))
                places_row = cursor.fetchone()
                extracted_places = places_row['count'] if places_row else 0
                
                # ジオコーディング済み地名数を取得
                cursor = conn.execute("""
                    SELECT COUNT(*) as count FROM geocoded_places 
                    WHERE author_id = ?
                """, (author_id,))
                geocoded_row = cursor.fetchone()
                geocoded_places = geocoded_row['count'] if geocoded_row else 0
                
                return {
                    'total_sentences': total_sentences,
                    'extracted_places': extracted_places,
                    'geocoded_places': geocoded_places
                }
        except Exception as e:
            logger.error(f"作者統計情報取得エラー: {e}")
            return {
                'total_sentences': 0,
                'extracted_places': 0,
                'geocoded_places': 0
            } 