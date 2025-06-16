#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高精度地名抽出システム v4 (MeCab + 強化正規表現)
v3からの移植・改良版 - 複雑地名対応
"""

import re
import logging
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# MeCabの動的インポート（オプショナル依存）
try:
    import MeCab
    MECAB_AVAILABLE = True
    logger.info("✅ MeCab利用可能")
except ImportError:
    MECAB_AVAILABLE = False
    logger.warning("⚠️ MeCab未インストール - 正規表現のみで動作")

@dataclass
class AdvancedPlace:
    """高精度地名データ"""
    work_id: int
    place_name: str
    sentence: str
    before_text: str = ""
    after_text: str = ""
    category: str = ""
    confidence: float = 0.0
    method: str = "advanced_regex"
    reading: str = ""
    pos: str = ""
    subpos: str = ""
    start_pos: int = 0
    end_pos: int = 0
    aozora_url: str = ""

class AdvancedPlaceExtractor:
    """高精度地名抽出クラス v4"""
    
    def __init__(self):
        # MeCab初期化（利用可能な場合）
        self.tagger = None
        if MECAB_AVAILABLE:
            try:
                self.tagger = MeCab.Tagger()
                logger.info("✅ MeCab初期化成功")
            except Exception as e:
                logger.warning(f"⚠️ MeCab初期化失敗: {e}")
                self.tagger = None
        
        # 地名データベース（包括的）
        self.place_patterns = self._build_place_patterns()
        
        # 除外パターン
        self.exclusions = self._build_exclusions()
        
        logger.info("🌟 高精度地名抽出システムv4初期化完了")
    
    def _build_place_patterns(self) -> Dict[str, Any]:
        """地名パターンデータベース構築"""
        return {
            # 都道府県
            'prefectures': [
                '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
                '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
                '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県',
                '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県',
                '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県',
                '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県',
                '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
            ],
            
            # 主要都市
            'major_cities': [
                '札幌', '仙台', '東京', '横浜', '名古屋', '京都', '大阪', '神戸', 
                '広島', '福岡', '那覇', '新宿', '渋谷', '池袋', '銀座', '浅草',
                '上野', '品川', '新橋', '有楽町', '秋葉原', '六本木', '赤坂'
            ],
            
            # 古典地名・文学地名
            'classical_places': [
                '江戸', '平安京', '武蔵', '相模', '甲斐', '信濃', '越後', '下野', '上野',
                '蜀川', '羅生門', '津軽', '松山', '龍宮', '蓬莱', '桃源郷'
            ],
            
            # 自然地名パターン
            'nature_patterns': [
                r'[一-龯]{1,4}川', r'[一-龯]{1,4}山', r'[一-龯]{1,4}湖', r'[一-龯]{1,4}海',
                r'[一-龯]{1,3}峠', r'[一-龯]{1,3}谷', r'[一-龯]{1,3}島', r'[一-龯]{1,3}岬'
            ]
        }
    
    def _build_exclusions(self) -> Dict[str, Set[str]]:
        """除外パターン構築"""
        return {
            '時間関連': {'日', '月', '年', '時', '分', '秒', '春', '夏', '秋', '冬'},
            '方向関連': {'上', '下', '左', '右', '前', '後', '中', '内', '外'},
            '一般名詞': {'人', '物', '事', '者', '家', '屋', '店', '場', '所'}
        }
    
    def extract_places(self, text: str) -> List[AdvancedPlace]:
        """テキストから地名を抽出（メイン機能）"""
        if not text or len(text) < 10:
            logger.warning(f"テキストが短すぎます: {len(text)}文字")
            return []
        # work_idやaozora_urlは使わず、textのみで抽出
        all_places = []
        # 正規表現抽出
        regex_places = self._extract_places_regex(0, text, "")
        all_places.extend(regex_places)
        # MeCab抽出（利用可能な場合）
        if hasattr(self, 'tagger') and self.tagger:
            mecab_places = self._extract_places_mecab(0, text, "")
            all_places.extend(mecab_places)
        # 重複除去とマージ
        unique_places = self._deduplicate_and_merge(all_places)
        logger.info(f"✅ 高精度地名抽出完了: {len(unique_places)}件")
        return unique_places
    
    def _extract_places_regex(self, work_id: int, text: str, aozora_url: str) -> List[AdvancedPlace]:
        """強化正規表現による地名抽出"""
        places = []
        
        try:
            # 明示的地名リストから抽出
            for category, place_list in self.place_patterns.items():
                if category.endswith('_patterns'):
                    # 正規表現パターン
                    for pattern in place_list:
                        matches = re.finditer(pattern, text)
                        for match in matches:
                            place_name = match.group()
                            if self._is_valid_place(place_name):
                                place = AdvancedPlace(
                                    work_id=work_id,
                                    place_name=place_name,
                                    sentence=self._get_context(text, place_name),
                                    category=category,
                                    confidence=self._calculate_regex_confidence(place_name, category),
                                    method='regex',
                                    start_pos=match.start(),
                                    end_pos=match.end(),
                                    aozora_url=aozora_url
                                )
                                places.append(place)
                else:
                    # 明示的リスト
                    for place in place_list:
                        if place in text:
                            start = text.find(place)
                            place_obj = AdvancedPlace(
                                work_id=work_id,
                                place_name=place,
                                sentence=self._get_context(text, place),
                                category=category,
                                confidence=self._calculate_regex_confidence(place, category),
                                method='regex',
                                start_pos=start,
                                end_pos=start + len(place),
                                aozora_url=aozora_url
                            )
                            places.append(place_obj)
        
        except Exception as e:
            logger.error(f"❌ 正規表現抽出エラー: {e}")
        
        return places
    
    def _extract_places_mecab(self, work_id: int, text: str, aozora_url: str) -> List[AdvancedPlace]:
        """MeCabを使った地名抽出（スタブ実装）"""
        # 実際のMeCab実装は複雑なので、基本機能のみ
        return []
    
    def _is_valid_place(self, place_name: str) -> bool:
        """地名の妥当性チェック"""
        if not place_name or len(place_name.strip()) <= 1:
            return False
        
        # 除外パターンチェック
        for category, exclusions in self.exclusions.items():
            if place_name in exclusions:
                return False
        
        return True
    
    def _calculate_regex_confidence(self, place_name: str, category: str) -> float:
        """正規表現地名の信頼度計算"""
        confidence_map = {
            'prefectures': 0.95,
            'major_cities': 0.90,
            'classical_places': 0.85,
            'nature_patterns': 0.75
        }
        return confidence_map.get(category, 0.65)
    
    def _get_context(self, text: str, place_name: str, context_len: int = 50) -> str:
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
    
    def _deduplicate_and_merge(self, places: List[AdvancedPlace]) -> List[AdvancedPlace]:
        """重複除去とマージ"""
        seen = set()
        unique_places = []
        
        # 信頼度順でソート
        places.sort(key=lambda x: x.confidence, reverse=True)
        
        for place in places:
            # 地名と作品IDの組み合わせで重複チェック
            key = (place.work_id, place.place_name)
            if key not in seen:
                seen.add(key)
                unique_places.append(place)
        
        return unique_places
    
    def test_extraction(self, test_text: str) -> Dict[str, Any]:
        """抽出機能のテスト"""
        logger.info("🧪 Advanced Place Extractor テスト開始")
        
        places = self.extract_places(test_text)
        
        # 統計作成
        methods = {}
        categories = {}
        for place in places:
            methods[place.method] = methods.get(place.method, 0) + 1
            categories[place.category] = categories.get(place.category, 0) + 1
        
        return {
            'test_text_length': len(test_text),
            'total_places': len(places),
            'mecab_available': MECAB_AVAILABLE,
            'places': [
                {
                    'name': place.place_name,
                    'category': place.category,
                    'confidence': place.confidence,
                    'method': place.method
                }
                for place in places[:10]  # 最初の10件のみ
            ],
            'stats': {
                'methods': methods,
                'categories': categories
            },
            'success': len(places) > 0
        }

if __name__ == "__main__":
    # 包括的テスト
    extractor = AdvancedPlaceExtractor()
    
    test_text = """
    私は東京都新宿区に住んでいます。
    鎌倉の大仏を見に行きました。
    津軽海峡を渡って北海道に向かいました。
    京都府京都市を経由して奈良県奈良市に到着しました。
    富士山の山頂から見た景色は素晴らしかった。
    江戸時代の武蔵国から相模国への旅路は困難でした。
    """
    
    result = extractor.test_extraction(test_text)
    
    print("✅ Advanced Place Extractor v4 テスト完了")
    print(f"📊 抽出地名数: {result['total_places']}")
    print(f"🔧 MeCab利用可能: {result['mecab_available']}")
    
    for place in result['places']:
        print(f"🗺️ {place['name']} [{place['category']}] "
              f"({place['method']}, 信頼度: {place['confidence']:.2f})")
    
    print(f"\n📈 抽出手法別統計: {result['stats']['methods']}")
    print(f"📋 カテゴリー別統計: {result['stats']['categories']}") 