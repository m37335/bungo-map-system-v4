"""
Bungo Map System v4.0 データベースモジュール
"""

from typing import List, Dict, Any, Optional
import sqlite3
from pathlib import Path


class Database:
    """データベース管理クラス"""
    
    def __init__(self, db_path: str = None):
        """初期化"""
        if db_path is None:
            db_path = str(Path(__file__).parent.parent.parent / 'data' / 'databases' / 'bungo_v4.db')
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """データベース初期化"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS works (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT,
                    content TEXT,
                    url TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS places (
                    id INTEGER PRIMARY KEY,
                    work_id INTEGER,
                    place_name TEXT NOT NULL,
                    sentence TEXT,
                    position_start INTEGER,
                    position_end INTEGER,
                    location_lat REAL,
                    location_lng REAL,
                    confidence REAL,
                    FOREIGN KEY (work_id) REFERENCES works (id)
                )
            ''')
            conn.commit()
    
    def get_work(self, work_id: int) -> Optional[Dict[str, Any]]:
        """作品データ取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM works WHERE id = ?', (work_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'title': row[1],
                    'author': row[2],
                    'content': row[3],
                    'url': row[4]
                }
            return None
    
    def get_unprocessed_works(self) -> List[Dict[str, Any]]:
        """未処理作品の取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT w.* FROM works w
                LEFT JOIN places p ON w.id = p.work_id
                WHERE p.id IS NULL
            ''')
            return [
                {
                    'id': row[0],
                    'title': row[1],
                    'author': row[2],
                    'content': row[3],
                    'url': row[4]
                }
                for row in cursor.fetchall()
            ]
    
    def save_extracted_place(self, place: Dict[str, Any]) -> None:
        """抽出地名の保存"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO places (
                    work_id, place_name, sentence,
                    position_start, position_end
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                place.get('work_id'),
                place['place_name'],
                place.get('sentence'),
                place.get('position', {}).get('start'),
                place.get('position', {}).get('end')
            ))
            conn.commit()
    
    def save_geocoded_place(self, place: Dict[str, Any]) -> None:
        """ジオコーディング結果の保存"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE places
                SET location_lat = ?,
                    location_lng = ?,
                    confidence = ?
                WHERE work_id = ? AND place_name = ?
            ''', (
                place['location']['lat'],
                place['location']['lng'],
                place['confidence'],
                place['work_id'],
                place['place_name']
            ))
            conn.commit()
    
    def reset_places_table(self) -> None:
        """placesテーブルのリセット"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM places')
            conn.commit() 