#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
軽量地名抽出器 (正規表現ベース)
GiNZAが利用できない環境でも動作する地名抽出機能
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from ..database.models import PlaceMaster as Place
from ..utils.aozora_text_cleaner import clean_aozora_sentence


class SimplePlaceExtractor:
    """正規表現ベースの軽量地名抽出器"""
    
    def __init__(self):
        self.place_patterns = self._build_place_patterns()
        print("✅ 軽量地名抽出器 初期化完了")
    
    def _build_place_patterns(self) -> List[Dict]:
        """地名抽出用のパターンを構築"""
        return [
            # 都道府県（境界条件強化版）
            {
                'pattern': r'(?<![一-龯])[北海青森岩手宮城秋田山形福島茨城栃木群馬埼玉千葉東京神奈川新潟富山石川福井山梨長野岐阜静岡愛知三重滋賀京都大阪兵庫奈良和歌山鳥取島根岡山広島山口徳島香川愛媛高知福岡佐賀長崎熊本大分宮崎鹿児島沖縄][都道府県](?![一-龯])',
                'category': '都道府県',
                'confidence': 0.9
            },
            # 市区町村（境界条件強化版）
            {
                'pattern': r'(?<![一-龯])[一-龯]{2,6}[市区町村](?![一-龯])',
                'category': '市区町村',
                'confidence': 0.8
            },
            # 郡（境界条件強化版）
            {
                'pattern': r'(?<![一-龯])[一-龯]{2,4}[郡](?![一-龯])',
                'category': '郡',
                'confidence': 0.7
            },
            # 有名な地名・駅名・観光地
            {
                'pattern': r'(?:' + '|'.join([
                    # 東京エリア
                    '銀座', '新宿', '渋谷', '上野', '浅草', '品川', '池袋', '新橋', '有楽町', '丸の内',
                    '表参道', '原宿', '恵比寿', '六本木', '赤坂', '青山', '麻布', '目黒', '世田谷',
                    '江戸', '本郷', '神田', '日本橋', '築地', '月島', '両国', '浅草橋', '秋葉原',
                    
                    # 関東エリア
                    '横浜', '川崎', '千葉', '埼玉', '大宮', '浦和', '船橋', '柏', '所沢', '川越',
                    '鎌倉', '湘南', '箱根', '熱海', '軽井沢', '日光', '那須', '草津', '伊香保',
                    
                    # 関西エリア
                    '京都', '大阪', '神戸', '奈良', '和歌山', '滋賀', '比叡山', '嵐山', '祇園',
                    '清水', '金閣寺', '銀閣寺', '伏見', '宇治', '平安京', '難波', '梅田', '心斎橋',
                    
                    # 中部エリア
                    '名古屋', '金沢', '富山', '新潟', '長野', '松本', '諏訪', '上高地', '立山',
                    
                    # 東北エリア
                    '仙台', '青森', '盛岡', '秋田', '山形', '福島', '会津', '松島',
                    
                    # 北海道
                    '札幌', '函館', '小樽', '旭川', '釧路', '帯広', '北見',
                    
                    # 中国・四国
                    '広島', '岡山', '山口', '鳥取', '島根', '高松', '松山', '高知', '徳島',
                    
                    # 九州・沖縄
                    '福岡', '博多', '北九州', '佐賀', '長崎', '熊本', '大分', '宮崎', '鹿児島', '沖縄', '那覇',
                    
                    # 古典的・文学的地名
                    '平安京', '江戸', '駿河', '甲斐', '信濃', '越後', '陸奥', '出羽', '薩摩', '土佐',
                    '伊豆', '伊勢', '山城', '大和', '河内', '和泉', '摂津', '近江', '美濃', '尾張',
                    
                    # 海外地名（文学作品によく出る）
                    'パリ', 'ロンドン', 'ベルリン', 'ローマ', 'ウィーン', 'モスクワ', 'ペテルブルク',
                    'ニューヨーク', 'シカゴ', 'サンフランシスコ', 'ロサンゼルス',
                    '上海', '北京', '香港', 'ソウル', 'バンコク', 'マニラ',
                    
                    # 地理的特徴
                    '富士山', '阿蘇山', '霧島', '筑波山', '比叡山', '高野山',
                    '琵琶湖', '中禅寺湖', '芦ノ湖', '十和田湖',
                    '瀬戸内海', '日本海', '太平洋', '東京湾', '大阪湾', '駿河湾',
                    '利根川', '信濃川', '石狩川', '筑後川', '吉野川'
                ]) + r')',
                'category': '有名地名',
                'confidence': 0.85
            }
        ]
    
    def extract_places_from_text(self, work_id: int, text: str, aozora_url: str = None) -> List[Place]:
        """テキストから地名を抽出"""
        if not text:
            return []
        
        places = []
        
        # 文に分割
        sentences = re.split(r'[。！？]', text)
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 10:  # 短すぎる文はスキップ
                continue
            
            # 青空文庫テキストのクリーニング
            clean_sentence = clean_aozora_sentence(sentence)
            if len(clean_sentence) < 10:  # クリーニング後も短い場合はスキップ
                continue
            
            # 各パターンを適用
            for pattern_info in self.place_patterns:
                pattern = pattern_info['pattern']
                category = pattern_info['category']
                confidence = pattern_info['confidence']
                
                # クリーンアップされた文で検索
                matches = re.finditer(pattern, clean_sentence)
                for match in matches:
                    place_name = match.group()
                    
                    # 前後のコンテキストを取得（元の文から）
                    before_text, after_text = self._get_context(sentence, place_name)
                    
                    # 文脈による信頼度調整
                    adjusted_confidence = self._adjust_confidence(place_name, clean_sentence, confidence)
                    
                    place = Place(
                        work_id=work_id,
                        place_name=place_name,
                        before_text=before_text,
                        sentence=clean_sentence,  # クリーンアップされた文を保存
                        after_text=after_text,
                        aozora_url=aozora_url,
                        confidence=adjusted_confidence,
                        extraction_method=f'regex_{category}'
                    )
                    places.append(place)
        
        # 重複除去
        return self._deduplicate_places(places)
    
    def _get_context(self, sentence: str, place_name: str, context_length: int = 20) -> Tuple[str, str]:
        """地名の前後のコンテキストを取得"""
        try:
            start_idx = sentence.find(place_name)
            if start_idx == -1:
                return "", ""
            
            before_start = max(0, start_idx - context_length)
            after_end = min(len(sentence), start_idx + len(place_name) + context_length)
            
            before_text = sentence[before_start:start_idx].strip()
            after_text = sentence[start_idx + len(place_name):after_end].strip()
            
            return before_text, after_text
        except Exception:
            return "", ""
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """テキストを文に分割"""
        # 句読点で分割
        sentences = re.split(r'[。！？]', text)
        
        # 空文字列を除去し、前後の空白をトリム
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _adjust_confidence(self, place_name: str, sentence: str, base_confidence: float) -> float:
        """文脈に基づいて信頼度を調整"""
        confidence = base_confidence
        
        # 地名らしい文脈かチェック
        location_contexts = [
            r'[から|より|への|へと|にて|にいる|にある|を通り|を経て]',
            r'[行く|来る|向かう|着く|発つ|出発|到着]',
            r'[住む|滞在|訪問|旅行|見物]'
        ]
        
        for context_pattern in location_contexts:
            if re.search(context_pattern, sentence):
                confidence += 0.1
                break
        
        # 人名と混同しやすい場合は信頼度を下げる
        person_contexts = [
            r'[さん|君|氏|先生|様]',
            r'[は|が][話す|言う|思う|考える]'
        ]
        
        for person_pattern in person_contexts:
            if re.search(person_pattern, sentence):
                confidence -= 0.2
                break
        
        # 長さによる調整（短すぎる地名は信頼度を下げる）
        if len(place_name) == 1:
            confidence -= 0.3
        elif len(place_name) == 2:
            confidence -= 0.1
        
        return max(0.1, min(confidence, 1.0))
    
    def _deduplicate_places(self, places: List[Place]) -> List[Place]:
        """重複する地名を除去（包含関係を考慮した高度な重複排除）"""
        if not places:
            return []
        
        # 優先度定義（extraction_method別）
        method_priority = {
            'regex_市区町村': 1,      # 完全地名が最高優先度
            'regex_都道府県': 2,
            'regex_郡': 3,
            'regex_有名地名': 4        # 有名地名は最低優先度
        }
        
        # 作品別にグループ化
        by_work = {}
        for place in places:
            if place.work_id not in by_work:
                by_work[place.work_id] = []
            by_work[place.work_id].append(place)
        
        deduplicated = []
        
        for work_id, work_places in by_work.items():
            # 同じsentence内での重複排除
            by_sentence = {}
            for place in work_places:
                sentence_key = place.sentence if place.sentence else ""
                if sentence_key not in by_sentence:
                    by_sentence[sentence_key] = []
                by_sentence[sentence_key].append(place)
            
            for sentence, sentence_places in by_sentence.items():
                if len(sentence_places) == 1:
                    deduplicated.extend(sentence_places)
                    continue
                
                # 包含関係をチェック
                filtered_places = []
                sentence_places_sorted = sorted(
                    sentence_places, 
                    key=lambda p: (
                        method_priority.get(p.extraction_method, 5),
                        -len(p.place_name),  # 長い地名を優先
                        -p.confidence
                    )
                )
                
                for current_place in sentence_places_sorted:
                    is_contained = False
                    
                    # 既に選択された地名に含まれるかチェック
                    for selected_place in filtered_places:
                        if (current_place.place_name in selected_place.place_name and 
                            current_place.place_name != selected_place.place_name):
                            is_contained = True
                            break
                    
                    if not is_contained:
                        # 現在の地名が既存の地名を包含するかチェック
                        to_remove = []
                        for i, selected_place in enumerate(filtered_places):
                            if (selected_place.place_name in current_place.place_name and
                                selected_place.place_name != current_place.place_name):
                                to_remove.append(i)
                        
                        # 包含される地名を除去
                        for i in reversed(to_remove):
                            filtered_places.pop(i)
                        
                        filtered_places.append(current_place)
                
                deduplicated.extend(filtered_places)
        
        return deduplicated
    
    def extract_places_with_context(self, text: str, work_id: int, aozora_url: str) -> List[Place]:
        """既存のGiNZA抽出器と互換性のあるインターフェース"""
        return self.extract_places_from_text(work_id, text, aozora_url)
    
    def test_extraction(self, test_text: str = None) -> Dict:
        """抽出機能のテスト"""
        if not test_text:
            test_text = """
            親譲りの無鉄砲で小供の時から損ばかりしている。東京の学校を卒業してから、
            四国の松山に赴任した。瀬戸内海の風景は美しく、道後温泉も有名である。
            京都の金閣寺や奈良の東大寺も見てみたい。鎌倉の大仏も素晴らしいらしい。
            """
        
        places = self.extract_places_from_text(work_id=999, text=test_text)
        
        result = {
            'test_text': test_text[:100] + "..." if len(test_text) > 100 else test_text,
            'places_found': len(places),
            'places': [
                {
                    'name': place.place_name,
                    'confidence': place.confidence,
                    'method': place.extraction_method,
                    'sentence': place.sentence[:50] + "..." if len(place.sentence) > 50 else place.sentence
                }
                for place in places
            ],
            'success': len(places) > 0
        }
        
        return result 