#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌟 高精度地名抽出システム (MeCab + 強化正規表現)
"""

import re
import MeCab
from typing import List, Dict, Set

class AdvancedPlaceExtractor:
    """高精度地名抽出クラス"""
    
    def __init__(self):
        self.tagger = MeCab.Tagger()
        
        # 地名データベース（包括的）
        self.place_patterns = {
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
                '蜀川', '阿修羅', '帝釈天', '須弥山', '兜率天', '忉利天', '極楽', '浄土',
                '龍宮', '蓬莱', '桃源郷', '天竺', '震旦', '羅生門'
            ],
            
            # 外国地名
            'foreign_places': [
                'ロンドン', 'パリ', 'ベルリン', 'ニューヨーク', 'シカゴ', 'ボストン',
                '中国', '朝鮮', '満州', '台湾', '樺太', 'シベリア', 'ヨーロッパ', 'アメリカ',
                '朝鮮', '高麗', '百済', '新羅'
            ],
            
            # 自然地名パターン
            'nature_patterns': [
                r'[一-龯]{1,4}川', r'[一-龯]{1,4}山', r'[一-龯]{1,4}湖', r'[一-龯]{1,4}海',
                r'[一-龯]{1,3}峠', r'[一-龯]{1,3}谷', r'[一-龯]{1,3}野', r'[一-龯]{1,3}原',
                r'[一-龯]{1,3}島', r'[一-龯]{1,3}岬', r'[一-龯]{1,3}浦', r'[一-龯]{1,3}崎'
            ],
            
            # 建造物・施設
            'facility_patterns': [
                r'[一-龯]{1,4}寺', r'[一-龯]{1,4}神社', r'[一-龯]{1,3}院', r'[一-龯]{1,3}宮',
                r'[一-龯]{1,3}城', r'[一-龯]{1,3}宿', r'[一-龯]{1,3}駅', r'[一-龯]{1,3}港'
            ]
        }
        
        # 除外パターン
        self.exclusions = {
            '時間関連': {'日', '月', '年', '時', '分', '秒', '春', '夏', '秋', '冬'},
            '方向関連': {'上', '下', '左', '右', '前', '後', '中', '内', '外'},
            '大小関連': {'大', '小', '高', '低', '長', '短'},
            '一般名詞': {'人', '物', '事', '者', '家', '屋', '店', '場', '所'}
        }

    def extract_places_mecab(self, text: str) -> List[Dict]:
        """MeCabを使った地名抽出"""
        places = []
        
        try:
            node = self.tagger.parseToNode(text)
            
            while node:
                if node.surface and len(node.surface) >= 2:
                    features = node.feature.split(',')
                    
                    # 名詞・固有名詞・地名をチェック
                    if len(features) > 6:
                        pos = features[0]  # 品詞
                        subpos = features[1] if len(features) > 1 else ''  # 細分類
                        reading = features[7] if len(features) > 7 else ''  # 読み
                        
                        if (pos == '名詞' and 
                            ('固有' in subpos or '地域' in subpos or '一般' in subpos)):
                            
                            place_info = {
                                'text': node.surface,
                                'reading': reading,
                                'pos': pos,
                                'subpos': subpos,
                                'method': 'mecab',
                                'confidence': self._calculate_mecab_confidence(node.surface, subpos)
                            }
                            places.append(place_info)
                
                node = node.next
                
        except Exception as e:
            print(f"❌ MeCab解析エラー: {e}")
        
        return places

    def extract_places_regex(self, text: str) -> List[Dict]:
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
                                places.append({
                                    'text': place_name,
                                    'category': category,
                                    'method': 'regex',
                                    'start': match.start(),
                                    'end': match.end(),
                                    'confidence': self._calculate_regex_confidence(place_name, category)
                                })
                else:
                    # 明示的リスト
                    for place in place_list:
                        if place in text:
                            start = text.find(place)
                            places.append({
                                'text': place,
                                'category': category,
                                'method': 'regex',
                                'start': start,
                                'end': start + len(place),
                                'confidence': self._calculate_regex_confidence(place, category)
                            })
        
        except Exception as e:
            print(f"❌ 正規表現抽出エラー: {e}")
        
        return places

    def extract_places_combined(self, text: str, work_info: Dict = None) -> List[Dict]:
        """MeCab + 正規表現の統合抽出"""
        mecab_places = self.extract_places_mecab(text)
        regex_places = self.extract_places_regex(text)
        
        # 結果をマージして重複除去
        all_places = []
        seen_places = set()
        
        # MeCab結果を追加
        for place in mecab_places:
            key = place['text']
            if key not in seen_places and self._is_valid_place(key):
                place.update({
                    'author_name': work_info.get('author_name', '') if work_info else '',
                    'work_title': work_info.get('title', '') if work_info else '',
                    'context': self._get_context(text, place['text'])
                })
                all_places.append(place)
                seen_places.add(key)
        
        # 正規表現結果を追加
        for place in regex_places:
            key = place['text']
            if key not in seen_places and self._is_valid_place(key):
                place.update({
                    'author_name': work_info.get('author_name', '') if work_info else '',
                    'work_title': work_info.get('title', '') if work_info else ''
                })
                all_places.append(place)
                seen_places.add(key)
        
        # 信頼度順でソート
        all_places.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return all_places

    def _is_valid_place(self, place_name: str) -> bool:
        """地名の妥当性チェック"""
        if not place_name or len(place_name.strip()) == 0:
            return False
        
        # 除外パターンチェック
        for category, exclusions in self.exclusions.items():
            if place_name in exclusions:
                return False
        
        # 数字のみは除外
        if place_name.isdigit():
            return False
        
        # 一文字は特定のもののみ許可
        if len(place_name) == 1:
            allowed_single = {'京', '江', '海', '山', '川', '島'}
            return place_name in allowed_single
        
        return True

    def _calculate_mecab_confidence(self, place_name: str, subpos: str) -> float:
        """MeCab結果の信頼度計算"""
        confidence = 0.7  # ベース信頼度
        
        if '固有' in subpos:
            confidence += 0.2
        if '地域' in subpos:
            confidence += 0.15
        if len(place_name) >= 3:
            confidence += 0.1
        
        return min(confidence, 1.0)

    def _calculate_regex_confidence(self, place_name: str, category: str) -> float:
        """正規表現結果の信頼度計算"""
        confidence = 0.6  # ベース信頼度
        
        confidence_boost = {
            'prefectures': 0.3,
            'major_cities': 0.25,
            'classical_places': 0.2,
            'foreign_places': 0.15,
            'nature_patterns': 0.1,
            'facility_patterns': 0.1
        }
        
        confidence += confidence_boost.get(category, 0)
        
        # 特別な地名のブースト
        special_places = {'蜀川', '阿修羅', '帝釈天', '江戸', '平安京'}
        if place_name in special_places:
            confidence += 0.15
        
        return min(confidence, 1.0)

    def _get_context(self, text: str, place_name: str, context_len: int = 50) -> str:
        """地名の文脈を取得"""
        start = text.find(place_name)
        if start == -1:
            return ""
        
        context_start = max(0, start - context_len)
        context_end = min(len(text), start + len(place_name) + context_len)
        
        return text[context_start:context_end]

def test_advanced_extractor():
    """高精度地名抽出のテスト"""
    extractor = AdvancedPlaceExtractor()
    
    # テストテキスト（青空文庫風）
    test_text = """
    東京で夏目漱石は生まれました。京都にも住んでいました。
    蜀川や阿修羅、帝釈天という言葉も出てきます。
    江戸時代の平安京では、多くの作家が隅田川のほとりで執筆していました。
    ロンドンやパリといった外国の都市についても言及されています。
    """
    
    print("🌟 高精度地名抽出テスト開始")
    print(f"📖 テストテキスト ({len(test_text)}文字)")
    
    # MeCab抽出
    mecab_places = extractor.extract_places_mecab(test_text)
    print(f"\n🔧 MeCab抽出: {len(mecab_places)}件")
    for place in mecab_places[:5]:
        print(f"  - {place['text']} (信頼度: {place['confidence']:.2f})")
    
    # 正規表現抽出
    regex_places = extractor.extract_places_regex(test_text)
    print(f"\n📝 正規表現抽出: {len(regex_places)}件")
    for place in regex_places[:5]:
        print(f"  - {place['text']} (信頼度: {place['confidence']:.2f})")
    
    # 統合抽出
    combined_places = extractor.extract_places_combined(test_text)
    print(f"\n🎯 統合抽出: {len(combined_places)}件")
    for place in combined_places:
        print(f"  - {place['text']} (信頼度: {place['confidence']:.2f}, 手法: {place['method']})")

if __name__ == "__main__":
    test_advanced_extractor() 