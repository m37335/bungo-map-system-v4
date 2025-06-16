#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名正規化システム v4
地名の表記揺れを吸収し、一貫性のあるデータを維持
"""

import re
import json
import logging
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class NormalizedPlace:
    """正規化地名データ"""
    canonical_name: str
    aliases: List[str]
    place_type: str
    prefecture: Optional[str] = None
    municipality: Optional[str] = None
    district: Optional[str] = None
    confidence: float = 0.0
    source: str = "normalizer"
    created_at: str = ""
    updated_at: str = ""

class PlaceNormalizer:
    """地名正規化システム v4"""
    
    def __init__(self):
        """初期化"""
        self.normalization_rules = self._build_normalization_rules()
        self.place_type_map = self._build_place_type_map()
        self.prefecture_map = self._build_prefecture_map()
        logger.info("🌟 地名正規化システムv4初期化完了")
    
    def _build_normalization_rules(self) -> Dict[str, Dict]:
        """正規化ルールの構築"""
        return {
            # 都道府県
            'prefectures': {
                '東京都': ['東京', '江戸'],
                '京都府': ['京都', '平安京'],
                '大阪府': ['大阪', '大坂'],
                '北海道': ['北海道', '蝦夷'],
                '沖縄県': ['沖縄', '琉球'],
                # 他の都道府県も同様に
            },
            
            # 主要都市
            'major_cities': {
                '横浜市': ['横浜'],
                '名古屋市': ['名古屋'],
                '神戸市': ['神戸'],
                '福岡市': ['福岡'],
                '札幌市': ['札幌'],
                # 他の主要都市も同様に
            },
            
            # 有名地名
            'famous_places': {
                '銀座': ['銀座通り', '銀座通り'],
                '新宿': ['新宿駅', '新宿区'],
                '渋谷': ['渋谷駅', '渋谷区'],
                '浅草': ['浅草寺', '浅草観音'],
                '鎌倉': ['鎌倉市', '鎌倉町'],
                # 他の有名地名も同様に
            },
            
            # 自然地名
            'nature_places': {
                '富士山': ['富士', '不二山'],
                '琵琶湖': ['琵琶の湖', '近江の海'],
                '日本海': ['日本海', '東海'],
                '太平洋': ['太平洋', '大洋'],
                # 他の自然地名も同様に
            }
        }
    
    def _build_place_type_map(self) -> Dict[str, str]:
        """地名タイプマッピング"""
        return {
            'prefectures': '都道府県',
            'major_cities': '市区町村',
            'famous_places': '有名地名',
            'nature_places': '自然地名'
        }
    
    def _build_prefecture_map(self) -> Dict[str, str]:
        """都道府県マッピング"""
        return {
            '東京都': '東京都',
            '京都府': '京都府',
            '大阪府': '大阪府',
            '北海道': '北海道',
            '沖縄県': '沖縄県',
            # 他の都道府県も同様に
        }
    
    def normalize_place(self, place_name: str) -> NormalizedPlace:
        """地名の正規化"""
        # 正規化ルールの適用
        canonical_name = place_name
        aliases = [place_name]
        place_type = '有名地名'  # デフォルト
        prefecture = None
        municipality = None
        district = None
        confidence = 0.8  # デフォルト信頼度
        
        # 各カテゴリーで正規化を試みる
        for category, rules in self.normalization_rules.items():
            for canonical, variants in rules.items():
                if place_name in variants or place_name == canonical:
                    canonical_name = canonical
                    aliases = variants + [canonical]
                    place_type = self.place_type_map.get(category, '有名地名')
                    
                    # 都道府県の特定
                    if category == 'prefectures':
                        prefecture = canonical_name
                        confidence = 0.95
                    elif category == 'major_cities':
                        # 市区町村の正規化
                        municipality = canonical_name
                        # 都道府県の推測
                        for pref, cities in self._get_city_prefecture_map().items():
                            if canonical_name in cities:
                                prefecture = pref
                                break
                        confidence = 0.90
                    elif category == 'famous_places':
                        confidence = 0.85
                    elif category == 'nature_places':
                        confidence = 0.80
                    
                    break
        
        return NormalizedPlace(
            canonical_name=canonical_name,
            aliases=aliases,
            place_type=place_type,
            prefecture=prefecture,
            municipality=municipality,
            district=district,
            confidence=confidence,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
    
    def _get_city_prefecture_map(self) -> Dict[str, List[str]]:
        """市区町村と都道府県のマッピング"""
        return {
            '東京都': ['新宿区', '渋谷区', '千代田区', '中央区', '港区'],
            '京都府': ['京都市', '宇治市', '亀岡市'],
            '大阪府': ['大阪市', '堺市', '豊中市'],
            '北海道': ['札幌市', '函館市', '小樽市'],
            '沖縄県': ['那覇市', '沖縄市', '宜野湾市'],
            # 他の都道府県も同様に
        }
    
    def get_aliases(self, place_name: str) -> List[str]:
        """地名の別名リストを取得"""
        normalized = self.normalize_place(place_name)
        return normalized.aliases
    
    def get_canonical_name(self, place_name: str) -> str:
        """地名の正規名を取得"""
        normalized = self.normalize_place(place_name)
        return normalized.canonical_name
    
    def get_place_type(self, place_name: str) -> str:
        """地名のタイプを取得"""
        normalized = self.normalize_place(place_name)
        return normalized.place_type
    
    def get_prefecture(self, place_name: str) -> Optional[str]:
        """地名の都道府県を取得"""
        normalized = self.normalize_place(place_name)
        return normalized.prefecture
    
    def test_normalization(self, test_places: List[str]) -> Dict:
        """正規化機能のテスト"""
        logger.info("🧪 地名正規化システムテスト開始")
        
        results = []
        for place in test_places:
            normalized = self.normalize_place(place)
            results.append({
                'original': place,
                'canonical': normalized.canonical_name,
                'aliases': normalized.aliases,
                'type': normalized.place_type,
                'prefecture': normalized.prefecture,
                'confidence': normalized.confidence
            })
        
        return {
            'total_places': len(results),
            'results': results,
            'success': len(results) > 0
        }

if __name__ == "__main__":
    # 簡単なテスト
    normalizer = PlaceNormalizer()
    
    test_places = [
        "東京",
        "江戸",
        "新宿",
        "新宿区",
        "銀座",
        "銀座通り",
        "富士山",
        "富士"
    ]
    
    result = normalizer.test_normalization(test_places)
    
    print("✅ 地名正規化システムv4テスト完了")
    print(f"📊 テスト地名数: {result['total_places']}")
    for place in result['results']:
        print(f"🗺️ {place['original']} → {place['canonical']} (タイプ: {place['type']}, 信頼度: {place['confidence']:.2f})")
        print(f"  別名: {', '.join(place['aliases'])}") 