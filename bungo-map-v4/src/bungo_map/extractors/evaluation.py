#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名抽出結果の評価機能
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .base_extractor import ExtractedPlace
from .place_normalizer import PlaceNormalizer
from ..geocoding.place_geocoder import PlaceGeocoder, GeocodedPlace

@dataclass
class EvaluationResult:
    """評価結果"""
    total_places: int
    valid_places: int
    invalid_places: int
    geocoded_places: int
    average_confidence: float
    details: List[Dict[str, Any]]

class PlaceExtractionEvaluator:
    """地名抽出結果の評価クラス"""
    
    def __init__(self, geocoder: PlaceGeocoder):
        self.geocoder = geocoder
        self.normalizer = PlaceNormalizer()
    
    def evaluate(self, extracted_places: List[ExtractedPlace]) -> EvaluationResult:
        """
        抽出結果を評価
        
        Args:
            extracted_places: 抽出された地名のリスト
            
        Returns:
            評価結果
        """
        total_places = len(extracted_places)
        valid_places = 0
        invalid_places = 0
        geocoded_places = 0
        total_confidence = 0.0
        details = []
        
        for place in extracted_places:
            # 地名を正規化
            normalized = self.normalizer.normalize(place.place_name)
            
            # ジオコーディング
            geocoded = self.geocoder.geocode(normalized.canonical_name)
            
            # 評価
            is_valid = self._validate_place(place, normalized, geocoded)
            if is_valid:
                valid_places += 1
                total_confidence += place.confidence
            else:
                invalid_places += 1
            
            if geocoded:
                geocoded_places += 1
            
            # 詳細情報を記録
            details.append({
                'original_name': place.place_name,
                'canonical_name': normalized.canonical_name,
                'confidence': place.confidence,
                'is_valid': is_valid,
                'is_geocoded': bool(geocoded),
                'prefecture': normalized.prefecture,
                'place_type': normalized.place_type
            })
        
        # 平均信頼度を計算
        average_confidence = total_confidence / valid_places if valid_places > 0 else 0.0
        
        return EvaluationResult(
            total_places=total_places,
            valid_places=valid_places,
            invalid_places=invalid_places,
            geocoded_places=geocoded_places,
            average_confidence=average_confidence,
            details=details
        )
    
    def _validate_place(self, place: ExtractedPlace, 
                       normalized: NormalizedPlace,
                       geocoded: Optional[GeocodedPlace]) -> bool:
        """
        地名の妥当性を検証
        
        Args:
            place: 抽出された地名
            normalized: 正規化された地名
            geocoded: ジオコーディングされた地名
            
        Returns:
            妥当な場合はTrue
        """
        # 基本的な検証
        if not place.place_name or len(place.place_name.strip()) == 0:
            return False
        
        if place.confidence < 0.5:  # 信頼度が低すぎる
            return False
        
        # 正規化の結果を検証
        if not normalized.canonical_name:
            return False
        
        # ジオコーディングの結果を検証
        if geocoded and geocoded.confidence < 0.5:
            return False
        
        return True
    
    def generate_report(self, result: EvaluationResult) -> str:
        """
        評価レポートを生成
        
        Args:
            result: 評価結果
            
        Returns:
            レポート文字列
        """
        report = []
        report.append("地名抽出評価レポート")
        report.append("=" * 40)
        report.append(f"総抽出数: {result.total_places}")
        report.append(f"有効な地名: {result.valid_places}")
        report.append(f"無効な地名: {result.invalid_places}")
        report.append(f"ジオコーディング成功: {result.geocoded_places}")
        report.append(f"平均信頼度: {result.average_confidence:.2f}")
        
        report.append("\n詳細:")
        for detail in result.details:
            report.append(f"\n- {detail['original_name']} → {detail['canonical_name']}")
            report.append(f"  信頼度: {detail['confidence']:.2f}")
            report.append(f"  妥当性: {'有効' if detail['is_valid'] else '無効'}")
            report.append(f"  ジオコーディング: {'成功' if detail['is_geocoded'] else '失敗'}")
            if detail['prefecture']:
                report.append(f"  都道府県: {detail['prefecture']}")
            if detail['place_type']:
                report.append(f"  地名タイプ: {detail['place_type']}")
        
        return "\n".join(report) 