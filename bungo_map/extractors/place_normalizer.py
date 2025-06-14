"""
地名正規化システム

地名の正規化、タイプ判定、別名生成を実装
"""

from typing import List, Dict, Any, Optional
import re
from dataclasses import dataclass


@dataclass
class PlaceType:
    """地名タイプ"""
    name: str
    description: str
    examples: List[str]


class PlaceNameNormalizer:
    """地名正規化システム"""
    
    def __init__(self):
        self.place_types = {
            'prefecture': PlaceType(
                name='都道府県',
                description='日本の都道府県',
                examples=['東京都', '大阪府', '北海道']
            ),
            'city': PlaceType(
                name='市区町村',
                description='日本の市区町村',
                examples=['新宿区', '横浜市', '札幌市']
            ),
            'station': PlaceType(
                name='駅',
                description='鉄道駅',
                examples=['東京駅', '新宿駅', '渋谷駅']
            ),
            'landmark': PlaceType(
                name='ランドマーク',
                description='有名な建物や場所',
                examples=['東京タワー', 'スカイツリー', '浅草寺']
            ),
            'natural': PlaceType(
                name='自然地形',
                description='山、川、海などの自然地形',
                examples=['富士山', '利根川', '太平洋']
            ),
            'historical': PlaceType(
                name='史跡',
                description='歴史的な場所',
                examples=['江戸城', '日光東照宮', '姫路城']
            )
        }
        
        # 正規化ルール
        self.normalization_rules = [
            (r'^東京都(.+区)$', r'\1'),  # 東京都新宿区 → 新宿区
            (r'^(.+?)市(.+区)$', r'\1市\2'),  # 横浜市中区 → 横浜市中区
            (r'^(.+?)駅$', r'\1駅'),  # 新宿駅 → 新宿駅
            (r'^(.+?)山$', r'\1山'),  # 富士山 → 富士山
        ]
        
        # 別名生成ルール
        self.alias_rules = [
            (r'^(.+?)市$', [r'\1', r'\1市']),  # 横浜市 → [横浜, 横浜市]
            (r'^(.+?)区$', [r'\1', r'\1区']),  # 新宿区 → [新宿, 新宿区]
            (r'^(.+?)駅$', [r'\1', r'\1駅']),  # 新宿駅 → [新宿, 新宿駅]
        ]
    
    def normalize(self, place_name: str) -> str:
        """地名の正規化"""
        normalized = place_name
        
        for pattern, replacement in self.normalization_rules:
            if re.match(pattern, normalized):
                normalized = re.sub(pattern, replacement, normalized)
                break
        
        return normalized
    
    def determine_place_type(self, place_name: str) -> str:
        """地名タイプの判定"""
        for type_name, type_info in self.place_types.items():
            for example in type_info.examples:
                if example in place_name:
                    return type_name
        
        return 'unknown'
    
    def generate_aliases(self, place_name: str) -> List[str]:
        """地名の別名生成"""
        aliases = [place_name]
        
        for pattern, replacements in self.alias_rules:
            if re.match(pattern, place_name):
                for replacement in replacements:
                    alias = re.sub(pattern, replacement, place_name)
                    if alias not in aliases:
                        aliases.append(alias)
        
        return aliases 