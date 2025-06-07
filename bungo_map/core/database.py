#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベース管理クラス
SQLiteをメインとした3階層データ管理
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from bungo_map.core.models import Author, Work, Place


class Database:
    """文豪データベース管理クラス"""
    
    def __init__(self, db_path: str = "data/bungo_production.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_tables()
    
    def _init_tables(self):
        """テーブル初期化"""
        with self.get_connection() as conn:
            # authors テーブル
            conn.execute("""
            CREATE TABLE IF NOT EXISTS authors (
                author_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                wikipedia_url TEXT,
                birth_year INTEGER,
                death_year INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # works テーブル
            conn.execute("""
            CREATE TABLE IF NOT EXISTS works (
                work_id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                wiki_url TEXT,
                aozora_url TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES authors (author_id),
                UNIQUE(author_id, title)
            )
            """)
            
            # places テーブル
            conn.execute("""
            CREATE TABLE IF NOT EXISTS places (
                place_id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_id INTEGER NOT NULL,
                place_name TEXT NOT NULL,
                lat REAL,
                lng REAL,
                before_text TEXT,
                sentence TEXT,
                after_text TEXT,
                aozora_url TEXT,
                confidence REAL DEFAULT 0.0,
                extraction_method TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (work_id) REFERENCES works (work_id)
            )
            """)
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """データベース接続コンテキストマネージャー"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def insert_author(self, author: Author) -> int:
        """作者挿入"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT OR IGNORE INTO authors (name, wikipedia_url, birth_year, death_year)
                   VALUES (?, ?, ?, ?)""",
                (author.name, author.wikipedia_url, author.birth_year, author.death_year)
            )
            conn.commit()
            
            if cursor.lastrowid:
                return cursor.lastrowid
            
            # 既存作者のIDを取得
            cursor = conn.execute("SELECT author_id FROM authors WHERE name = ?", (author.name,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def insert_work(self, work: Work) -> int:
        """作品挿入"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT OR IGNORE INTO works (author_id, title, wiki_url, aozora_url, content)
                   VALUES (?, ?, ?, ?, ?)""",
                (work.author_id, work.title, work.wiki_url, work.aozora_url, work.content)
            )
            conn.commit()
            
            if cursor.lastrowid:
                return cursor.lastrowid
            
            # 既存作品のIDを取得
            cursor = conn.execute(
                "SELECT work_id FROM works WHERE author_id = ? AND title = ?", 
                (work.author_id, work.title)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    
    def insert_place(self, place: Place) -> int:
        """地名挿入"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT OR REPLACE INTO places 
                   (work_id, place_name, lat, lng, before_text, sentence, after_text, 
                    aozora_url, confidence, extraction_method)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (place.work_id, place.place_name, place.lat, place.lng, 
                 place.before_text, place.sentence, place.after_text,
                 place.aozora_url, place.confidence, place.extraction_method)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_author_by_name(self, name: str) -> Optional[Author]:
        """作者名で検索"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM authors WHERE name LIKE ?", (f"%{name}%",))
            row = cursor.fetchone()
            if row:
                return Author(**dict(row))
            return None
    
    def get_stats(self) -> Dict[str, int]:
        """データベース統計情報"""
        with self.get_connection() as conn:
            stats = {}
            for table in ['authors', 'works', 'places']:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            return stats
    
    def get_place_count(self) -> int:
        """地名の総数を取得"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM places")
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def get_places_with_coordinates_count(self) -> int:
        """座標が設定済みの地名数を取得"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM places WHERE lat IS NOT NULL AND lng IS NOT NULL")
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def get_places_without_coordinates(self, limit: int = None) -> List[Place]:
        """座標が未設定の地名を取得"""
        query = """
        SELECT place_id, work_id, place_name, lat, lng, 
               before_text, sentence, after_text, confidence
        FROM places 
        WHERE lat IS NULL OR lng IS NULL
        ORDER BY place_id
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query)
            places = []
            
            for row in cursor.fetchall():
                place = Place(
                    place_id=row[0],
                    work_id=row[1],
                    place_name=row[2],
                    lat=row[3],
                    lng=row[4],
                    before_text=row[5],
                    sentence=row[6],
                    after_text=row[7],
                    confidence=row[8]
                )
                places.append(place)
        
        return places
    
    def update_place(self, place: Place) -> bool:
        """地名情報を更新"""
        try:
            with self.get_connection() as conn:
                query = """
                UPDATE places 
                SET place_name = ?, lat = ?, lng = ?, 
                    before_text = ?, sentence = ?, after_text = ?, confidence = ?
                WHERE place_id = ?
                """
                
                conn.execute(query, (
                    place.place_name,
                    place.lat,
                    place.lng,
                    place.before_text,
                    place.sentence,
                    place.after_text,
                    place.confidence,
                    place.place_id
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"地名更新エラー: {e}")
            return False
    
    # ===========================================
    # 検索メソッド（双方向検索機能）
    # ===========================================
    
    def search_authors(self, query: str, limit: int = 50) -> List[Dict]:
        """作者検索（部分一致）"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT author_id, name, wikipedia_url, birth_year, death_year
                   FROM authors 
                   WHERE name LIKE ? 
                   ORDER BY name
                   LIMIT ?""",
                (f"%{query}%", limit)
            )
            
            columns = ['author_id', 'name', 'wikipedia_url', 'birth_year', 'death_year']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def search_works(self, query: str, limit: int = 50) -> List[Dict]:
        """作品検索（部分一致）- 作者名も含む"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT w.work_id, w.author_id, w.title, w.wiki_url, w.aozora_url,
                          a.name as author_name
                   FROM works w
                   JOIN authors a ON w.author_id = a.author_id
                   WHERE w.title LIKE ? OR a.name LIKE ?
                   ORDER BY a.name, w.title
                   LIMIT ?""",
                (f"%{query}%", f"%{query}%", limit)
            )
            
            columns = ['work_id', 'author_id', 'title', 'wiki_url', 'aozora_url', 'author_name']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def search_places(self, query: str, limit: int = 100) -> List[Dict]:
        """地名検索（部分一致）- 作者名・作品名も含む"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT p.place_id, p.work_id, p.place_name, p.lat, p.lng,
                          p.before_text, p.sentence, p.after_text, p.confidence,
                          w.title as work_title, a.name as author_name
                   FROM places p
                   JOIN works w ON p.work_id = w.work_id
                   JOIN authors a ON w.author_id = a.author_id
                   WHERE p.place_name LIKE ? OR a.name LIKE ? OR w.title LIKE ?
                   ORDER BY a.name, w.title, p.place_name
                   LIMIT ?""",
                (f"%{query}%", f"%{query}%", f"%{query}%", limit)
            )
            
            columns = ['place_id', 'work_id', 'place_name', 'latitude', 'longitude',
                      'before_text', 'sentence', 'after_text', 'confidence',
                      'work_title', 'author_name']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_works_by_author(self, author_id: int) -> List[Dict]:
        """特定作者の全作品取得"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT w.work_id, w.author_id, w.title, w.wiki_url, w.aozora_url,
                          a.name as author_name
                   FROM works w
                   JOIN authors a ON w.author_id = a.author_id
                   WHERE w.author_id = ?
                   ORDER BY w.title""",
                (author_id,)
            )
            
            columns = ['work_id', 'author_id', 'title', 'wiki_url', 'aozora_url', 'author_name']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_places_by_work(self, work_id: int) -> List[Dict]:
        """特定作品の全地名取得"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT p.place_id, p.work_id, p.place_name, p.lat, p.lng,
                          p.before_text, p.sentence, p.after_text, p.confidence,
                          w.title as work_title, a.name as author_name
                   FROM places p
                   JOIN works w ON p.work_id = w.work_id
                   JOIN authors a ON w.author_id = a.author_id
                   WHERE p.work_id = ?
                   ORDER BY p.place_name""",
                (work_id,)
            )
            
            columns = ['place_id', 'work_id', 'place_name', 'latitude', 'longitude',
                      'before_text', 'sentence', 'after_text', 'confidence',
                      'work_title', 'author_name']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """詳細な統計情報取得"""
        with self.get_connection() as conn:
            stats = {}
            
            # 基本カウント
            for table in ['authors', 'works', 'places']:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f'{table}_count'] = cursor.fetchone()[0]
            
            # ジオコーディング統計
            cursor = conn.execute("SELECT COUNT(*) FROM places WHERE lat IS NOT NULL AND lng IS NOT NULL")
            geocoded_count = cursor.fetchone()[0]
            stats['geocoded_count'] = geocoded_count
            
            total_places = stats['places_count']
            stats['geocoded_rate'] = (geocoded_count / total_places * 100) if total_places > 0 else 0
            
            return stats


class BungoDB(Database):
    """文豪データベース（拡張版）"""
    
    def __init__(self, db_path: str = "data/bungo_production.db"):
        super().__init__(db_path)
    
    def upsert_author(self, name: str, wikipedia_url: str = None) -> int:
        """作者の挿入または更新"""
        author = Author(name=name, wikipedia_url=wikipedia_url)
        return self.insert_author(author)
    
    def upsert_work(self, author_id: int, title: str, wiki_url: str = None, aozora_url: str = None) -> int:
        """作品の挿入または更新"""
        work = Work(author_id=author_id, title=title, wiki_url=wiki_url, aozora_url=aozora_url)
        return self.insert_work(work)
    
    def upsert_place(self, work_id: int, place_name: str, before_text: str = None, 
                     sentence: str = None, after_text: str = None, aozora_url: str = None,
                     extraction_method: str = None, confidence: float = 0.0) -> int:
        """地名の挿入または更新"""
        place = Place(
            work_id=work_id,
            place_name=place_name,
            before_text=before_text,
            sentence=sentence,
            after_text=after_text,
            aozora_url=aozora_url,
            extraction_method=extraction_method,
            confidence=confidence
        )
        return self.insert_place(place)
    
    def get_authors_count(self) -> int:
        """作者の総数"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM authors")
            return cursor.fetchone()[0]
    
    def get_works_count(self) -> int:
        """作品の総数"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM works")
            return cursor.fetchone()[0]
    
    def get_works_count_by_author(self, author_id: int) -> int:
        """指定作者の作品数"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM works WHERE author_id = ?", (author_id,))
            return cursor.fetchone()[0]
    
    def get_places_count(self) -> int:
        """地名の総数"""
        return self.get_place_count()
    
    def get_recent_places(self, limit: int = 10) -> List[Dict]:
        """最新の地名を取得"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
            SELECT p.place_name, p.extraction_method, p.confidence, p.sentence,
                   w.title as work_title, a.name as author_name
            FROM places p
            JOIN works w ON p.work_id = w.work_id
            JOIN authors a ON w.author_id = a.author_id
            ORDER BY p.place_id DESC
            LIMIT ?
            """, (limit,))
            
            places = []
            for row in cursor.fetchall():
                places.append({
                    'place_name': row[0],
                    'extraction_method': row[1],
                    'confidence': row[2],
                    'sentence': row[3],
                    'work_title': row[4],
                    'author_name': row[5]
                })
            return places


class BungoDatabase(BungoDB):
    """互換性のためのエイリアス"""
    pass


def init_db(db_path: str = "data/bungo_production.db") -> Database:
    """データベース初期化ヘルパー関数"""
    return Database(db_path) 