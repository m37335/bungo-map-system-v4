"""
Bungo Map System v4.0 Place Name Normalizer

地名の正規化・統一処理
"""

import re
from typing import List, Dict, Any, Optional


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
    
    def normalize(self, place_name: str) -> str:
        """地名正規化"""
        if not place_name:
            return ""
        
        normalized = place_name.strip()
        
        # 表記揺れ統一
        for old, new in self.normalization_rules.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
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