#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改良地名抽出器 v4
重複抽出問題と緯度経度変換問題を解決 - v3からの移植・改良版
"""

import re
import logging
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ImprovedPlace:
    """改良版地名データ"""
    work_id: int
    place_name: str
    sentence: str
    before_text: str = ""
    after_text: str = ""
    category: str = ""
    confidence: float = 0.0
    priority: int = 5
    extraction_method: str = "improved_regex"
    start_pos: int = 0
    end_pos: int = 0
    aozora_url: str = ""

class ImprovedPlaceExtractor:
    """重複抽出を防ぐ改良された地名抽出器 v4"""
    
    def __init__(self):
        self.patterns = self._build_improved_patterns()
        logger.info("✅ 改良地名抽出器v4初期化完了")
    
    def _build_improved_patterns(self) -> List[Dict]:
        """改良された地名抽出パターン"""
        return [
            # 1. 都道府県（境界条件強化）
            {
                'pattern': r'(?<![一-龯])[北海青森岩手宮城秋田山形福島茨城栃木群馬埼玉千葉東京神奈川新潟富山石川福井山梨長野岐阜静岡愛知三重滋賀京都大阪兵庫奈良和歌山鳥取島根岡山広島山口徳島香川愛媛高知福岡佐賀長崎熊本大分宮崎鹿児島沖縄][都道府県](?![一-龯])',
                'category': '都道府県',
                'confidence': 0.95,
                'priority': 1
            },
            
            # 2. 完全地名（都道府県+市区町村）- 最高優先度
            {
                'pattern': r'(?<![一-龯])[北海青森岩手宮城秋田山形福島茨城栃木群馬埼玉千葉東京神奈川新潟富山石川福井山梨長野岐阜静岡愛知三重滋賀京都大阪兵庫奈良和歌山鳥取島根岡山広島山口徳島香川愛媛高知福岡佐賀長崎熊本大分宮崎鹿児島沖縄][都道府県][一-龯]{2,8}[市区町村](?![一-龯])',
                'category': '完全地名',
                'confidence': 0.98,
                'priority': 0  # 最高優先度
            },
            
            # 3. 市区町村（境界条件強化）
            {
                'pattern': r'(?<![一-龯])[一-龯]{2,6}[市区町村](?![一-龯])',
                'category': '市区町村',
                'confidence': 0.85,
                'priority': 2
            },
            
            # 4. 郡（境界条件強化）
            {
                'pattern': r'(?<![一-龯])[一-龯]{2,4}[郡](?![一-龯])',
                'category': '郡',
                'confidence': 0.80,
                'priority': 3
            },
            
            # 5. 有名地名（明示リスト）
            {
                'pattern': r'(?:' + '|'.join([
                    '銀座', '新宿', '渋谷', '上野', '浅草', '品川', '池袋', '新橋', '有楽町',
                    '横浜', '川崎', '千葉', '船橋', '柏', '鎌倉', '湘南', '箱根',
                    '京都', '大阪', '神戸', '奈良', '江戸', '本郷', '神田', '日本橋',
                    '津軽', '松山', '四国', '九州', '本州', '北海道'
                ]) + r')',
                'category': '有名地名',
                'confidence': 0.90,
                'priority': 4
            },
            
            # 6. 自然地名
            {
                'pattern': r'(?<![一-龯])[一-龯]{1,4}[川山湖海峠谷野原島岬浦崎](?![一-龯])',
                'category': '自然地名',
                'confidence': 0.75,
                'priority': 5
            }
        ]
    
    def extract_places_with_deduplication(self, work_id: int, text: str, aozora_url: str = "") -> List[ImprovedPlace]:
        """重複排除機能付き地名抽出（メイン機能）"""
        if not text or len(text) < 10:
            logger.warning(f"テキストが短すぎます: {len(text)}文字")
            return []
            
        all_matches = []
        sentences = self._split_into_sentences(text)
        
        logger.info(f"📄 文数: {len(sentences)}, 文字数: {len(text)}")
        
        for sentence_idx, sentence in enumerate(sentences):
            sentence_matches = self._extract_from_sentence(sentence, sentence_idx, sentences)
            
            # 重複排除処理
            deduplicated_matches = self._deduplicate_overlapping_matches(sentence_matches)
            all_matches.extend(deduplicated_matches)
        
        # ImprovedPlaceオブジェクトに変換
        places = []
        for match in all_matches:
            place = ImprovedPlace(
                work_id=work_id,
                place_name=match['text'],
                sentence=match['sentence'],
                before_text=match['before_text'][:300],
                after_text=match['after_text'][:300],
                category=match['category'],
                confidence=match['confidence'],
                priority=match['priority'],
                extraction_method=f"improved_{match['category']}",
                start_pos=match['start'],
                end_pos=match['end'],
                aozora_url=aozora_url
            )
            places.append(place)
        
        logger.info(f"✅ 改良地名抽出完了: {len(places)}件")
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
    
    def analyze_extraction_problems(self, text: str) -> Dict:
        """抽出問題の分析"""
        logger.info("🔍 地名抽出問題分析開始")
        
        # 改良版で抽出
        improved_places = self.extract_places_with_deduplication(999, text)
        
        # 基本パターンで抽出（比較用）
        basic_matches = self._simulate_basic_extractor(text)
        
        # 重複グループの検出
        overlapping_groups = self._find_overlapping_groups(basic_matches)
        
        return {
            "input_text": text[:100] + "..." if len(text) > 100 else text,
            "basic_extraction": {
                "total_matches": len(basic_matches),
                "overlapping_groups": len(overlapping_groups),
                "problematic_extractions": [
                    m for m in basic_matches 
                    if len(m['text']) <= 2  # 短すぎる地名
                ]
            },
            "improved_extraction": {
                "total_matches": len(improved_places),
                "high_confidence_count": len([p for p in improved_places if p.confidence >= 0.9]),
                "categories": self._get_category_stats(improved_places)
            },
            "comparison": {
                "reduction_rate": (len(basic_matches) - len(improved_places)) / len(basic_matches) if basic_matches else 0,
                "quality_improvement": len([p for p in improved_places if p.confidence >= 0.9]) / len(improved_places) if improved_places else 0
            }
        }
    
    def _simulate_basic_extractor(self, text: str) -> List[Dict]:
        """基本抽出器をシミュレート（比較用）"""
        basic_patterns = [
            r'[北海青森岩手宮城秋田山形福島茨城栃木群馬埼玉千葉東京神奈川新潟富山石川福井山梨長野岐阜静岡愛知三重滋賀京都大阪兵庫奈良和歌山鳥取島根岡山広島山口徳島香川愛媛高知福岡佐賀長崎熊本大分宮崎鹿児島沖縄][都道府県]',
            r'[一-龯]{2,8}[市区町村]',
            r'(?:船橋|千葉|銀座|新宿|上野)'
        ]
        
        matches = []
        for i, pattern in enumerate(basic_patterns):
            for match in re.finditer(pattern, text):
                matches.append({
                    'text': match.group(0),
                    'start': match.start(),
                    'end': match.end(),
                    'pattern_id': i
                })
        
        return matches
    
    def _find_overlapping_groups(self, matches: List[Dict]) -> List[List[Dict]]:
        """重複するマッチのグループを検出"""
        if not matches:
            return []
        
        # 位置順でソート
        matches.sort(key=lambda x: x['start'])
        
        groups = []
        current_group = [matches[0]]
        
        for i in range(1, len(matches)):
            current_match = matches[i]
            last_in_group = current_group[-1]
            
            # 重複チェック
            if self._ranges_overlap(
                (current_match['start'], current_match['end']),
                (last_in_group['start'], last_in_group['end'])
            ):
                current_group.append(current_match)
            else:
                if len(current_group) > 1:
                    groups.append(current_group)
                current_group = [current_match]
        
        if len(current_group) > 1:
            groups.append(current_group)
        
        return groups
    
    def _get_category_stats(self, places: List[ImprovedPlace]) -> Dict[str, int]:
        """カテゴリー別統計を取得"""
        stats = {}
        for place in places:
            category = place.category
            stats[category] = stats.get(category, 0) + 1
        return stats
    
    def test_extraction(self, test_text: str) -> Dict:
        """抽出機能のテスト"""
        logger.info("🧪 Improved Place Extractor テスト開始")
        
        places = self.extract_places_with_deduplication(999, test_text)
        analysis = self.analyze_extraction_problems(test_text)
        
        return {
            'test_text_length': len(test_text),
            'total_places': len(places),
            'places': [
                {
                    'name': place.place_name,
                    'category': place.category,
                    'confidence': place.confidence,
                    'priority': place.priority,
                    'sentence': place.sentence[:50] + '...' if len(place.sentence) > 50 else place.sentence
                }
                for place in places[:10]  # 最初の10件のみ
            ],
            'analysis': analysis,
            'success': len(places) > 0
        }

if __name__ == "__main__":
    # 詳細テスト
    extractor = ImprovedPlaceExtractor()
    
    test_text = """
    私は東京都新宿区に住んでいます。
    鎌倉の大仏を見に行きました。
    津軽海峡を渡って北海道に向かいました。
    京都府京都市を経由して奈良県奈良市に到着しました。
    富士山の山頂から見た景色は素晴らしかった。
    """
    
    result = extractor.test_extraction(test_text)
    
    print("✅ Improved Place Extractor v4 テスト完了")
    print(f"📊 抽出地名数: {result['total_places']}")
    
    for place in result['places']:
        print(f"🗺️ {place['name']} [{place['category']}] (信頼度: {place['confidence']:.2f}, 優先度: {place['priority']})")
    
    print(f"\n📈 品質向上率: {result['analysis']['comparison']['quality_improvement']:.1%}")
    print(f"📉 抽出数削減率: {result['analysis']['comparison']['reduction_rate']:.1%}") 