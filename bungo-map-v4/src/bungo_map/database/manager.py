"""
Bungo Map System v4.0 Database Manager

センテンス中心アーキテクチャのデータベース操作管理
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any, Tuple
from .models import Sentence, PlaceMaster, SentencePlace, DatabaseConnection
from .models import row_to_sentence, row_to_place_master, row_to_sentence_place


class DatabaseManager:
    """v4.0データベース管理クラス"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    # ========== センテンス操作 ==========
    
    def insert_sentence(self, sentence: Sentence) -> int:
        """センテンスを挿入"""
        with DatabaseConnection(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO sentences (
                    sentence_text, work_id, author_id, before_text, after_text,
                    source_info, chapter, page_number, position_in_work
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sentence.sentence_text, sentence.work_id, sentence.author_id,
                sentence.before_text, sentence.after_text, sentence.source_info,
                sentence.chapter, sentence.page_number, sentence.position_in_work
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_sentence(self, sentence_id: int) -> Optional[Sentence]:
        """センテンスIDで取得"""
        with DatabaseConnection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM sentences WHERE sentence_id = ?", 
                (sentence_id,)
            )
            row = cursor.fetchone()
            return row_to_sentence(row) if row else None
    
    def get_sentences_by_work(self, work_id: int) -> List[Sentence]:
        """作品IDでセンテンス一覧取得"""
        with DatabaseConnection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM sentences WHERE work_id = ? ORDER BY position_in_work",
                (work_id,)
            )
            return [row_to_sentence(row) for row in cursor.fetchall()]
    
    def search_sentences(self, text: str, limit: int = 100) -> List[Sentence]:
        """センテンス文字列検索"""
        with DatabaseConnection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM sentences WHERE sentence_text LIKE ? LIMIT ?",
                (f"%{text}%", limit)
            )
            return [row_to_sentence(row) for row in cursor.fetchall()]
    
    # ========== 地名マスター操作 ==========
    
    def insert_place_master(self, place: PlaceMaster) -> int:
        """地名マスターを挿入"""
        with DatabaseConnection(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO places_master (
                    place_name, canonical_name, aliases, latitude, longitude,
                    place_type, confidence, description, wikipedia_url, image_url,
                    prefecture, municipality, district, source_system, verification_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                place.place_name, place.canonical_name, place.get_aliases_json(),
                place.latitude, place.longitude, place.place_type, place.confidence,
                place.description, place.wikipedia_url, place.image_url,
                place.prefecture, place.municipality, place.district,
                place.source_system, place.verification_status
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_place_master(self, place_id: int) -> Optional[PlaceMaster]:
        """地名マスターIDで取得"""
        with DatabaseConnection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM places_master WHERE place_id = ?",
                (place_id,)
            )
            row = cursor.fetchone()
            return row_to_place_master(row) if row else None
    
    def find_place_by_name(self, place_name: str) -> Optional[PlaceMaster]:
        """地名で地名マスター検索（完全一致）"""
        with DatabaseConnection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM places_master WHERE place_name = ? OR canonical_name = ?",
                (place_name, place_name)
            )
            row = cursor.fetchone()
            if row:
                return row_to_place_master(row)
            
            # 別名も検索
            cursor = conn.execute("SELECT * FROM places_master")
            for row in cursor.fetchall():
                place = row_to_place_master(row)
                if place.matches_name(place_name):
                    return place
            
            return None
    
    def search_places_master(self, text: str, place_type: Optional[str] = None) -> List[PlaceMaster]:
        """地名マスター検索"""
        with DatabaseConnection(self.db_path) as conn:
            if place_type:
                cursor = conn.execute("""
                    SELECT * FROM places_master 
                    WHERE (place_name LIKE ? OR canonical_name LIKE ?) AND place_type = ?
                    ORDER BY place_name
                """, (f"%{text}%", f"%{text}%", place_type))
            else:
                cursor = conn.execute("""
                    SELECT * FROM places_master 
                    WHERE place_name LIKE ? OR canonical_name LIKE ?
                    ORDER BY place_name
                """, (f"%{text}%", f"%{text}%"))
            
            return [row_to_place_master(row) for row in cursor.fetchall()]
    
    def get_or_create_place_master(self, place_name: str, place_info: dict) -> int:
        """地名マスター取得または作成"""
        # 既存チェック
        existing = self.find_place_by_name(place_name)
        if existing:
            # 別名として追加
            if place_name != existing.place_name:
                existing.add_alias(place_name)
                self.update_place_master(existing)
            return existing.place_id
        
        # 新規作成
        place = PlaceMaster(
            place_name=place_name,
            canonical_name=place_info.get('canonical_name', place_name),
            place_type=place_info.get('place_type', '有名地名'),
            confidence=place_info.get('confidence', 0.0),
            latitude=place_info.get('latitude'),
            longitude=place_info.get('longitude'),
            source_system='v4.0'
        )
        
        return self.insert_place_master(place)
    
    def update_place_master(self, place: PlaceMaster) -> bool:
        """地名マスター更新"""
        try:
            with DatabaseConnection(self.db_path) as conn:
                conn.execute("""
                    UPDATE places_master SET
                        place_name = ?, canonical_name = ?, aliases = ?,
                        latitude = ?, longitude = ?, place_type = ?, confidence = ?,
                        description = ?, wikipedia_url = ?, image_url = ?,
                        prefecture = ?, municipality = ?, district = ?,
                        verification_status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE place_id = ?
                """, (
                    place.place_name, place.canonical_name, place.get_aliases_json(),
                    place.latitude, place.longitude, place.place_type, place.confidence,
                    place.description, place.wikipedia_url, place.image_url,
                    place.prefecture, place.municipality, place.district,
                    place.verification_status, place.place_id
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ 地名マスター更新エラー: {e}")
            return False
    
    # ========== センテンス-地名関連操作 ==========
    
    def insert_sentence_place(self, relation: SentencePlace) -> int:
        """センテンス-地名関連を挿入"""
        with DatabaseConnection(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO sentence_places (
                    sentence_id, place_id, extraction_method, confidence,
                    position_in_sentence, context_before, context_after, matched_text,
                    verification_status, quality_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                relation.sentence_id, relation.place_id, relation.extraction_method,
                relation.confidence, relation.position_in_sentence,
                relation.context_before, relation.context_after, relation.matched_text,
                relation.verification_status, relation.quality_score
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_places_by_sentence(self, sentence_id: int) -> List[Tuple[PlaceMaster, SentencePlace]]:
        """センテンスIDから関連地名一覧取得"""
        with DatabaseConnection(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT pm.*, sp.*
                FROM places_master pm
                JOIN sentence_places sp ON pm.place_id = sp.place_id
                WHERE sp.sentence_id = ?
                ORDER BY sp.position_in_sentence
            """, (sentence_id,))
            
            results = []
            for row in cursor.fetchall():
                # Rowオブジェクトから直接変換
                place = row_to_place_master(row)
                relation = row_to_sentence_place(row)
                results.append((place, relation))
            
            return results
    
    def get_sentences_by_place(self, place_id: int) -> List[Tuple[Sentence, SentencePlace]]:
        """地名IDから関連センテンス一覧取得"""
        with DatabaseConnection(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT s.*, sp.*
                FROM sentences s
                JOIN sentence_places sp ON s.sentence_id = sp.sentence_id
                WHERE sp.place_id = ?
                ORDER BY s.work_id, s.position_in_work
            """, (place_id,))
            
            results = []
            for row in cursor.fetchall():
                # Rowオブジェクトから直接変換
                sentence = row_to_sentence(row)
                relation = row_to_sentence_place(row)
                results.append((sentence, relation))
            
            return results
    
    # ========== 統計・分析 ==========
    
    def get_statistics(self) -> dict:
        """統計情報取得"""
        with DatabaseConnection(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM statistics_summary")
            row = cursor.fetchone()
            
            if row:
                return {
                    'total_sentences': row['total_sentences'],
                    'total_places': row['total_places'],
                    'total_relations': row['total_relations'],
                    'total_works': row['total_works'],
                    'total_authors': row['total_authors'],
                    'avg_confidence': row['avg_confidence']
                }
            return {}
    
    def get_place_type_distribution(self) -> Dict[str, int]:
        """地名タイプ別分布"""
        with DatabaseConnection(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT place_type, COUNT(*) as count
                FROM places_master 
                GROUP BY place_type 
                ORDER BY count DESC
            """)
            return {row['place_type']: row['count'] for row in cursor.fetchall()}
    
    def get_extraction_method_distribution(self) -> Dict[str, int]:
        """抽出手法別分布"""
        with DatabaseConnection(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT extraction_method, COUNT(*) as count
                FROM sentence_places 
                GROUP BY extraction_method 
                ORDER BY count DESC
            """)
            return {row['extraction_method']: row['count'] for row in cursor.fetchall()} 