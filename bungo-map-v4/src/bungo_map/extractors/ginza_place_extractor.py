#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GiNZAを使用した地名抽出器
"""

import ginza
import spacy
from typing import List, Dict, Any, Optional
from .base_extractor import BasePlaceExtractor, ExtractedPlace

class GinzaPlaceExtractor(BasePlaceExtractor):
    """GiNZAを使用した地名抽出器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.nlp = spacy.load('ja_ginza')
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
        doc = self.nlp(text)
        places = []
        
        for ent in doc.ents:
            if ent.label_ in ['LOC', 'GPE']:  # 地名または地理的実体
                place = ExtractedPlace(
                    place_name=ent.text,
                    start_pos=ent.start_char,
                    end_pos=ent.end_char,
                    confidence=1.0,  # GiNZAは信頼度を提供しないため1.0
                    context_before=context_before,
                    context_after=context_after,
                    place_type=ent.label_
                )
                
                if self.validate_place(place):
                    places.append(place)
        
        return places
    
    def get_description(self) -> str:
        """抽出器の説明を取得"""
        return "GiNZAを使用した地名抽出器（LOC, GPEラベル）"
    
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
        
        # GiNZA固有の検証
        if place.place_type not in ['LOC', 'GPE']:
            return False
        
        return True 