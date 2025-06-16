from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """バリデーション結果"""
    is_valid: bool
    score: float
    issues: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class QualityValidator:
    """品質チェック管理クラス"""
    
    def __init__(self):
        # 品質チェックの閾値
        self.thresholds = {
            "min_confidence": 0.6,
            "min_text_length": 10,
            "max_text_length": 1000,
            "min_place_name_length": 2,
            "max_place_name_length": 50
        }
        
        # 地名の正規表現パターン
        self.place_patterns = {
            "prefecture": r"(.+?[都道府県])",
            "city": r"(.+?[市区町村])",
            "district": r"(.+?郡)",
            "station": r"(.+?駅)",
            "landmark": r"(.+?[山|川|湖|海|公園|寺|神社])"
        }

    def validate_sentence(self, text: str) -> ValidationResult:
        """センテンスの品質チェック"""
        issues = []
        score = 1.0
        
        # テキスト長のチェック
        if len(text) < self.thresholds["min_text_length"]:
            issues.append({
                "type": "text_too_short",
                "message": "テキストが短すぎます",
                "value": len(text),
                "threshold": self.thresholds["min_text_length"]
            })
            score *= 0.8
            
        if len(text) > self.thresholds["max_text_length"]:
            issues.append({
                "type": "text_too_long",
                "message": "テキストが長すぎます",
                "value": len(text),
                "threshold": self.thresholds["max_text_length"]
            })
            score *= 0.9
            
        # 特殊文字のチェック
        if re.search(r'[^\w\s\u3000-\u9fff。、！？「」『』（）]', text):
            issues.append({
                "type": "invalid_characters",
                "message": "特殊文字が含まれています",
                "value": text
            })
            score *= 0.7
            
        return ValidationResult(
            is_valid=len(issues) == 0,
            score=score,
            issues=issues,
            metadata={
                "text_length": len(text),
                "checked_at": datetime.utcnow().isoformat()
            }
        )

    def validate_place(
        self,
        place_name: str,
        confidence: float,
        metadata: Dict[str, Any]
    ) -> ValidationResult:
        """地名の品質チェック"""
        issues = []
        score = 1.0
        
        # 地名長のチェック
        if len(place_name) < self.thresholds["min_place_name_length"]:
            issues.append({
                "type": "place_name_too_short",
                "message": "地名が短すぎます",
                "value": len(place_name),
                "threshold": self.thresholds["min_place_name_length"]
            })
            score *= 0.8
            
        if len(place_name) > self.thresholds["max_place_name_length"]:
            issues.append({
                "type": "place_name_too_long",
                "message": "地名が長すぎます",
                "value": len(place_name),
                "threshold": self.thresholds["max_place_name_length"]
            })
            score *= 0.9
            
        # 信頼度のチェック
        if confidence < self.thresholds["min_confidence"]:
            issues.append({
                "type": "low_confidence",
                "message": "信頼度が低すぎます",
                "value": confidence,
                "threshold": self.thresholds["min_confidence"]
            })
            score *= 0.7
            
        # 地名パターンのチェック
        pattern_matches = []
        for pattern_name, pattern in self.place_patterns.items():
            if re.match(pattern, place_name):
                pattern_matches.append(pattern_name)
                
        if not pattern_matches:
            issues.append({
                "type": "unrecognized_pattern",
                "message": "認識できない地名パターンです",
                "value": place_name
            })
            score *= 0.6
            
        return ValidationResult(
            is_valid=len(issues) == 0,
            score=score,
            issues=issues,
            metadata={
                "place_name_length": len(place_name),
                "pattern_matches": pattern_matches,
                "checked_at": datetime.utcnow().isoformat()
            }
        )

    def validate_sentence_place(
        self,
        sentence_text: str,
        place_name: str,
        context: str,
        confidence: float
    ) -> ValidationResult:
        """センテンス-地名関連の品質チェック"""
        issues = []
        score = 1.0
        
        # 文脈の存在チェック
        if not context:
            issues.append({
                "type": "missing_context",
                "message": "文脈が存在しません"
            })
            score *= 0.8
            
        # 地名の出現チェック
        if place_name not in sentence_text:
            issues.append({
                "type": "place_not_in_sentence",
                "message": "地名がセンテンスに含まれていません",
                "value": {
                    "place_name": place_name,
                    "sentence": sentence_text
                }
            })
            score *= 0.5
            
        # 文脈の長さチェック
        if len(context) < 10:
            issues.append({
                "type": "context_too_short",
                "message": "文脈が短すぎます",
                "value": len(context)
            })
            score *= 0.9
            
        return ValidationResult(
            is_valid=len(issues) == 0,
            score=score,
            issues=issues,
            metadata={
                "context_length": len(context),
                "checked_at": datetime.utcnow().isoformat()
            }
        )

    def calculate_quality_score(
        self,
        sentence_result: ValidationResult,
        place_result: ValidationResult,
        sentence_place_result: ValidationResult
    ) -> float:
        """総合品質スコアの計算"""
        # 各要素の重み付け
        weights = {
            "sentence": 0.3,
            "place": 0.4,
            "sentence_place": 0.3
        }
        
        # 重み付け平均の計算
        total_score = (
            sentence_result.score * weights["sentence"] +
            place_result.score * weights["place"] +
            sentence_place_result.score * weights["sentence_place"]
        )
        
        return round(total_score, 2)
