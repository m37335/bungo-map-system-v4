#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
複数の抽出器を組み合わせた統合抽出器
"""

from typing import List, Dict, Any, Optional
from .base_extractor import BasePlaceExtractor, ExtractedPlace
from .ginza_place_extractor import GinzaPlaceExtractor
from .regex_place_extractor import RegexPlaceExtractor

class UnifiedPlaceExtractor(BasePlaceExtractor):
    """複数の抽出器を組み合わせた統合抽出器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.extractors = [
            GinzaPlaceExtractor(config),
            RegexPlaceExtractor(config)
        ]
        self.min_confidence = self.config.get('min_confidence', 0.5)
    
    def extract(self, text: str, context_before: Optional[str] = None, 
                context_after: Optional[str] = None) -> List[ExtractedPlace]:
        """
        テキストから地名を抽出
        
        Args:
            text: 抽出対象のテキスト
            context_before: 前の文脈（オプション）
            context_after: 後の文脈（オプション）
            
        Returns:
            抽出された地名のリスト
        """
        all_places = []
        
        # 各抽出器で地名を抽出
        for extractor in self.extractors:
            try:
                places = extractor.extract(text, context_before, context_after)
                all_places.extend(places)
            except Exception as e:
                print(f"抽出器 {extractor.get_name()} でエラー: {e}")
                continue
        
        # 重複を除去し、信頼度の高いものを優先
        unique_places = self._deduplicate_places(all_places)
        
        return unique_places
    
    def _deduplicate_places(self, places: List[ExtractedPlace]) -> List[ExtractedPlace]:
        """
        重複する地名を除去
        
        Args:
            places: 抽出された地名のリスト
            
        Returns:
            重複を除去した地名のリスト
        """
        # 位置情報で重複を判定
        seen_positions = set()
        unique_places = []
        
        # 信頼度でソート
        sorted_places = sorted(places, key=lambda x: x.confidence, reverse=True)
        
        for place in sorted_places:
            position = (place.start_pos, place.end_pos)
            if position not in seen_positions:
                seen_positions.add(position)
                unique_places.append(place)
        
        return unique_places
    
    def get_description(self) -> str:
        """抽出器の説明を取得"""
        return "複数の抽出器を組み合わせた統合地名抽出器"
    
    def validate_place(self, place: ExtractedPlace) -> bool:
        """
        抽出された地名の妥当性を検証
        
        Args:
            place: 検証対象の地名情報
            
        Returns:
            妥当な場合はTrue
        """
        if not super().validate_place(place):
            return False
        
        if place.confidence < self.min_confidence:
            return False
        
        return True 