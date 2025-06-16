#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名の重要度スコアリング機能
"""

import sqlite3
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np
from sklearn.preprocessing import MinMaxScaler

@dataclass
class PlaceImportance:
    """地名の重要度情報"""
    place_name: str
    canonical_name: str
    total_score: float
    mention_score: float
    context_score: float
    temporal_score: float
    author_score: float
    work_score: float
    rank: int

class ImportanceScorer:
    """地名の重要度スコアリングクラス"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.scaler = MinMaxScaler()
    
    def calculate_importance(self, place_name: str) -> Optional[PlaceImportance]:
        """
        地名の重要度を計算
        
        Args:
            place_name: 対象の地名
            
        Returns:
            重要度情報
        """
        with sqlite3.connect(self.db_path) as conn:
            # 基本統計の取得
            cursor = conn.execute("""
                SELECT 
                    pm.place_name,
                    pm.canonical_name,
                    COUNT(sp.id) as mention_count,
                    COUNT(DISTINCT s.work_id) as work_count,
                    COUNT(DISTINCT s.author_id) as author_count,
                    AVG(s.position_in_work) as avg_position,
                    COUNT(DISTINCT s.chapter) as chapter_count
                FROM places_master pm
                JOIN sentence_places sp ON pm.place_id = sp.place_id
                JOIN sentences s ON sp.sentence_id = s.sentence_id
                WHERE pm.place_name = ? OR pm.canonical_name = ?
                GROUP BY pm.place_id
            """, (place_name, place_name))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # 各スコアの計算
            mention_score = self._calculate_mention_score(row[2])
            context_score = self._calculate_context_score(row[5], row[6])
            temporal_score = self._calculate_temporal_score(place_name)
            author_score = self._calculate_author_score(row[4])
            work_score = self._calculate_work_score(row[3])
            
            # 総合スコアの計算
            total_score = (
                mention_score * 0.3 +
                context_score * 0.2 +
                temporal_score * 0.2 +
                author_score * 0.15 +
                work_score * 0.15
            )
            
            # ランクの計算
            rank = self._calculate_rank(total_score)
            
            return PlaceImportance(
                place_name=row[0],
                canonical_name=row[1],
                total_score=total_score,
                mention_score=mention_score,
                context_score=context_score,
                temporal_score=temporal_score,
                author_score=author_score,
                work_score=work_score,
                rank=rank
            )
    
    def _calculate_mention_score(self, mention_count: int) -> float:
        """言及回数スコアの計算"""
        # 対数スケールで正規化
        return np.log1p(mention_count) / np.log1p(self._get_max_mentions())
    
    def _calculate_context_score(self, avg_position: float, chapter_count: int) -> float:
        """文脈スコアの計算"""
        # 位置と章の数を考慮
        position_score = 1 - (avg_position / self._get_max_position())
        chapter_score = chapter_count / self._get_max_chapters()
        return (position_score + chapter_score) / 2
    
    def _calculate_temporal_score(self, place_name: str) -> float:
        """時系列スコアの計算"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT DATE(s.created_at))
                FROM places_master pm
                JOIN sentence_places sp ON pm.place_id = sp.place_id
                JOIN sentences s ON sp.sentence_id = s.sentence_id
                WHERE pm.place_name = ? OR pm.canonical_name = ?
            """, (place_name, place_name))
            
            unique_days = cursor.fetchone()[0]
            return unique_days / self._get_max_unique_days()
    
    def _calculate_author_score(self, author_count: int) -> float:
        """作家スコアの計算"""
        return author_count / self._get_max_authors()
    
    def _calculate_work_score(self, work_count: int) -> float:
        """作品スコアの計算"""
        return work_count / self._get_max_works()
    
    def _calculate_rank(self, total_score: float) -> int:
        """ランクの計算"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) + 1
                FROM (
                    SELECT 
                        pm.place_id,
                        COUNT(sp.id) as mention_count
                    FROM places_master pm
                    JOIN sentence_places sp ON pm.place_id = sp.place_id
                    GROUP BY pm.place_id
                    HAVING mention_count > (
                        SELECT COUNT(sp.id)
                        FROM places_master pm
                        JOIN sentence_places sp ON pm.place_id = sp.place_id
                        WHERE pm.place_name = ?
                        GROUP BY pm.place_id
                    )
                )
            """, (self.place_name,))
            
            return cursor.fetchone()[0]
    
    def _get_max_mentions(self) -> int:
        """最大言及回数を取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT MAX(mention_count)
                FROM (
                    SELECT COUNT(sp.id) as mention_count
                    FROM places_master pm
                    JOIN sentence_places sp ON pm.place_id = sp.place_id
                    GROUP BY pm.place_id
                )
            """)
            return cursor.fetchone()[0]
    
    def _get_max_position(self) -> float:
        """最大位置を取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT MAX(position_in_work)
                FROM sentences
            """)
            return cursor.fetchone()[0]
    
    def _get_max_chapters(self) -> int:
        """最大章数を取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT MAX(chapter)
                FROM sentences
            """)
            return cursor.fetchone()[0]
    
    def _get_max_unique_days(self) -> int:
        """最大ユニーク日数を取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT DATE(created_at))
                FROM sentences
            """)
            return cursor.fetchone()[0]
    
    def _get_max_authors(self) -> int:
        """最大作家数を取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT author_id)
                FROM sentences
            """)
            return cursor.fetchone()[0]
    
    def _get_max_works(self) -> int:
        """最大作品数を取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT work_id)
                FROM sentences
            """)
            return cursor.fetchone()[0]
    
    def generate_importance_report(self, importance: PlaceImportance) -> str:
        """
        重要度レポートを生成
        
        Args:
            importance: 重要度情報
            
        Returns:
            レポート文字列
        """
        report = []
        report.append(f"地名: {importance.place_name}")
        report.append(f"正規名: {importance.canonical_name}")
        report.append(f"総合スコア: {importance.total_score:.2f}")
        report.append(f"ランク: {importance.rank}")
        report.append("\n詳細スコア:")
        report.append(f"- 言及回数スコア: {importance.mention_score:.2f}")
        report.append(f"- 文脈スコア: {importance.context_score:.2f}")
        report.append(f"- 時系列スコア: {importance.temporal_score:.2f}")
        report.append(f"- 作家スコア: {importance.author_score:.2f}")
        report.append(f"- 作品スコア: {importance.work_score:.2f}")
        
        return "\n".join(report) 