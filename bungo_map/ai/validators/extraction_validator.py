"""
地名抽出品質検証システム

青空文庫からの地名抽出結果を多角的に検証
"""

import sqlite3
import re
import json
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from collections import Counter, defaultdict
import pandas as pd

from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ExtractionIssue:
    """抽出問題"""
    place_id: int
    place_name: str
    issue_type: str  # 'false_positive', 'context_mismatch', 'boundary_error', 'suspicious'
    severity: str    # 'high', 'medium', 'low'
    description: str
    context: str
    suggestion: str

@dataclass
class ExtractionStats:
    """抽出統計"""
    total_places: int
    unique_places: int
    avg_confidence: float
    extraction_methods: Dict[str, int]
    work_distribution: Dict[str, int]
    author_distribution: Dict[str, int]
    suspicious_patterns: List[str]

class ExtractionValidator:
    """地名抽出品質検証クラス"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        # 検証パターン
        self.person_name_patterns = [
            r'[一-龯]{1,2}(太郎|次郎|三郎|四郎|五郎)',
            r'[一-龯]{1,3}(子|美|恵|香|代)',
        ]
        
        self.non_place_indicators = [
            '氏', '様', '先生', '君', '嬢', '殿', '社', '会社', '株式会社',
            '大学', '学校', '病院', '駅', '空港', '店', '屋'
        ]
        
        self.suspicious_patterns = [
            r'^[一-龯]{1}$',  # 一文字地名
            r'[0-9]+',        # 数字を含む
        ]
    
    def validate_all_extractions(self, limit: Optional[int] = None) -> List[ExtractionIssue]:
        """全地名抽出結果を検証"""
        places_data = self._fetch_places_for_validation(limit)
        issues = []
        
        logger.info(f"地名抽出検証開始: {len(places_data)}件")
        
        for place_data in places_data:
            place_issues = self._validate_single_extraction(place_data)
            issues.extend(place_issues)
        
        logger.info(f"検証完了: {len(issues)}件の問題を検出")
        return issues
    
    def _validate_single_extraction(self, place_data: Dict) -> List[ExtractionIssue]:
        """単一地名抽出の検証"""
        issues = []
        place_name = place_data['place_name']
        context = place_data.get('sentence', '')
        
        # 人名パターンチェック
        if self._is_likely_person_name(place_name):
            issues.append(ExtractionIssue(
                place_id=place_data['place_id'],
                place_name=place_name,
                issue_type='false_positive',
                severity='high',
                description='人名と思われる抽出',
                context=context,
                suggestion='人名である可能性が高いため削除を検討'
            ))
        
        return issues
    
    def _is_likely_person_name(self, name: str) -> bool:
        """人名らしさをチェック"""
        for pattern in self.person_name_patterns:
            if re.search(pattern, name):
                return True
        return False
    
    def _fetch_places_for_validation(self, limit: Optional[int] = None) -> List[Dict]:
        """検証用地名データを取得"""
        query = """
        SELECT 
            p.place_id,
            p.place_name,
            p.sentence,
            p.before_text,
            p.after_text
        FROM places p
        WHERE p.place_name IS NOT NULL
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query)
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def get_extraction_statistics(self) -> ExtractionStats:
        """抽出統計を取得"""
        with sqlite3.connect(self.db_path) as conn:
            # 基本統計
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT place_name) as distinct_count,
                    AVG(confidence) as avg_conf
                FROM places
            """)
            total, distinct_count, avg_conf = cursor.fetchone()
            
            # 抽出方法別統計
            cursor = conn.execute("""
                SELECT extraction_method, COUNT(*) 
                FROM places 
                GROUP BY extraction_method
            """)
            extraction_methods = dict(cursor.fetchall())
            
            # 作品別統計
            cursor = conn.execute("""
                SELECT w.title, COUNT(*) 
                FROM places p
                LEFT JOIN works w ON p.work_id = w.work_id
                GROUP BY w.title
                ORDER BY COUNT(*) DESC
                LIMIT 20
            """)
            work_distribution = dict(cursor.fetchall())
            
            # 作者別統計
            cursor = conn.execute("""
                SELECT a.name, COUNT(*) 
                FROM places p
                LEFT JOIN works w ON p.work_id = w.work_id
                LEFT JOIN authors a ON w.author_id = a.author_id
                GROUP BY a.name
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """)
            author_distribution = dict(cursor.fetchall())
            
            # 疑わしいパターンの検出
            cursor = conn.execute("SELECT place_name FROM places")
            place_names = [row[0] for row in cursor.fetchall()]
            
            suspicious_patterns = []
            for pattern in self.suspicious_patterns:
                matches = [name for name in place_names if re.search(pattern, name)]
                if matches:
                    suspicious_patterns.append(f"{pattern}: {len(matches)}件")
        
        return ExtractionStats(
            total_places=total,
            unique_places=distinct_count,
            avg_confidence=avg_conf or 0.0,
            extraction_methods=extraction_methods,
            work_distribution=work_distribution,
            author_distribution=author_distribution,
            suspicious_patterns=suspicious_patterns
        )
    
    def analyze_missing_extractions(self, work_ids: List[int] = None) -> Dict[str, Any]:
        """抽出漏れの分析（高度な分析）"""
        # この機能は将来的に、作品の全文を再解析して
        # 現在の抽出結果と比較することで実装可能
        return {
            "status": "not_implemented",
            "suggestion": "作品全文の再解析機能が必要"
        } 