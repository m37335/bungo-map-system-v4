#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪ゆかり地図システム v4.0 - 品質管理サービス
"""

import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import sqlite3
from datetime import datetime

class QualityManagementService:
    """品質管理サービス"""
    
    def __init__(self, db_path: Optional[str] = None):
        """初期化
        
        Args:
            db_path: データベースパス（省略時はデフォルト）
        """
        self.db_path = db_path or 'data/bungo_v4.db'
        self.quality_threshold = 0.7
        self.duplicate_threshold = 0.8
    
    def detect_new_data(self) -> Dict[str, Any]:
        """新規データの検知
        
        Returns:
            データ状態の辞書
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 地名データの統計
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_places,
                    COUNT(DISTINCT place_name) as unique_places,
                    COUNT(DISTINCT work_id) as works_with_places
                FROM places
            """)
            stats = dict(cursor.fetchone())
            
            # 信頼度分布
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN confidence >= 0.9 THEN 'high'
                        WHEN confidence >= 0.7 THEN 'medium'
                        ELSE 'low'
                    END as confidence_level,
                    COUNT(*) as count
                FROM places
                GROUP BY confidence_level
            """)
            confidence_stats = dict(cursor.fetchall())
            
            return {
                'stats': stats,
                'confidence_distribution': confidence_stats,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_quality_score(self) -> float:
        """品質スコアの計算
        
        Returns:
            品質スコア（0-100）
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 基本統計
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(confidence) as avg_confidence,
                    COUNT(CASE WHEN confidence >= 0.7 THEN 1 END) as high_confidence
                FROM places
            """)
            total, avg_confidence, high_confidence = cursor.fetchone()
            
            if total == 0:
                return 0.0
            
            # スコア計算
            confidence_score = (high_confidence / total) * 60  # 信頼度の重み: 60%
            uniqueness_score = 40  # 一意性の重み: 40%
            
            return min(100.0, confidence_score + uniqueness_score)
    
    def run_adaptive_cleanup(self) -> Dict[str, Any]:
        """適応型クリーンアップの実行
        
        Returns:
            クリーンアップ結果
        """
        before_score = self.get_quality_score()
        actions_taken = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. 低信頼度データの削除
            cursor.execute("""
                DELETE FROM places 
                WHERE confidence < ?
            """, (self.quality_threshold,))
            low_confidence_removed = cursor.rowcount
            if low_confidence_removed > 0:
                actions_taken.append(f"低信頼度データ{low_confidence_removed}件を削除")
            
            # 2. 重複データの統合
            cursor.execute("""
                SELECT place_name, COUNT(*) as count
                FROM places
                GROUP BY place_name
                HAVING count > 1
            """)
            duplicates = cursor.fetchall()
            
            for place_name, count in duplicates:
                # 最も信頼度の高いデータを残す
                cursor.execute("""
                    DELETE FROM places
                    WHERE place_name = ? AND place_id NOT IN (
                        SELECT place_id
                        FROM places
                        WHERE place_name = ?
                        ORDER BY confidence DESC
                        LIMIT 1
                    )
                """, (place_name, place_name))
                removed = cursor.rowcount
                if removed > 0:
                    actions_taken.append(f"重複データ{removed}件を統合: {place_name}")
            
            conn.commit()
        
        after_score = self.get_quality_score()
        
        return {
            'before_score': before_score,
            'after_score': after_score,
            'improvement': after_score - before_score,
            'actions_taken': actions_taken
        } 