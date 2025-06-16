#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名抽出器の基本インターフェース
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ExtractedPlace:
    """抽出された地名情報"""
    place_name: str
    start_pos: int
    end_pos: int
    confidence: float
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    place_type: Optional[str] = None
    prefecture: Optional[str] = None

class BasePlaceExtractor(ABC):
    """地名抽出器の基本クラス"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @abstractmethod
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
        pass
    
    def get_name(self) -> str:
        """抽出器の名前を取得"""
        return self.__class__.__name__
    
    def get_description(self) -> str:
        """抽出器の説明を取得"""
        return "基本的な地名抽出器"
    
    def validate_place(self, place: ExtractedPlace) -> bool:
        """
        抽出された地名の妥当性を検証
        
        Args:
            place: 検証対象の地名情報
            
        Returns:
            妥当な場合はTrue
        """
        # 基本的な検証
        if not place.place_name or len(place.place_name.strip()) == 0:
            return False
        
        if place.confidence < 0.0 or place.confidence > 1.0:
            return False
        
        if place.start_pos < 0 or place.end_pos <= place.start_pos:
            return False
        
        return True 