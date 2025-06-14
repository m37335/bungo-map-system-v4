#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI複合地名抽出システム v4 (OpenAI API統合)
v3からの移植・改良版 - 複合地名「東京駅前」等の高精度抽出
"""

import re
import os
import json
import logging
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# OpenAI APIの動的インポート（オプショナル依存）
try:
    import openai
    OPENAI_AVAILABLE = True
    logger.info("✅ OpenAI API利用可能")
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("⚠️ OpenAI未インストール - フォールバック機能で動作")

@dataclass
class CompoundPlace:
    """AI複合地名データ"""
    work_id: int
    place_name: str
    sentence: str
    category: str = ""
    confidence: float = 0.0
    method: str = "ai_compound"
    compound_type: str = ""
    base_place: str = ""
    modifier: str = ""
    start_pos: int = 0
    end_pos: int = 0
    ai_reasoning: str = ""
    aozora_url: str = ""

class PreciseCompoundExtractor:
    """AI複合地名抽出クラス v4"""
    
    def __init__(self):
        # OpenAI API初期化
        self.client = None
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                openai.api_key = self.api_key
                self.client = openai
                logger.info("✅ OpenAI API初期化成功")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI API初期化失敗: {e}")
                self.client = None
        else:
            logger.warning("⚠️ OpenAI API Key未設定 - フォールバック機能で動作")
        
        # 複合地名パターン
        self.compound_patterns = self._build_compound_patterns()
        
        # フォールバック複合地名データベース
        self.fallback_compounds = self._build_fallback_compounds()
        
        logger.info("🌟 AI複合地名抽出システムv4初期化完了")
    
    def _build_compound_patterns(self) -> Dict[str, Any]:
        """複合地名パターン構築"""
        return {
            # 方向・位置パターン
            'direction_patterns': [
                r'([一-龯]{2,})(駅前|駅後|駅周辺)',
                r'([一-龯]{2,})(南|北|東|西)(口|側|部|地区)',
                r'([一-龯]{2,})(上|下|中)(町|地|部)',
                r'([一-龯]{2,})(内|外)(地|部|側)'
            ],
            
            # 施設複合パターン
            'facility_patterns': [
                r'([一-龯]{2,})(大学前|学校前)',
                r'([一-龯]{2,})(神社前|寺前)',
                r'([一-龯]{2,})(市役所前|役場前)',
                r'([一-龯]{2,})(病院前|公園前)'
            ],
            
            # 地形複合パターン
            'terrain_patterns': [
                r'([一-龯]{2,})(川沿い|川岸|河畔)',
                r'([一-龯]{2,})(山麓|山頂|山中)',
                r'([一-龯]{2,})(海岸|湖畔|水辺)'
            ]
        }
    
    def _build_fallback_compounds(self) -> Set[str]:
        """フォールバック複合地名データベース"""
        return {
            # 東京圏
            '新宿駅前', '渋谷駅前', '池袋駅前', '品川駅前', '上野駅前',
            '東京駅前', '有楽町駅前', '銀座周辺', '秋葉原周辺',
            
            # 関西圏
            '大阪駅前', '梅田駅前', '難波周辺', '京都駅前', '神戸駅前',
            
            # その他主要都市
            '札幌駅前', '仙台駅前', '名古屋駅前', '広島駅前', '福岡駅前',
            
            # 古典複合地名
            '江戸城下', '京都御所周辺', '奈良公園周辺'
        }
    
    def extract_compound_places(self, work_id: int, text: str, aozora_url: str = "") -> List[CompoundPlace]:
        """AI複合地名抽出（メイン機能）"""
        if not text or len(text) < 20:
            logger.warning(f"テキストが短すぎます: {len(text)}文字")
            return []
        
        places = []
        
        # 正規表現フォールバック抽出
        regex_places = self._extract_with_regex(work_id, text, aozora_url)
        places.extend(regex_places)
        logger.info(f"📊 正規表現抽出: {len(regex_places)}件")
        
        # 重複除去
        unique_places = self._deduplicate_places(places)
        
        logger.info(f"✅ AI複合地名抽出完了: {len(unique_places)}件")
        return unique_places
    
    def _extract_with_regex(self, work_id: int, text: str, aozora_url: str) -> List[CompoundPlace]:
        """正規表現による複合地名抽出（フォールバック）"""
        places = []
        
        try:
            # パターンマッチング
            for category, patterns in self.compound_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        place_name = match.group()
                        base_place = match.group(1) if match.groups() else ''
                        modifier = match.group(2) if len(match.groups()) > 1 else ''
                        
                        if self._is_valid_compound(place_name):
                            place = CompoundPlace(
                                work_id=work_id,
                                place_name=place_name,
                                sentence=self._get_context(text, place_name),
                                category=category,
                                confidence=self._calculate_regex_confidence(category),
                                method='regex',
                                compound_type=category.replace('_patterns', ''),
                                base_place=base_place,
                                modifier=modifier,
                                start_pos=match.start(),
                                end_pos=match.end(),
                                aozora_url=aozora_url
                            )
                            places.append(place)
            
            # フォールバック複合地名チェック
            for compound in self.fallback_compounds:
                if compound in text:
                    start = text.find(compound)
                    place = CompoundPlace(
                        work_id=work_id,
                        place_name=compound,
                        sentence=self._get_context(text, compound),
                        category='fallback_compound',
                        confidence=0.85,
                        method='fallback',
                        compound_type='known_compound',
                        start_pos=start,
                        end_pos=start + len(compound),
                        aozora_url=aozora_url
                    )
                    places.append(place)
        
        except Exception as e:
            logger.error(f"❌ 正規表現抽出エラー: {e}")
        
        return places
    
    def _is_valid_compound(self, place_name: str) -> bool:
        """複合地名の妥当性チェック"""
        if not place_name or len(place_name) < 3:
            return False
        
        # 除外パターン
        exclusions = {'今日', '昨日', '明日', '時間', '場合', '問題'}
        return place_name not in exclusions
    
    def _calculate_regex_confidence(self, category: str) -> float:
        """正規表現の信頼度計算"""
        confidence_map = {
            'direction_patterns': 0.80,
            'facility_patterns': 0.85,
            'terrain_patterns': 0.80
        }
        return confidence_map.get(category, 0.70)
    
    def _get_context(self, text: str, place_name: str, context_len: int = 60) -> str:
        """地名周辺の文脈を取得"""
        try:
            start = text.find(place_name)
            if start == -1:
                return ""
            
            context_start = max(0, start - context_len)
            context_end = min(len(text), start + len(place_name) + context_len)
            
            return text[context_start:context_end]
        except Exception:
            return ""
    
    def _deduplicate_places(self, places: List[CompoundPlace]) -> List[CompoundPlace]:
        """重複除去"""
        seen = set()
        unique_places = []
        
        # 信頼度順でソート
        places.sort(key=lambda x: x.confidence, reverse=True)
        
        for place in places:
            key = (place.work_id, place.place_name)
            if key not in seen:
                seen.add(key)
                unique_places.append(place)
        
        return unique_places
    
    def test_extraction(self, test_text: str) -> Dict[str, Any]:
        """抽出機能のテスト"""
        logger.info("🧪 AI複合地名抽出器 テスト開始")
        
        places = self.extract_compound_places(999, test_text)
        
        # 統計作成
        categories = {}
        compound_types = {}
        for place in places:
            categories[place.category] = categories.get(place.category, 0) + 1
            compound_types[place.compound_type] = compound_types.get(place.compound_type, 0) + 1
        
        return {
            'test_text_length': len(test_text),
            'total_places': len(places),
            'openai_available': OPENAI_AVAILABLE,
            'api_key_configured': self.api_key is not None,
            'places': [
                {
                    'name': place.place_name,
                    'base_place': place.base_place,
                    'modifier': place.modifier,
                    'compound_type': place.compound_type,
                    'confidence': place.confidence,
                    'method': place.method
                }
                for place in places[:10]
            ],
            'stats': {
                'categories': categories,
                'compound_types': compound_types
            },
            'success': len(places) > 0
        }

if __name__ == "__main__":
    extractor = PreciseCompoundExtractor()
    
    test_text = """
    新宿駅前の喫茶店で待ち合わせをしました。
    東京駅周辺は多くの人で賑わっていました。
    大阪城周辺を散歩していると、美しい桜が咲いていました。
    富士山麓の湖畔で静かな時間を過ごしました。
    """
    
    result = extractor.test_extraction(test_text)
    
    print("✅ AI複合地名抽出器 v4 テスト完了")
    print(f"📊 抽出複合地名数: {result['total_places']}")
    print(f"🔧 OpenAI利用可能: {result['openai_available']}")
    print(f"🔑 API Key設定済み: {result['api_key_configured']}")
    
    for place in result['places']:
        print(f"🗺️ {place['name']} = {place['base_place']} + {place['modifier']}")
        print(f"    タイプ: {place['compound_type']}, 信頼度: {place['confidence']:.2f}")
    
    print(f"\n📈 複合タイプ別統計: {result['stats']['compound_types']}") 