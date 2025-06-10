#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚖️ 地名抽出優先順位オプティマイザー
動的な優先順位調整とバランス最適化
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

@dataclass
class PriorityConfig:
    """優先順位設定"""
    base_reliability: float
    priority: int
    trust_threshold: float
    weight_precision: float = 1.0    # 精度重視度
    weight_recall: float = 1.0       # 網羅性重視度

class PriorityOptimizer:
    """優先順位の動的最適化"""
    
    def __init__(self):
        # 現在の設定
        self.current_configs = {
            "regex": PriorityConfig(0.95, 1, 0.7, 1.0, 0.7),     # 精度重視
            "ginza_nlp": PriorityConfig(0.75, 2, 0.6, 0.6, 1.0), # 網羅性重視
            "ai_context": PriorityConfig(0.85, 0, 0.8, 0.9, 0.8) # バランス型
        }
        
        # 最適化の履歴
        self.optimization_history = []
    
    def analyze_current_performance(self) -> Dict:
        """現在の性能分析"""
        return {
            "strengths": {
                "regex": [
                    "完全地名の高精度抽出",
                    "重複問題の解決",
                    "境界条件による誤抽出防止"
                ],
                "ginza_nlp": [
                    "高いカバレッジ",
                    "未知地名の発見",
                    "自然言語処理の利点"
                ],
                "ai_context": [
                    "文脈による誤抽出除去",
                    "植物名・方向語の識別",
                    "意味的理解"
                ]
            },
            "weaknesses": {
                "regex": [
                    "明示リスト依存",
                    "新しい地名への対応不足",
                    "境界条件が厳しすぎる場合あり"
                ],
                "ginza_nlp": [
                    "誤抽出の多さ",
                    "文脈理解の限界",
                    "同音異義語の問題"
                ],
                "ai_context": [
                    "計算コストの高さ",
                    "API依存",
                    "処理速度の問題"
                ]
            },
            "benchmark_results": {
                "precision_focused_cases": "75%成功",  # 誤抽出防止
                "recall_focused_cases": "25%成功",     # 網羅性
                "overall_balance": "50%成功"
            }
        }
    
    def propose_optimizations(self) -> Dict:
        """最適化提案"""
        return {
            "strategy_1_precision_first": {
                "description": "精度優先戦略",
                "configs": {
                    "regex": PriorityConfig(0.95, 1, 0.65, 1.0, 0.6),    # 閾値を少し下げる
                    "ginza_nlp": PriorityConfig(0.70, 3, 0.75, 0.5, 1.0), # 閾値を上げて厳格化
                    "ai_context": PriorityConfig(0.90, 2, 0.85, 1.0, 0.7) # AI検証を強化
                },
                "benefits": [
                    "誤抽出の大幅削減",
                    "高品質データの確保",
                    "信頼性の向上"
                ],
                "trade_offs": [
                    "網羅性の低下",
                    "新規地名の見落とし"
                ]
            },
            
            "strategy_2_balanced": {
                "description": "バランス戦略",
                "configs": {
                    "regex": PriorityConfig(0.95, 1, 0.6, 0.8, 0.8),     # 少し緩和
                    "ginza_nlp": PriorityConfig(0.75, 2, 0.65, 0.7, 0.9), # 中程度の厳格さ
                    "ai_context": PriorityConfig(0.85, 0, 0.75, 0.9, 0.8) # 検証レベル調整
                },
                "benefits": [
                    "精度と網羅性のバランス",
                    "実用的な抽出率",
                    "多様な地名への対応"
                ],
                "trade_offs": [
                    "一部誤抽出の可能性",
                    "設定の複雑さ"
                ]
            },
            
            "strategy_3_coverage_first": {
                "description": "網羅性優先戦略",
                "configs": {
                    "regex": PriorityConfig(0.95, 1, 0.5, 0.6, 1.0),     # 大幅緩和
                    "ginza_nlp": PriorityConfig(0.80, 1, 0.4, 0.4, 1.0),  # 優先度上げ
                    "ai_context": PriorityConfig(0.85, 2, 0.6, 0.8, 1.0)  # 後処理で修正
                },
                "benefits": [
                    "最大限の地名カバレッジ",
                    "新規地名の発見",
                    "データの豊富さ"
                ],
                "trade_offs": [
                    "誤抽出の増加",
                    "後処理の必要性"
                ]
            }
        }
    
    def recommend_strategy(self, use_case: str) -> Dict:
        """用途別の推奨戦略"""
        recommendations = {
            "research": {
                "strategy": "strategy_1_precision_first",
                "reason": "研究用途では高品質なデータが最重要",
                "additional_settings": {
                    "enable_manual_review": True,
                    "ai_validation_required": True
                }
            },
            
            "visualization": {
                "strategy": "strategy_2_balanced",
                "reason": "地図表示では適度な網羅性と精度が必要",
                "additional_settings": {
                    "geographic_validation": True,
                    "duplicate_radius_check": 100  # 100m圏内重複チェック
                }
            },
            
            "exploration": {
                "strategy": "strategy_3_coverage_first",
                "reason": "探索的分析では網羅性を重視",
                "additional_settings": {
                    "confidence_based_display": True,
                    "experimental_features": True
                }
            },
            
            "production": {
                "strategy": "strategy_2_balanced",
                "reason": "本番環境では安定性とバランスが重要",
                "additional_settings": {
                    "error_handling": "graceful",
                    "performance_monitoring": True
                }
            }
        }
        
        return recommendations.get(use_case, recommendations["production"])
    
    def evaluate_strategy(self, strategy_name: str, test_cases: List[Dict]) -> Dict:
        """戦略の評価"""
        # ここでは概念的評価
        proposals = self.propose_optimizations()
        strategy = proposals.get(strategy_name)
        
        if not strategy:
            return {"error": "Unknown strategy"}
        
        # シミュレーション結果（実際には統合システムでテスト）
        simulated_results = {
            "strategy_1_precision_first": {
                "precision": 0.95,
                "recall": 0.60,
                "f1_score": 0.74,
                "false_positives": 2,
                "false_negatives": 8
            },
            "strategy_2_balanced": {
                "precision": 0.85,
                "recall": 0.80,
                "f1_score": 0.82,
                "false_positives": 6,
                "false_negatives": 4
            },
            "strategy_3_coverage_first": {
                "precision": 0.70,
                "recall": 0.95,
                "f1_score": 0.81,
                "false_positives": 15,
                "false_negatives": 1
            }
        }
        
        return {
            "strategy": strategy,
            "simulated_performance": simulated_results.get(strategy_name, {}),
            "recommendation": self._generate_recommendation(strategy_name)
        }
    
    def _generate_recommendation(self, strategy_name: str) -> str:
        """戦略別の推奨事項"""
        recommendations = {
            "strategy_1_precision_first": 
                "学術研究や高品質データが必要な用途に最適。誤抽出を最小限に抑制。",
            "strategy_2_balanced": 
                "一般的な用途に推奨。実用性と品質のバランスが良い。",
            "strategy_3_coverage_first": 
                "データ探索や新規地名発見に有効。後処理でのクリーニングが必要。"
        }
        
        return recommendations.get(strategy_name, "戦略が見つかりません")

