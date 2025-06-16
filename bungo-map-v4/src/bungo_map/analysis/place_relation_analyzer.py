#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名の関連性分析機能
"""

import sqlite3
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import networkx as nx
import numpy as np
from datetime import datetime

@dataclass
class PlaceRelation:
    """地名間の関係性情報"""
    source_place: str
    target_place: str
    relation_type: str
    strength: float
    context: str
    work_id: int
    author_id: int
    created_at: datetime

@dataclass
class RelationStats:
    """関係性の統計情報"""
    total_relations: int
    unique_places: int
    relation_types: Dict[str, int]
    top_related_places: List[Tuple[str, float]]
    average_strength: float

class PlaceRelationAnalyzer:
    """地名の関連性分析クラス"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
        self.graph = nx.Graph()
    
    def _init_database(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS place_relations (
                    relation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_place_id INTEGER,
                    target_place_id INTEGER,
                    relation_type TEXT,
                    strength REAL,
                    context TEXT,
                    work_id INTEGER,
                    author_id INTEGER,
                    created_at TIMESTAMP,
                    FOREIGN KEY (source_place_id) REFERENCES places_master(place_id),
                    FOREIGN KEY (target_place_id) REFERENCES places_master(place_id),
                    FOREIGN KEY (work_id) REFERENCES works(work_id),
                    FOREIGN KEY (author_id) REFERENCES authors(author_id)
                )
            """)
    
    def analyze_sentence(self, sentence_id: int) -> List[PlaceRelation]:
        """
        文から地名の関係性を分析
        
        Args:
            sentence_id: 分析対象の文ID
            
        Returns:
            検出された関係性のリスト
        """
        with sqlite3.connect(self.db_path) as conn:
            # 文と関連する地名を取得
            cursor = conn.execute("""
                SELECT 
                    s.sentence_text,
                    s.work_id,
                    s.author_id,
                    GROUP_CONCAT(pm.place_id) as place_ids,
                    GROUP_CONCAT(pm.place_name) as place_names
                FROM sentences s
                JOIN sentence_places sp ON s.sentence_id = sp.sentence_id
                JOIN places_master pm ON sp.place_id = pm.place_id
                WHERE s.sentence_id = ?
                GROUP BY s.sentence_id
            """, (sentence_id,))
            
            row = cursor.fetchone()
            if not row:
                return []
            
            sentence_text, work_id, author_id, place_ids, place_names = row
            place_ids = [int(pid) for pid in place_ids.split(',')]
            place_names = place_names.split(',')
            
            # 地名間の関係性を分析
            relations = []
            for i, source_id in enumerate(place_ids):
                for j, target_id in enumerate(place_ids[i+1:], i+1):
                    relation = self._analyze_relation(
                        sentence_text,
                        source_id,
                        target_id,
                        place_names[i],
                        place_names[j],
                        work_id,
                        author_id
                    )
                    if relation:
                        relations.append(relation)
            
            return relations
    
    def _analyze_relation(self, text: str, source_id: int, target_id: int,
                         source_name: str, target_name: str,
                         work_id: int, author_id: int) -> Optional[PlaceRelation]:
        """
        2つの地名間の関係性を分析
        
        Args:
            text: 文テキスト
            source_id: 元の地名ID
            target_id: 対象の地名ID
            source_name: 元の地名
            target_name: 対象の地名
            work_id: 作品ID
            author_id: 作者ID
            
        Returns:
            関係性情報
        """
        # 関係性タイプの判定
        relation_type = self._determine_relation_type(text, source_name, target_name)
        if not relation_type:
            return None
        
        # 関係性の強さを計算
        strength = self._calculate_relation_strength(text, source_name, target_name)
        
        # 文脈を抽出
        context = self._extract_relation_context(text, source_name, target_name)
        
        return PlaceRelation(
            source_place=source_name,
            target_place=target_name,
            relation_type=relation_type,
            strength=strength,
            context=context,
            work_id=work_id,
            author_id=author_id,
            created_at=datetime.now()
        )
    
    def _determine_relation_type(self, text: str, source: str, target: str) -> Optional[str]:
        """関係性タイプの判定"""
        # 距離関係
        distance_patterns = [
            (r'から.*?まで', 'distance'),
            (r'までの.*?距離', 'distance'),
            (r'間の.*?距離', 'distance')
        ]
        
        # 方向関係
        direction_patterns = [
            (r'の.*?北', 'direction'),
            (r'の.*?南', 'direction'),
            (r'の.*?東', 'direction'),
            (r'の.*?西', 'direction')
        ]
        
        # 包含関係
        containment_patterns = [
            (r'の中の', 'containment'),
            (r'に含まれる', 'containment'),
            (r'の一部', 'containment')
        ]
        
        # パターンマッチング
        for pattern, rel_type in (distance_patterns + direction_patterns + containment_patterns):
            if re.search(pattern, text):
                return rel_type
        
        return None
    
    def _calculate_relation_strength(self, text: str, source: str, target: str) -> float:
        """関係性の強さを計算"""
        # 基本的な強さ
        strength = 0.5
        
        # 距離に基づく調整
        source_pos = text.find(source)
        target_pos = text.find(target)
        if source_pos != -1 and target_pos != -1:
            distance = abs(source_pos - target_pos)
            strength *= 1.0 / (1.0 + distance / 100.0)
        
        # 文脈に基づく調整
        context_words = ['近い', '隣接', '隣り合う', '接する']
        for word in context_words:
            if word in text:
                strength *= 1.2
        
        return min(1.0, strength)
    
    def _extract_relation_context(self, text: str, source: str, target: str) -> str:
        """関係性の文脈を抽出"""
        source_pos = text.find(source)
        target_pos = text.find(target)
        
        if source_pos == -1 or target_pos == -1:
            return ""
        
        start = min(source_pos, target_pos)
        end = max(source_pos + len(source), target_pos + len(target))
        
        # 文脈の範囲を拡張
        context_start = max(0, start - 50)
        context_end = min(len(text), end + 50)
        
        return text[context_start:context_end]
    
    def save_relation(self, relation: PlaceRelation):
        """
        関係性を保存
        
        Args:
            relation: 保存する関係性情報
        """
        with sqlite3.connect(self.db_path) as conn:
            # 地名IDを取得
            cursor = conn.execute("""
                SELECT place_id FROM places_master
                WHERE place_name IN (?, ?)
            """, (relation.source_place, relation.target_place))
            
            place_ids = [row[0] for row in cursor.fetchall()]
            if len(place_ids) != 2:
                return
            
            # 関係性を保存
            conn.execute("""
                INSERT INTO place_relations
                (source_place_id, target_place_id, relation_type,
                 strength, context, work_id, author_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                place_ids[0],
                place_ids[1],
                relation.relation_type,
                relation.strength,
                relation.context,
                relation.work_id,
                relation.author_id,
                relation.created_at
            ))
    
    def get_relation_stats(self) -> RelationStats:
        """
        関係性の統計情報を取得
        
        Returns:
            統計情報
        """
        with sqlite3.connect(self.db_path) as conn:
            # 基本統計
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_relations,
                    COUNT(DISTINCT source_place_id) + COUNT(DISTINCT target_place_id) as unique_places,
                    AVG(strength) as avg_strength
                FROM place_relations
            """)
            
            total_relations, unique_places, avg_strength = cursor.fetchone()
            
            # 関係タイプ別の集計
            cursor = conn.execute("""
                SELECT relation_type, COUNT(*) as count
                FROM place_relations
                GROUP BY relation_type
            """)
            
            relation_types = dict(cursor.fetchall())
            
            # 上位の関連地名
            cursor = conn.execute("""
                SELECT 
                    pm.place_name,
                    AVG(pr.strength) as avg_strength
                FROM place_relations pr
                JOIN places_master pm ON pr.target_place_id = pm.place_id
                GROUP BY pm.place_id
                ORDER BY avg_strength DESC
                LIMIT 10
            """)
            
            top_related = cursor.fetchall()
        
        return RelationStats(
            total_relations=total_relations,
            unique_places=unique_places,
            relation_types=relation_types,
            top_related_places=top_related,
            average_strength=avg_strength
        )
    
    def generate_relation_report(self, relation: PlaceRelation) -> str:
        """
        関係性レポートを生成
        
        Args:
            relation: 関係性情報
            
        Returns:
            レポート文字列
        """
        report = []
        report.append(f"関係性: {relation.source_place} → {relation.target_place}")
        report.append(f"タイプ: {relation.relation_type}")
        report.append(f"強さ: {relation.strength:.2f}")
        report.append(f"\n文脈:")
        report.append(relation.context)
        
        return "\n".join(report) 