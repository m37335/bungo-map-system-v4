#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベースマネージャー v4
地名抽出・正規化システムと連携したデータベース管理
"""

import sqlite3
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

from .models import Author, Work, Sentence, Place, SentencePlace

logger = logging.getLogger(__name__)

class DatabaseManager:
    """現行スキーマ対応 データベースマネージャー"""
    
    def __init__(self, db_path: str = 'data/bungo_map.db'):
        """初期化"""
        self.db_path = db_path
        logger.info(f"🌟 データベースマネージャーv4初期化: DBパス = {self.db_path}")
    
    def get_connection(self):
        """データベース接続を取得"""
        return sqlite3.connect(self.db_path)
    
    def get_author_by_name(self, author_name: str) -> Optional[Author]:
        """作者名で作者情報を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM authors WHERE author_name = ?",
                    (author_name,)
                )
                result = cursor.fetchone()
                if result:
                    # Authorオブジェクトを作成
                    author = Author()
                    for key in result.keys():
                        setattr(author, key, result[key])
                    return author
                return None
        except Exception as e:
            logger.error(f"作者取得エラー: {e}")
            return None
    
    def get_all_authors(self) -> List[Author]:
        """すべての作者を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM authors ORDER BY author_name")
                results = cursor.fetchall()
                
                authors = []
                for result in results:
                    author = Author()
                    for key in result.keys():
                        setattr(author, key, result[key])
                    authors.append(author)
                
                return authors
        except Exception as e:
            logger.error(f"作者一覧取得エラー: {e}")
            return []
    
    def get_work_by_title_and_author(self, work_title: str, author_id: int) -> Optional[Work]:
        """作品タイトルと作者IDで作品を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM works WHERE title = ? AND author_id = ?",
                    (work_title, author_id)
                )
                result = cursor.fetchone()
                if result:
                    work = Work()
                    for key in result.keys():
                        setattr(work, key, result[key])
                    return work
                return None
        except Exception as e:
            logger.error(f"作品取得エラー: {e}")
            return None

    def save_author(self, author_data) -> Optional[int]:
        """作者情報を保存し、IDを返す。既存ならそのIDを返す"""
        try:
            # 辞書形式とAuthorオブジェクト両方に対応
            if isinstance(author_data, dict):
                author_name = author_data.get('author_name')
                author_name_kana = author_data.get('author_name_kana')
                birth_year = author_data.get('birth_year')
                death_year = author_data.get('death_year')
                period = author_data.get('period')
                wikipedia_url = author_data.get('wikipedia_url')
                description = author_data.get('description')
                source_system = author_data.get('source_system', 'manual')
            else:
                author_name = author_data.author_name
                author_name_kana = author_data.author_name_kana
                birth_year = author_data.birth_year
                death_year = author_data.death_year
                period = author_data.period
                wikipedia_url = author_data.wikipedia_url
                description = author_data.description
                source_system = getattr(author_data, 'source_system', 'manual')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT author_id FROM authors WHERE author_name = ?",
                    (author_name,)
                )
                result = cursor.fetchone()
                if result:
                    return result[0]
                
                # 新規作成
                cursor = conn.execute(
                    """
                    INSERT INTO authors (
                        author_name, author_name_kana, birth_year, death_year,
                        period, wikipedia_url, description, source_system,
                        created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        author_name,
                        author_name_kana,
                        birth_year,
                        death_year,
                        period,
                        wikipedia_url,
                        description,
                        source_system,
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    )
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"作者保存エラー: {e}")
            return None

    def create_author(self, author_data) -> Optional[int]:
        """新規作者作成（save_authorのエイリアス）"""
        return self.save_author(author_data)

    def create_or_get_author(self, author_data) -> Optional[int]:
        """作者を作成または取得（統一インターフェース）"""
        return self.save_author(author_data)

    def update_author(self, author_id: int, author_data: dict) -> bool:
        """作者情報更新"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 更新フィールドを動的に構築
                update_fields = []
                values = []
                
                for key, value in author_data.items():
                    if key != 'author_id':  # IDは更新しない
                        update_fields.append(f"{key} = ?")
                        values.append(value)
                
                if not update_fields:
                    return False
                
                values.append(author_id)
                values.append(datetime.now().isoformat())
                
                query = f"""UPDATE authors SET 
                    {', '.join(update_fields)}, updated_at = ?
                    WHERE author_id = ?"""
                
                cursor = conn.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"作者更新エラー: {e}")
            return False

    def save_work(self, work_data) -> Optional[int]:
        """作品情報を保存（辞書形式とWorkオブジェクト両方に対応）"""
        try:
            # 辞書形式とWorkオブジェクト両方に対応
            if isinstance(work_data, dict):
                work_title = work_data.get('work_title') or work_data.get('title')
                author_id = work_data.get('author_id')
                publication_year = work_data.get('publication_year')
                genre = work_data.get('genre')
                aozora_url = work_data.get('aozora_url') or work_data.get('aozora_work_url') or work_data.get('work_url')
                content_length = work_data.get('content_length', 0)
                sentence_count = work_data.get('sentence_count', 0)
                source_system = work_data.get('source_system', 'aozora_scraper')
                processing_status = work_data.get('processing_status', 'pending')
            else:
                work_title = work_data.work_title
                author_id = work_data.author_id
                publication_year = work_data.publication_year
                genre = work_data.genre
                aozora_url = work_data.aozora_url
                content_length = work_data.content_length
                sentence_count = work_data.sentence_count
                source_system = getattr(work_data, 'source_system', 'aozora_scraper')
                processing_status = getattr(work_data, 'processing_status', 'pending')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO works (
                        title, author_id, aozora_work_url, 
                        content_length, sentence_count, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        work_title,
                        author_id,
                        aozora_url,
                        content_length,
                        sentence_count,
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    )
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"作品保存エラー: {e}")
            return None

    def get_works_by_author(self, author_id: int) -> List[Work]:
        """作者の作品一覧を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM works WHERE author_id = ? ORDER BY title",
                    (author_id,)
                )
                results = cursor.fetchall()
                
                works = []
                for result in results:
                    work = Work()
                    for key in result.keys():
                        setattr(work, key, result[key])
                    works.append(work)
                
                return works
        except Exception as e:
            logger.error(f"作者の作品取得エラー: {e}")
            return []

    def get_authors_with_aozora_url(self) -> List[Author]:
        """aozora_author_urlが設定されている作者一覧を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM authors WHERE aozora_author_url IS NOT NULL AND aozora_author_url != '' ORDER BY author_name"
                )
                results = cursor.fetchall()
                
                authors = []
                for result in results:
                    author = Author()
                    for key in result.keys():
                        setattr(author, key, result[key])
                    authors.append(author)
                
                return authors
        except Exception as e:
            logger.error(f"青空文庫URL付き作者一覧取得エラー: {e}")
            return []

    def save_sentence(self, sentence_data) -> Optional[int]:
        """センテンス情報を保存（v2スキーマ対応）"""
        try:
            # 辞書形式とSentenceオブジェクト両方に対応
            if isinstance(sentence_data, dict):
                sentence_text = sentence_data.get('sentence_text')
                work_id = sentence_data.get('work_id')
                sentence_order = sentence_data.get('sentence_order', 1)
                paragraph_number = sentence_data.get('paragraph_number', 1)
                character_count = sentence_data.get('character_count', len(sentence_text or ''))
            else:
                sentence_text = sentence_data.sentence_text
                work_id = sentence_data.work_id
                sentence_order = getattr(sentence_data, 'sentence_order', 1)
                paragraph_number = getattr(sentence_data, 'paragraph_number', 1)
                character_count = len(sentence_text or '')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO sentences (
                        work_id, sentence_order, sentence_text, char_count
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        work_id,
                        sentence_order,
                        sentence_text,
                        character_count
                    )
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"センテンス保存エラー: {e}")
            return None

    def save_place(self, place: Place) -> Optional[int]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT place_id FROM places WHERE place_name = ?",
                    (place.place_name,)
                )
                result = cursor.fetchone()
                if result:
                    return result[0]
                cursor = conn.execute(
                    """
                    INSERT INTO places (
                        place_name, canonical_name, aliases, latitude, longitude, place_type, confidence, description, wikipedia_url, image_url, country, prefecture, municipality, district, mention_count, author_count, work_count, source_system, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        place.place_name,
                        place.canonical_name,
                        str(getattr(place, 'aliases', '[]')),
                        place.latitude,
                        place.longitude,
                        place.place_type,
                        place.confidence,
                        place.description,
                        place.wikipedia_url,
                        place.image_url,
                        place.country,
                        place.prefecture,
                        place.municipality,
                        place.district,
                        place.mention_count,
                        place.author_count,
                        place.work_count,
                        getattr(place, 'source_system', 'manual'),
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    )
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"地名保存エラー: {e}")
            return None

    def save_sentence_place(self, sp: SentencePlace) -> Optional[int]:
        """センテンス-地名関係を保存（v2スキーマ対応）"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO sentence_places (
                        sentence_id, master_id, matched_text, start_position, end_position,
                        extraction_confidence, extraction_method, ai_verified, ai_confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sp.sentence_id,
                        getattr(sp, 'master_id', None) or sp.place_id,  # 互換性
                        sp.matched_text,
                        getattr(sp, 'start_position', sp.position_in_sentence),
                        getattr(sp, 'end_position', None),
                        sp.confidence,
                        sp.extraction_method,
                        getattr(sp, 'ai_verified', False),
                        getattr(sp, 'ai_confidence', None)
                    )
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"sentence_place保存エラー: {e}")
            return None

    def get_work_statistics(self, work_id: int) -> Dict[str, Any]:
        """作品の統計情報取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT w.title, w.place_count, w.sentence_count, a.author_name
                    FROM works w
                    JOIN authors a ON w.author_id = a.author_id
                    WHERE w.work_id = ?
                    """,
                    (work_id,)
                )
                result = cursor.fetchone()
                if result:
                    return {
                        'work_title': result[0],
                        'place_count': result[1],
                        'sentence_count': result[2],
                        'author_name': result[3]
                    }
                return {}
        except Exception as e:
            logger.error(f"統計取得エラー: {e}")
            return {}

