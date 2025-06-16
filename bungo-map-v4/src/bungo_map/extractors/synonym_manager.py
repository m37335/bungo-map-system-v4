#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名の同義語・類義語の管理機能
"""

import json
import sqlite3
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from pathlib import Path

@dataclass
class PlaceSynonym:
    """地名の同義語情報"""
    canonical_name: str
    synonyms: List[str]
    place_type: str
    prefecture: Optional[str] = None
    description: Optional[str] = None

class SynonymManager:
    """地名の同義語・類義語管理クラス"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS place_synonyms (
                    canonical_name TEXT PRIMARY KEY,
                    synonyms TEXT,
                    place_type TEXT,
                    prefecture TEXT,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_place_synonyms_synonyms 
                ON place_synonyms(canonical_name)
            """)
    
    def add_synonym(self, canonical_name: str, synonyms: List[str],
                   place_type: str, prefecture: Optional[str] = None,
                   description: Optional[str] = None):
        """
        同義語を追加
        
        Args:
            canonical_name: 正規名
            synonyms: 同義語のリスト
            place_type: 地名タイプ
            prefecture: 都道府県（オプション）
            description: 説明（オプション）
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO place_synonyms
                (canonical_name, synonyms, place_type, prefecture, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                canonical_name,
                json.dumps(synonyms, ensure_ascii=False),
                place_type,
                prefecture,
                description
            ))
    
    def get_synonyms(self, place_name: str) -> Optional[PlaceSynonym]:
        """
        同義語を取得
        
        Args:
            place_name: 地名
            
        Returns:
            同義語情報
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT canonical_name, synonyms, place_type, prefecture, description
                FROM place_synonyms
                WHERE canonical_name = ? OR synonyms LIKE ?
            """, (place_name, f'%{place_name}%'))
            row = cursor.fetchone()
            
            if row:
                return PlaceSynonym(
                    canonical_name=row[0],
                    synonyms=json.loads(row[1]),
                    place_type=row[2],
                    prefecture=row[3],
                    description=row[4]
                )
        
        return None
    
    def get_all_synonyms(self) -> List[PlaceSynonym]:
        """
        全ての同義語を取得
        
        Returns:
            同義語情報のリスト
        """
        synonyms = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT canonical_name, synonyms, place_type, prefecture, description
                FROM place_synonyms
                ORDER BY canonical_name
            """)
            
            for row in cursor.fetchall():
                synonyms.append(PlaceSynonym(
                    canonical_name=row[0],
                    synonyms=json.loads(row[1]),
                    place_type=row[2],
                    prefecture=row[3],
                    description=row[4]
                ))
        
        return synonyms
    
    def remove_synonym(self, canonical_name: str):
        """
        同義語を削除
        
        Args:
            canonical_name: 正規名
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM place_synonyms
                WHERE canonical_name = ?
            """, (canonical_name,))
    
    def import_from_json(self, json_path: str):
        """
        JSONファイルから同義語をインポート
        
        Args:
            json_path: JSONファイルのパス
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            for item in data:
                self.add_synonym(
                    canonical_name=item['canonical_name'],
                    synonyms=item['synonyms'],
                    place_type=item['place_type'],
                    prefecture=item.get('prefecture'),
                    description=item.get('description')
                )
    
    def export_to_json(self, json_path: str):
        """
        同義語をJSONファイルにエクスポート
        
        Args:
            json_path: JSONファイルのパス
        """
        synonyms = self.get_all_synonyms()
        data = [
            {
                'canonical_name': s.canonical_name,
                'synonyms': s.synonyms,
                'place_type': s.place_type,
                'prefecture': s.prefecture,
                'description': s.description
            }
            for s in synonyms
        ]
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def find_similar_places(self, place_name: str) -> List[PlaceSynonym]:
        """
        類似する地名を検索
        
        Args:
            place_name: 検索対象の地名
            
        Returns:
            類似する地名のリスト
        """
        similar_places = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT canonical_name, synonyms, place_type, prefecture, description
                FROM place_synonyms
                WHERE canonical_name LIKE ? OR synonyms LIKE ?
            """, (f'%{place_name}%', f'%{place_name}%'))
            
            for row in cursor.fetchall():
                similar_places.append(PlaceSynonym(
                    canonical_name=row[0],
                    synonyms=json.loads(row[1]),
                    place_type=row[2],
                    prefecture=row[3],
                    description=row[4]
                ))
        
        return similar_places 