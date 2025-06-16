#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bungo Map System v4.0 Place Name Normalizer

地名の正規化・統一処理
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class NormalizedPlace:
    """正規化された地名情報"""
    original_name: str
    canonical_name: str
    prefecture: Optional[str] = None
    place_type: Optional[str] = None
    confidence: float = 1.0

class PlaceNameNormalizer:
    """地名正規化クラス"""
    
    def __init__(self):
        # 表記揺れパターン
        self.normalization_rules = {
            'ヶ': 'が',
            'ケ': 'が', 
            'ヵ': 'が',
            '　': ' ',
            '東京都': '東京',
            '大阪府': '大阪',
            '京都府': '京都'
        }
        
        # 地名タイプ判定パターン
        self.type_patterns = {
            '都道府県': [r'.*[都道府県]$', r'^(東京|京都|大阪)$'],
            '市区町村': [r'.*[市区町村]$'],
            '郡': [r'.*郡$'],
            '有名地名': []  # デフォルト
        }
    
    def normalize(self, place_name: str) -> NormalizedPlace:
        """
        地名を正規化
        
        Args:
            place_name: 正規化対象の地名
            
        Returns:
            正規化された地名情報
        """
        if not place_name:
            return NormalizedPlace(
                original_name="",
                canonical_name="",
                confidence=0.5
            )
        
        normalized = place_name.strip()
        
        # 表記揺れ統一
        for old, new in self.normalization_rules.items():
            normalized = normalized.replace(old, new)
        
        # 都道府県の正規化
        prefecture, prefecture_type = self._normalize_prefecture(normalized)
        if prefecture:
            return NormalizedPlace(
                original_name=place_name,
                canonical_name=prefecture,
                prefecture=prefecture,
                place_type=prefecture_type,
                confidence=1.0
            )
        
        # 市区町村の正規化
        city, city_type = self._normalize_city(normalized)
        if city:
            return NormalizedPlace(
                original_name=place_name,
                canonical_name=city,
                prefecture=self._extract_prefecture(place_name),
                place_type=city_type,
                confidence=0.9
            )
        
        # 地区の正規化
        district, district_type = self._normalize_district(normalized)
        if district:
            return NormalizedPlace(
                original_name=place_name,
                canonical_name=district,
                prefecture=self._extract_prefecture(place_name),
                place_type=district_type,
                confidence=0.8
            )
        
        # 正規化できない場合は元の地名をそのまま使用
        return NormalizedPlace(
            original_name=place_name,
            canonical_name=normalized,
            confidence=0.5
        )
    
    def _normalize_prefecture(self, place_name: str) -> Tuple[Optional[str], Optional[str]]:
        """都道府県の正規化"""
        for pattern, canonical, place_type in self.prefecture_patterns:
            if pattern.search(place_name):
                return canonical, place_type
        return None, None
    
    def _normalize_city(self, place_name: str) -> Tuple[Optional[str], Optional[str]]:
        """市区町村の正規化"""
        for pattern, canonical, place_type in self.city_patterns:
            if pattern.search(place_name):
                return canonical, place_type
        return None, None
    
    def _normalize_district(self, place_name: str) -> Tuple[Optional[str], Optional[str]]:
        """地区の正規化"""
        for pattern, canonical, place_type in self.district_patterns:
            if pattern.search(place_name):
                return canonical, place_type
        return None, None
    
    def _extract_prefecture(self, place_name: str) -> Optional[str]:
        """地名から都道府県を抽出"""
        for pattern, prefecture, _ in self.prefecture_patterns:
            if pattern.search(place_name):
                return prefecture
        return None
    
    def _compile_prefecture_patterns(self) -> List[Tuple[re.Pattern, str, str]]:
        """都道府県の正規表現パターンをコンパイル"""
        patterns = [
            (re.compile(r'東京(?:都|府)?'), '東京都', 'prefecture'),
            (re.compile(r'大阪(?:府|都)?'), '大阪府', 'prefecture'),
            (re.compile(r'京都(?:府|都)?'), '京都府', 'prefecture'),
            (re.compile(r'北海道'), '北海道', 'prefecture'),
            (re.compile(r'青森県?'), '青森県', 'prefecture'),
            (re.compile(r'岩手県?'), '岩手県', 'prefecture'),
            # ... 他の都道府県も同様に追加
        ]
        return patterns
    
    def _compile_city_patterns(self) -> List[Tuple[re.Pattern, str, str]]:
        """市区町村の正規表現パターンをコンパイル"""
        patterns = [
            (re.compile(r'東京(?:市|区)'), '東京都', 'city'),
            (re.compile(r'大阪(?:市|区)'), '大阪市', 'city'),
            (re.compile(r'横浜市'), '横浜市', 'city'),
            (re.compile(r'名古屋市'), '名古屋市', 'city'),
            (re.compile(r'札幌市'), '札幌市', 'city'),
            # ... 他の市区町村も同様に追加
        ]
        return patterns
    
    def _compile_district_patterns(self) -> List[Tuple[re.Pattern, str, str]]:
        """地区の正規表現パターンをコンパイル"""
        patterns = [
            (re.compile(r'新宿(?:区|市)?'), '新宿区', 'district'),
            (re.compile(r'渋谷(?:区|市)?'), '渋谷区', 'district'),
            (re.compile(r'池袋(?:区|市)?'), '池袋', 'district'),
            (re.compile(r'銀座(?:区|市)?'), '銀座', 'district'),
            (re.compile(r'秋葉原(?:区|市)?'), '秋葉原', 'district'),
            # ... 他の地区も同様に追加
        ]
        return patterns
    
    def determine_place_type(self, place_name: str) -> str:
        """地名タイプ判定"""
        normalized = self.normalize(place_name)
        
        for place_type, patterns in self.type_patterns.items():
            for pattern in patterns:
                if re.match(pattern, normalized):
                    return place_type
        
        return '有名地名'  # デフォルト
    
    def generate_aliases(self, place_name: str) -> List[str]:
        """地名の別名候補生成"""
        aliases = []
        
        # 基本正規化
        normalized = self.normalize(place_name)
        if normalized != place_name:
            aliases.append(normalized)
        
        # 都道府県の別名
        if place_name.endswith('都'):
            aliases.append(place_name[:-1])
        elif place_name.endswith('府'):
            aliases.append(place_name[:-1])
        elif place_name.endswith('県'):
            aliases.append(place_name[:-1])
        
        # 重複除去
        aliases = list(set(aliases))
        
        return [alias for alias in aliases if alias != place_name] 