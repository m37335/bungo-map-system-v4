#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
強化版地名抽出器 v4
v3からの移植・改良版 - 正規表現強化システム
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EnhancedPlace:
    """強化版地名データ"""
    work_id: int
    place_name: str
    sentence: str
    before_text: str = ""
    after_text: str = ""
    sentence_index: int = 0
    char_position: int = 0
    confidence: float = 0.0
    extraction_method: str = "enhanced_regex"
    aozora_url: str = ""

class EnhancedPlaceExtractor:
    """強化版地名抽出器 v4 - 正規表現パターン強化"""
    
    def __init__(self):
        self.patterns = self._build_enhanced_patterns()
        logger.info("🗺️ 強化版地名抽出器v4初期化完了")
    
    def _build_enhanced_patterns(self) -> List[Dict]:
        """強化された地名抽出パターン"""
        return [
            # 1. 都道府県（境界条件強化）
            {
                'pattern': r'(?<![一-龯])[北海青森岩手宮城秋田山形福島茨城栃木群馬埼玉千葉東京神奈川新潟富山石川福井山梨長野岐阜静岡愛知三重滋賀京都大阪兵庫奈良和歌山鳥取島根岡山広島山口徳島香川愛媛高知福岡佐賀長崎熊本大分宮崎鹿児島沖縄][都道府県](?![一-龯])',
                'category': '都道府県',
                'confidence': 0.95,
                'priority': 1
            },
            
            # 2. 完全地名（都道府県+市区町村） - 最高優先度
            {
                'pattern': r'(?<![一-龯])[北海青森岩手宮城秋田山形福島茨城栃木群馬埼玉千葉東京神奈川新潟富山石川福井山梨長野岐阜静岡愛知三重滋賀京都大阪兵庫奈良和歌山鳥取島根岡山広島山口徳島香川愛媛高知福岡佐賀長崎熊本大分宮崎鹿児島沖縄][都道府県][一-龯]{2,8}[市区町村](?![一-龯])',
                'category': '完全地名',
                'confidence': 0.98,
                'priority': 0
            },
            
            # 3. 市区町村（境界条件強化）
            {
                'pattern': r'(?<![一-龯])[一-龯]{2,6}[市区町村](?![一-龯])',
                'category': '市区町村',
                'confidence': 0.85,
                'priority': 2
            },
            
            # 4. 有名地名（明示リスト）
            {
                'pattern': r'(?:' + '|'.join([
                    '銀座', '新宿', '渋谷', '上野', '浅草', '品川', '池袋', '新橋', '有楽町',
                    '横浜', '川崎', '千葉', '船橋', '柏', '鎌倉', '湘南', '箱根',
                    '京都', '大阪', '神戸', '奈良', '江戸', '本郷', '神田', '日本橋',
                    '津軽', '松山', '四国', '九州', '本州', '北海道'
                ]) + r')',
                'category': '有名地名',
                'confidence': 0.90,
                'priority': 3
            },
            
            # 5. 自然地名パターン
            {
                'pattern': r'(?<![一-龯])[一-龯]{1,4}[川山湖海峠谷野原島岬浦崎](?![一-龯])',
                'category': '自然地名',
                'confidence': 0.80,
                'priority': 4
            }
        ]
    
    def extract_places(self, text: str) -> List[EnhancedPlace]:
        """テキストから地名を抽出（メイン機能）"""
        if not text or len(text) < 10:
            logger.warning(f"テキストが短すぎます: {len(text)}文字")
            return []
        all_matches = []
        sentences = self._split_into_sentences(text)
        logger.info(f"📄 文数: {len(sentences)}, 文字数: {len(text)}")
        for sentence_idx, sentence in enumerate(sentences):
            sentence_matches = self._extract_from_sentence(
                sentence, sentence_idx, sentences
            )
            # 重複排除処理
            deduplicated_matches = self._deduplicate_overlapping_matches(sentence_matches)
            all_matches.extend(deduplicated_matches)
        # EnhancedPlaceオブジェクトに変換
        places = []
        for match in all_matches:
            place = EnhancedPlace(
                work_id=0,  # work_idは使わない
                place_name=match['text'],
                sentence=match['sentence'],
                before_text=match['before_text'][:300],
                after_text=match['after_text'][:300],
                sentence_index=match.get('sentence_index', 0),
                char_position=match.get('start', 0),
                confidence=match['confidence'],
                extraction_method=f"enhanced_{match['category']}",
                aozora_url=""
            )
            places.append(place)
        logger.info(f"✅ 地名抽出完了: {len(places)}件")
        return places
    
    def _extract_from_sentence(self, sentence: str, sentence_idx: int, sentences: List[str]) -> List[Dict]:
        """単一文からの地名抽出"""
        matches = []
        
        for pattern_info in self.patterns:
            pattern_matches = list(re.finditer(pattern_info['pattern'], sentence))
            
            for match in pattern_matches:
                place_name = match.group(0)
                
                # 前後の文脈取得
                before_text = sentences[sentence_idx - 1] if sentence_idx > 0 else ""
                after_text = sentences[sentence_idx + 1] if sentence_idx < len(sentences) - 1 else ""
                
                matches.append({
                    'text': place_name,
                    'start': match.start(),
                    'end': match.end(),
                    'sentence': sentence,
                    'before_text': before_text,
                    'after_text': after_text,
                    'sentence_index': sentence_idx,
                    'category': pattern_info['category'],
                    'confidence': pattern_info['confidence'],
                    'priority': pattern_info['priority']
                })
        
        return matches
    
    def _deduplicate_overlapping_matches(self, matches: List[Dict]) -> List[Dict]:
        """重複する地名の排除"""
        if not matches:
            return []
        
        # 優先度順でソート（priority 0が最高優先度）
        matches.sort(key=lambda x: (x['priority'], -x['confidence'], -len(x['text'])))
        
        deduplicated = []
        used_ranges = []
        
        for match in matches:
            match_range = (match['start'], match['end'])
            
            # 既に使用された範囲と重複するかチェック
            is_overlapping = any(
                self._ranges_overlap(match_range, used_range) 
                for used_range in used_ranges
            )
            
            if not is_overlapping:
                deduplicated.append(match)
                used_ranges.append(match_range)
        
        return deduplicated
    
    def _ranges_overlap(self, range1: Tuple[int, int], range2: Tuple[int, int]) -> bool:
        """2つの範囲が重複するかチェック"""
        start1, end1 = range1
        start2, end2 = range2
        return not (end1 <= start2 or end2 <= start1)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """テキストを文に分割"""
        sentences = re.split(r'[。！？]', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def test_extraction(self, test_text: str) -> Dict:
        """抽出機能のテスト"""
        logger.info("🧪 Enhanced Place Extractor テスト開始")
        
        places = self.extract_places(test_text)
        
        # 統計作成
        categories = {}
        for place in places:
            method = place.extraction_method
            categories[method] = categories.get(method, 0) + 1
        
        return {
            'test_text_length': len(test_text),
            'total_places': len(places),
            'places': [
                {
                    'name': place.place_name,
                    'confidence': place.confidence,
                    'method': place.extraction_method,
                    'sentence': place.sentence[:50] + '...' if len(place.sentence) > 50 else place.sentence
                }
                for place in places[:10]  # 最初の10件のみ
            ],
            'categories': categories,
            'success': len(places) > 0
        }

if __name__ == "__main__":
    # 簡単なテスト
    extractor = EnhancedPlaceExtractor()
    
    test_text = """
    私は東京都新宿区に住んでいます。
    鎌倉の大仏を見に行きました。
    津軽海峡を渡って北海道に向かいました。
    """
    
    result = extractor.test_extraction(test_text)
    
    print("✅ Enhanced Place Extractor v4 テスト完了")
    print(f"📊 抽出地名数: {result['total_places']}")
    for place in result['places']:
        print(f"🗺️ {place['name']} (信頼度: {place['confidence']:.2f})")
