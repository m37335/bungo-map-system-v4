#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Sentence重複検知システム
現在のデータベースでのsentence部分の重複検知機能を調査・分析
"""

import sqlite3
import logging
from typing import Dict, List
from collections import defaultdict, Counter
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DuplicatePattern:
    pattern_type: str
    sentence: str
    duplicated_places: List[str]
    extraction_methods: List[str]
    severity: str
    recommendation: str

class DatabaseVerificationSystem:
    def __init__(self, db_path: str = "data/bungo_production.db"):
        self.db_path = db_path
    
    def analyze_sentence_duplicates(self) -> List[DuplicatePattern]:
        """Sentence レベルの重複分析"""
        logger.info("🔍 Sentence重複分析開始")
        patterns = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT sentence, 
                       GROUP_CONCAT(place_name, '|') as places,
                       GROUP_CONCAT(extraction_method, '|') as methods,
                       COUNT(*) as count
                FROM places 
                WHERE sentence IS NOT NULL AND sentence != ''
                GROUP BY sentence 
                HAVING COUNT(*) > 1 
                ORDER BY COUNT(*) DESC
            """)
            
            for sentence, places_str, methods_str, count in cursor.fetchall():
                places = places_str.split('|')
                methods = methods_str.split('|')
                
                unique_places = list(set(places))
                unique_methods = list(set(methods))
                
                # 重複パターンの分類
                if len(unique_places) == 1:
                    pattern_type = "extractor_conflict"
                    severity = "medium" if count <= 3 else "high"
                    recommendation = f"抽出器間で重複: {unique_methods}"
                elif count > 10:
                    pattern_type = "name_list"
                    severity = "low"
                    recommendation = "地名列挙文: 重要度の高い地名のみ保持"
                else:
                    pattern_type = "general_duplicate"
                    severity = "medium"
                    recommendation = "文脈と信頼度で優先度決定"
                
                patterns.append(DuplicatePattern(
                    pattern_type=pattern_type,
                    sentence=sentence[:100] + "..." if len(sentence) > 100 else sentence,
                    duplicated_places=unique_places,
                    extraction_methods=unique_methods,
                    severity=severity,
                    recommendation=recommendation
                ))
        
        logger.info(f"✅ {len(patterns)}件の重複パターンを検出")
        return patterns
    
    def analyze_extractor_conflicts(self) -> Dict:
        """抽出器間の競合分析"""
        logger.info("⚔️ 抽出器競合分析開始")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT place_name, extraction_method, COUNT(*) as count
                FROM places 
                GROUP BY place_name, extraction_method
                ORDER BY place_name, count DESC
            """)
            
            place_methods = defaultdict(list)
            for place_name, method, count in cursor.fetchall():
                place_methods[place_name].append((method, count))
        
        conflicts = {}
        for place_name, methods in place_methods.items():
            if len(methods) > 1:
                total_count = sum(count for _, count in methods)
                method_distribution = {
                    method: count / total_count for method, count in methods
                }
                
                max_ratio = max(method_distribution.values())
                if max_ratio < 0.7:  # どの手法も70%未満の場合
                    conflicts[place_name] = {
                        'methods': dict(methods),
                        'distribution': method_distribution,
                        'conflict_level': 'high' if max_ratio < 0.5 else 'medium',
                        'total_count': total_count
                    }
        
        logger.info(f"⚔️ {len(conflicts)}件の抽出器競合を検出")
        return conflicts
    
    def run_verification(self) -> Dict:
        """包括的検証の実行"""
        duplicate_patterns = self.analyze_sentence_duplicates()
        extractor_conflicts = self.analyze_extractor_conflicts()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM places")
            total_places = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(DISTINCT sentence) FROM places WHERE sentence IS NOT NULL")
            unique_sentences = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT COUNT(*) FROM (
                    SELECT sentence FROM places 
                    WHERE sentence IS NOT NULL 
                    GROUP BY sentence 
                    HAVING COUNT(*) > 1
                )
            """)
            sentence_duplicates = cursor.fetchone()[0]
        
        return {
            "total_places": total_places,
            "unique_sentences": unique_sentences,
            "sentence_duplicates": sentence_duplicates,
            "duplicate_patterns": len(duplicate_patterns),
            "extractor_conflicts": len(extractor_conflicts),
            "patterns": duplicate_patterns[:5],
            "conflicts": dict(list(extractor_conflicts.items())[:5])
        }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Sentence重複検知システム')
    parser.add_argument('command', choices=['verify', 'duplicates', 'conflicts'],
                       help='実行コマンド')
    args = parser.parse_args()
    
    verifier = DatabaseVerificationSystem()
    
    if args.command == 'verify':
        result = verifier.run_verification()
        print("🔍 データベース品質検証結果")
        print("=" * 50)
        print(f"📍 総地名数: {result['total_places']:,}")
        print(f"📝 ユニーク文数: {result['unique_sentences']:,}")
        print(f"🔄 Sentence重複: {result['sentence_duplicates']}件")
        print(f"📊 重複パターン: {result['duplicate_patterns']}件")
        print(f"⚔️ 抽出器競合: {result['extractor_conflicts']}件")
        
    elif args.command == 'duplicates':
        patterns = verifier.analyze_sentence_duplicates()
        print(f"🔄 Sentence重複分析: {len(patterns)}件検出")
        print("=" * 50)
        
        for i, pattern in enumerate(patterns[:5]):
            print(f"【{i+1}】{pattern.severity}: {pattern.pattern_type}")
            print(f"地名: {', '.join(pattern.duplicated_places)}")
            print(f"文: {pattern.sentence}")
            print(f"推奨: {pattern.recommendation}")
            print("-" * 40)
            
    elif args.command == 'conflicts':
        conflicts = verifier.analyze_extractor_conflicts()
        print(f"⚔️ 抽出器競合分析: {len(conflicts)}件検出")
        print("=" * 50)
        
        for place_name, info in list(conflicts.items())[:5]:
            print(f"地名: {place_name}")
            print(f"競合レベル: {info['conflict_level']}")
            print(f"分布: {info['distribution']}")
            print("-" * 40)

if __name__ == "__main__":
    main() 