if __name__ == "__main__":
    # 簡単なテスト
    manager = DatabaseManager()
    
    # テスト用の作者データ
    author = Author(
        author_name="夏目漱石",
        author_name_kana="なつめそうせき",
        birth_year=1867,
        death_year=1916,
        period="明治・大正",
        wikipedia_url="https://ja.wikipedia.org/wiki/夏目漱石",
        description="明治時代を代表する文豪。本名は夏目金之助。"
    )
    
    # 作者を保存
    author_id = manager.save_author(author)
    print(f"✅ 作者保存完了: ID = {author_id}")
    
    if author_id:
        # テスト用の作品データ
        work = {
            'title': "吾輩は猫である",
            'author_id': author_id,
            'publication_year': 1905,
            'genre': "小説",
            'aozora_url': "https://www.aozora.gr.jp/cards/000148/files/789_14547.html",
            'content_length': 0,
            'sentence_count': 0
        }
        
        # 作品を保存
        work_id = manager.save_work(work)
        print(f"✅ 作品保存完了: ID = {work_id}")
        
        if work_id:
            # 統計情報を取得
            stats = manager.get_work_statistics(work_id)
            print("\n📊 作品統計:")
            print(f"  タイトル: {stats.get('work_title')}")
            print(f"  作者: {stats.get('author_name')}")
            print(f"  地名数: {stats.get('place_count', 0)}")
            print(f"  センテンス数: {stats.get('sentence_count', 0)}") 