# 使用例
def demonstrate_optimization():
    """最適化デモンストレーション"""
    optimizer = PriorityOptimizer()
    
    print("⚖️ 地名抽出優先順位オプティマイザー\n")
    
    # 現在の性能分析
    analysis = optimizer.analyze_current_performance()
    print("📊 現在の性能分析:")
    print(f"ベンチマーク結果: {analysis['benchmark_results']['overall_balance']}")
    
    # 最適化提案
    print("\n🎯 最適化戦略提案:")
    proposals = optimizer.propose_optimizations()
    
    for name, strategy in proposals.items():
        print(f"\n【{strategy['description']}】")
        print(f"利点: {', '.join(strategy['benefits'])}")
        
        # 戦略評価
        evaluation = optimizer.evaluate_strategy(name, [])
        performance = evaluation["simulated_performance"]
        if performance:
            print(f"予想性能: 精度={performance['precision']:.2f}, 網羅性={performance['recall']:.2f}, F1={performance['f1_score']:.2f}")
    
    # 用途別推奨
    print("\n🎪 用途別推奨:")
    use_cases = ["research", "visualization", "production"]
    
    for use_case in use_cases:
        rec = optimizer.recommend_strategy(use_case)
        print(f"{use_case}: {rec['strategy']} - {rec['reason']}")

if __name__ == "__main__":
    demonstrate_optimization() 