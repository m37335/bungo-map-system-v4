#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 地名抽出統合システム
Regex、GinzaNLP、AI複合地名抽出を統合する高精度抽出
"""

import logging
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from bungo_map.core.models import Place
from bungo_map.extractors.simple_place_extractor import SimplePlaceExtractor
from bungo_map.ai.validators.context_analyzer import ContextAnalyzer
from bungo_map.ai.cleaners.place_cleaner import PlaceCleaner
from bungo_map.ai.extractors.precise_compound_extractor import PreciseCompoundExtractor

logger = logging.getLogger(__name__)

class ExtractionMethod(Enum):
    """抽出手法の種類"""
    REGEX = "regex"
    GINZA_NLP = "ginza_nlp"
    AI_CONTEXT = "ai_context"
    AI_COMPOUND = "ai_compound"  # 新追加
    MANUAL = "manual"

@dataclass
class ExtractionResult:
    """抽出結果の統合データ"""
    place_name: str
    confidence: float
    extraction_method: ExtractionMethod
    original_confidence: float
    sentence: str
    before_text: str
    after_text: str
    category: str
    reasoning: str = ""
    is_valid: bool = True

class ExtractionCoordinator:
    """地名抽出の統合調整システム"""
    
    def __init__(self, openai_api_key: str = None):
        self.regex_extractor = SimplePlaceExtractor()
        
        # APIキーが提供された場合のみAI機能を有効化
        self.ai_enabled = openai_api_key is not None
        if self.ai_enabled:
            self.context_analyzer = ContextAnalyzer(openai_api_key)
            self.place_cleaner = PlaceCleaner()
            self.compound_extractor = PreciseCompoundExtractor(openai_api_key)  # 新追加
        
        # 手法別の基本信頼度と優先度（バランス戦略）
        self.method_configs = {
            ExtractionMethod.REGEX: {
                "base_reliability": 0.95,  # Regex系は高精度維持
                "priority": 1,             # 最高優先度維持
                "trust_threshold": 0.6     # 閾値を緩和（0.7→0.6）
            },
            ExtractionMethod.GINZA_NLP: {
                "base_reliability": 0.75,  # 中程度の精度
                "priority": 3,             # 優先度を下げる（AI複合地名抽出を優先）
                "trust_threshold": 0.65    # 閾値を上げる（0.6→0.65）
            },
            ExtractionMethod.AI_COMPOUND: {
                "base_reliability": 0.90,  # 高精度複合地名抽出
                "priority": 2,             # Regexの次に高い優先度
                "trust_threshold": 0.7     # 高信頼度
            },
            ExtractionMethod.AI_CONTEXT: {
                "base_reliability": 0.85,  # 文脈分析は高精度
                "priority": 0,             # 検証用（優先度外）
                "trust_threshold": 0.75    # 閾値を下げる（0.8→0.75）
            }
        }
        
        ai_status = "有効" if self.ai_enabled else "無効"
        logger.info(f"✅ 地名抽出統合システム初期化完了 (AI機能: {ai_status})")
    
    def extract_and_coordinate(self, work_id: int, text: str, aozora_url: str = None) -> List[Place]:
        """統合地名抽出の実行"""
        logger.info(f"🎯 統合地名抽出開始 (work_id: {work_id})")
        
        # 各手法での抽出実行
        regex_results = self._extract_with_regex(work_id, text, aozora_url)
        ginza_results = self._extract_with_ginza(work_id, text, aozora_url)
        compound_results = self._extract_with_ai_compound(work_id, text, aozora_url)  # 新追加
        
        # 結果の統合と調整
        coordinated_results = self._coordinate_results(regex_results, ginza_results, compound_results, text)
        
        # AI文脈分析による品質向上
        validated_results = self._apply_ai_validation(coordinated_results)
        
        # 最終的なPlaceオブジェクトに変換
        final_places = self._convert_to_places(validated_results, work_id, aozora_url)
        
        logger.info(f"✅ 統合抽出完了: {len(final_places)}件")
        return final_places
    
    def _extract_with_regex(self, work_id: int, text: str, aozora_url: str) -> List[ExtractionResult]:
        """Regex抽出"""
        places = self.regex_extractor.extract_places_from_text(work_id, text, aozora_url)
        
        results = []
        for place in places:
            # extraction_methodから手法を判定
            if place.extraction_method.startswith('regex_'):
                method = ExtractionMethod.REGEX
                category = place.extraction_method.replace('regex_', '')
            else:
                method = ExtractionMethod.REGEX
                category = "unknown"
            
            results.append(ExtractionResult(
                place_name=place.place_name,
                confidence=place.confidence,
                extraction_method=method,
                original_confidence=place.confidence,
                sentence=place.sentence,
                before_text=place.before_text,
                after_text=place.after_text,
                category=category,
                reasoning=f"Regex抽出: {category}"
            ))
        
        logger.info(f"📍 Regex抽出: {len(results)}件")
        return results
    
    def _extract_with_ginza(self, work_id: int, text: str, aozora_url: str) -> List[ExtractionResult]:
        """GinzaNLP抽出（シミュレート）"""
        # 実際のGinzaNLP抽出は既存システムを使用
        # ここでは問題のある抽出例をシミュレート
        
        # データベースからginza_nlp結果を取得してシミュレート
        known_ginza_issues = [
            ("萩", "plant", "大きな萩が人の背より高く延びて"),
            ("柏", "building_part", "高柏寺の五重の塔"),
            ("東", "direction", "東から西へ貫いた廊下"),
            ("都", "general_noun", "都のまん中に立って")
        ]
        
        results = []
        for place_name, issue_type, context in known_ginza_issues:
            if place_name in text:
                results.append(ExtractionResult(
                    place_name=place_name,
                    confidence=0.6,  # GinzaNLPの標準信頼度
                    extraction_method=ExtractionMethod.GINZA_NLP,
                    original_confidence=0.6,
                    sentence=context,
                    before_text="",
                    after_text="",
                    category="地名候補",
                    reasoning=f"GinzaNLP抽出: {issue_type}の可能性"
                ))
        
        logger.info(f"📍 GinzaNLP抽出: {len(results)}件")
        return results
    
    def _extract_with_ai_compound(self, work_id: int, text: str, aozora_url: str) -> List[ExtractionResult]:
        """AI複合地名抽出"""
        if not self.ai_enabled:
            logger.info("⚠️  AI機能無効: 複合地名抽出をスキップ")
            return []
        
        places = self.compound_extractor.extract_precise_places(work_id, text, aozora_url)
        
        results = []
        for place in places:
            # extraction_methodから手法を判定
            method = ExtractionMethod.AI_COMPOUND
            category = place.extraction_method.replace('precise_compound_', '')
            
            results.append(ExtractionResult(
                place_name=place.place_name,
                confidence=place.confidence,
                extraction_method=method,
                original_confidence=place.confidence,
                sentence=place.sentence,
                before_text=place.before_text,
                after_text=place.after_text,
                category=category,
                reasoning=f"AI複合地名抽出: {category}"
            ))
        
        logger.info(f"📍 AI複合地名抽出: {len(results)}件")
        return results
    
    def _coordinate_results(self, regex_results: List[ExtractionResult], 
                          ginza_results: List[ExtractionResult], 
                          compound_results: List[ExtractionResult], 
                          text: str) -> List[ExtractionResult]:
        """抽出結果の統合調整"""
        logger.info("🔄 抽出結果の統合調整中...")
        
        # すべての結果をマージ
        all_results = regex_results + ginza_results + compound_results
        
        # 文別にグループ化
        by_sentence = {}
        for result in all_results:
            sentence_key = result.sentence[:50] if result.sentence else ""
            if sentence_key not in by_sentence:
                by_sentence[sentence_key] = []
            by_sentence[sentence_key].append(result)
        
        coordinated = []
        
        for sentence, sentence_results in by_sentence.items():
            if len(sentence_results) == 1:
                coordinated.extend(sentence_results)
                continue
            
            # 同じ地名の重複をチェック
            by_place_name = {}
            for result in sentence_results:
                if result.place_name not in by_place_name:
                    by_place_name[result.place_name] = []
                by_place_name[result.place_name].append(result)
            
            for place_name, place_results in by_place_name.items():
                if len(place_results) == 1:
                    coordinated.extend(place_results)
                else:
                    # 手法の優先度で選択
                    best_result = self._select_best_by_priority(place_results)
                    coordinated.append(best_result)
        
        logger.info(f"✅ 統合調整完了: {len(coordinated)}件")
        return coordinated
    
    def _select_best_by_priority(self, results: List[ExtractionResult]) -> ExtractionResult:
        """優先度に基づく最適結果の選択"""
        # 優先度順でソート（数値が小さいほど高優先度）
        sorted_results = sorted(results, key=lambda r: (
            self.method_configs[r.extraction_method]["priority"],
            -r.confidence,
            -len(r.place_name)
        ))
        
        best = sorted_results[0]
        
        # 選択理由を更新
        if len(results) > 1:
            other_methods = [r.extraction_method.value for r in sorted_results[1:]]
            best.reasoning += f" (優先選択: {', '.join(other_methods)}より高優先度)"
        
        return best
    
    def _apply_ai_validation(self, results: List[ExtractionResult]) -> List[ExtractionResult]:
        """AI文脈分析による品質向上"""
        if not self.ai_enabled:
            logger.info("⚠️  AI機能無効: 基本的な信頼度フィルタリングのみ実行")
            return self._basic_validation(results)
        
        logger.info("🤖 AI文脈分析による検証中...")
        
        validated = []
        
        for result in results:
            # GinzaNLPの結果には必ずAI検証を適用
            if result.extraction_method == ExtractionMethod.GINZA_NLP:
                try:
                    # 文脈分析実行
                    analysis = self.context_analyzer.analyze_place_context(
                        result.place_name,
                        result.sentence,
                        result.before_text,
                        result.after_text
                    )
                    
                    # 分析結果で信頼度調整
                    if analysis.is_valid_place:
                        result.confidence = min(result.confidence * 1.2, 1.0)
                        result.reasoning += f" | AI検証: {analysis.reasoning}"
                    else:
                        result.confidence *= 0.3  # 大幅に信頼度を下げる
                        result.is_valid = False
                        result.reasoning += f" | AI除外: {analysis.reasoning}"
                    
                except Exception as e:
                    logger.warning(f"AI分析エラー ({result.place_name}): {e}")
            
            # 信頼度閾値でフィルタリング
            threshold = self.method_configs[result.extraction_method]["trust_threshold"]
            if result.confidence >= threshold and result.is_valid:
                validated.append(result)
            else:
                logger.debug(f"除外: {result.place_name} (信頼度: {result.confidence:.2f} < {threshold})")
        
        logger.info(f"✅ AI検証完了: {len(validated)}件 (除外: {len(results) - len(validated)}件)")
        return validated
    
    def _basic_validation(self, results: List[ExtractionResult]) -> List[ExtractionResult]:
        """AI無効時の基本検証"""
        validated = []
        
        for result in results:
            # GinzaNLPの結果は信頼度を少し下げる（AI検証なしのため）
            if result.extraction_method == ExtractionMethod.GINZA_NLP:
                result.confidence *= 0.8  # AI検証なしの補正
                result.reasoning += " | AI検証なし: 信頼度補正適用"
            
            # 信頼度閾値でフィルタリング
            threshold = self.method_configs[result.extraction_method]["trust_threshold"]
            if result.confidence >= threshold and result.is_valid:
                validated.append(result)
            else:
                logger.debug(f"除外: {result.place_name} (信頼度: {result.confidence:.2f} < {threshold})")
        
        logger.info(f"✅ 基本検証完了: {len(validated)}件 (除外: {len(results) - len(validated)}件)")
        return validated
    
    def _convert_to_places(self, results: List[ExtractionResult], 
                          work_id: int, aozora_url: str) -> List[Place]:
        """ExtractionResultをPlaceオブジェクトに変換"""
        places = []
        
        for result in results:
            place = Place(
                work_id=work_id,
                place_name=result.place_name,
                before_text=result.before_text,
                sentence=result.sentence,
                after_text=result.after_text,
                aozora_url=aozora_url,
                confidence=result.confidence,
                extraction_method=f"{result.extraction_method.value}_{result.category}_integrated"
            )
            places.append(place)
        
        return places
    
    def get_extraction_statistics(self) -> Dict:
        """抽出統計の取得"""
        return {
            "method_configs": self.method_configs,
            "available_methods": [method.value for method in ExtractionMethod],
            "priority_order": [
                "1. Regex (最高精度・優先)",
                "2. GinzaNLP (高カバレッジ・AI検証必須)",
                "3. AI文脈分析 (品質向上・除外判定)"
            ],
            "integration_strategy": {
                "duplicate_resolution": "優先度ベース選択",
                "quality_control": "AI文脈分析による検証",
                "confidence_threshold": "手法別閾値適用"
            }
        }

# 使用例とテスト
def test_integration():
    """統合システムのテスト"""
    coordinator = ExtractionCoordinator()
    
    test_texts = [
        "然るに、ことしの二月、私は千葉県船橋市に疎開している或る友人をたずねた",
        "大きな萩が人の背より高く延びて、その奥に見える東京の空",
        "高柏寺の五重の塔から都のまん中を眺める"
    ]
    
    print("🧪 統合抽出システムテスト\n")
    
    for i, text in enumerate(test_texts, 1):
        print(f"【テスト{i}】: {text[:40]}...")
        
        try:
            places = coordinator.extract_and_coordinate(999, text)
            print(f"結果: {len(places)}件抽出")
            
            for place in places:
                print(f"  📍 {place.place_name} ({place.extraction_method}, 信頼度: {place.confidence:.2f})")
        
        except Exception as e:
            print(f"  ❌ エラー: {e}")
        
        print()

if __name__ == "__main__":
    test_integration() 