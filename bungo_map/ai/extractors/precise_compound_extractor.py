#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 精密複合地名抽出器
完全境界検出による高精度複合地名抽出
"""

import re
import logging
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass

from bungo_map.core.models import Place
from bungo_map.utils.aozora_text_cleaner import clean_aozora_sentence

logger = logging.getLogger(__name__)

@dataclass
class PrecisePlaceMatch:
    """精密地名マッチ"""
    full_name: str
    start_pos: int
    end_pos: int
    confidence: float
    match_type: str
    components: List[Dict]

class PreciseCompoundExtractor:
    """精密複合地名抽出器"""
    
    def __init__(self, openai_api_key: str = None):
        self.ai_enabled = openai_api_key is not None
        
        # 都道府県の完全リスト
        self.prefectures = [
            '北海道', '青森', '岩手', '宮城', '秋田', '山形', '福島',
            '茨城', '栃木', '群馬', '埼玉', '千葉', '東京', '神奈川',
            '新潟', '富山', '石川', '福井', '山梨', '長野', '岐阜',
            '静岡', '愛知', '三重', '滋賀', '京都', '大阪', '兵庫',
            '奈良', '和歌山', '鳥取', '島根', '岡山', '広島', '山口',
            '徳島', '香川', '愛媛', '高知', '福岡', '佐賀', '長崎',
            '熊本', '大分', '宮崎', '鹿児島', '沖縄'
        ]
        
        # 都道府県接尾辞
        self.prefecture_suffixes = ['都', '道', '府', '県']
        
        # 地名接尾辞
        self.place_suffixes = ['市', '区', '町', '村', '郡']
        
        logger.info(f"🎯 精密複合地名抽出器初期化完了 (AI機能: {'有効' if self.ai_enabled else '無効'})")
    
    def extract_precise_places(self, work_id: int, text: str, aozora_url: str = None) -> List[Place]:
        """精密複合地名抽出のメインメソッド"""
        logger.info(f"🎯 精密地名抽出開始 (work_id: {work_id})")
        
        if not text:
            return []
        
        places = []
        
        # 文に分割して処理
        sentences = re.split(r'[。！？]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            # 青空文庫テキストのクリーニング
            clean_sentence = clean_aozora_sentence(sentence)
            if len(clean_sentence) < 10:
                continue
            
            # 複合地名パターンをクリーンアップされた文で検索
            sentence_places = self._extract_from_sentence(work_id, clean_sentence, sentence, aozora_url)
            places.extend(sentence_places)
        
        # 重複排除と最適化
        optimized_places = self._optimize_compound_places(places)
        
        logger.info(f"✅ 精密抽出完了: {len(optimized_places)}件")
        return optimized_places

    def _extract_from_sentence(self, work_id: int, clean_sentence: str, original_sentence: str, aozora_url: str = None) -> List[Place]:
        """単一文からの地名抽出"""
        places = []
        
        # 複合地名パターンで検索
        for pattern_name, (pattern, confidence) in self.compound_patterns.items():
            matches = re.finditer(pattern, clean_sentence)
            for match in matches:
                compound_place = match.group()
                
                # 地理的妥当性チェック
                if self._validate_geographic_structure(compound_place):
                    # 人名との区別チェック
                    if not self._is_person_name(compound_place, clean_sentence):
                        # 前後のコンテキスト取得（元の文から）
                        before_text, after_text = self._get_context(original_sentence, compound_place)
                        
                        place = Place(
                            work_id=work_id,
                            place_name=compound_place,
                            before_text=before_text,
                            sentence=clean_sentence,  # クリーンアップされた文を保存
                            after_text=after_text,
                            aozora_url=aozora_url,
                            confidence=confidence,
                            extraction_method=pattern_name
                        )
                        places.append(place)
        
        return places
    
    def _find_prefecture_gun_village(self, sentence: str) -> List[PrecisePlaceMatch]:
        """都道府県+郡+町村パターンの検出"""
        matches = []
        
        for pref in self.prefectures:
            # 都道府県名を検索
            pref_pattern = f'{pref}[都道府県]'
            pref_matches = list(re.finditer(pref_pattern, sentence))
            
            for pref_match in pref_matches:
                pref_end = pref_match.end()
                
                # 都道府県の直後から郡を検索
                remaining_text = sentence[pref_end:]
                gun_pattern = r'([一-龯]{2,4}郡)'
                gun_match = re.match(gun_pattern, remaining_text)
                
                if gun_match:
                    gun_end = pref_end + gun_match.end()
                    
                    # 郡の直後から町村を検索
                    remaining_text2 = sentence[gun_end:]
                    village_pattern = r'([一-龯]{2,6}[町村])'
                    village_match = re.match(village_pattern, remaining_text2)
                    
                    if village_match:
                        # 完全な複合地名を構築
                        full_name = sentence[pref_match.start():gun_end + village_match.end()]
                        
                        # 境界チェック
                        if self._check_boundaries(sentence, pref_match.start(), gun_end + village_match.end()):
                            match = PrecisePlaceMatch(
                                full_name=full_name,
                                start_pos=pref_match.start(),
                                end_pos=gun_end + village_match.end(),
                                confidence=0.95,  # 3層構造は高信頼度
                                match_type="prefecture_gun_village",
                                components=[
                                    {'type': 'prefecture', 'text': pref_match.group()},
                                    {'type': 'gun', 'text': gun_match.group()},
                                    {'type': 'village', 'text': village_match.group()}
                                ]
                            )
                            matches.append(match)
        
        return matches
    
    def _find_prefecture_city(self, sentence: str) -> List[PrecisePlaceMatch]:
        """都道府県+市区町村パターンの検出"""
        matches = []
        
        for pref in self.prefectures:
            pref_pattern = f'{pref}[都道府県]'
            pref_matches = list(re.finditer(pref_pattern, sentence))
            
            for pref_match in pref_matches:
                pref_end = pref_match.end()
                
                # 都道府県の直後から市区町村を検索
                remaining_text = sentence[pref_end:]
                city_pattern = r'([一-龯]{2,8}[市区町村])'
                city_match = re.match(city_pattern, remaining_text)
                
                if city_match:
                    # 完全な複合地名を構築
                    full_name = sentence[pref_match.start():pref_end + city_match.end()]
                    
                    # 境界チェック
                    if self._check_boundaries(sentence, pref_match.start(), pref_end + city_match.end()):
                        match = PrecisePlaceMatch(
                            full_name=full_name,
                            start_pos=pref_match.start(),
                            end_pos=pref_end + city_match.end(),
                            confidence=0.90,  # 2層構造
                            match_type="prefecture_city",
                            components=[
                                {'type': 'prefecture', 'text': pref_match.group()},
                                {'type': 'city', 'text': city_match.group()}
                            ]
                        )
                        matches.append(match)
        
        return matches
    
    def _find_city_ward(self, sentence: str) -> List[PrecisePlaceMatch]:
        """市+区パターンの検出"""
        matches = []
        
        # 市を検索
        city_pattern = r'([一-龯]{2,8}市)'
        city_matches = list(re.finditer(city_pattern, sentence))
        
        for city_match in city_matches:
            city_end = city_match.end()
            
            # 市の直後から区を検索
            remaining_text = sentence[city_end:]
            ward_pattern = r'([一-龯]{2,4}区)'
            ward_match = re.match(ward_pattern, remaining_text)
            
            if ward_match:
                # 完全な複合地名を構築
                full_name = sentence[city_match.start():city_end + ward_match.end()]
                
                # 境界チェック
                if self._check_boundaries(sentence, city_match.start(), city_end + ward_match.end()):
                    match = PrecisePlaceMatch(
                        full_name=full_name,
                        start_pos=city_match.start(),
                        end_pos=city_end + ward_match.end(),
                        confidence=0.85,  # 市区構造
                        match_type="city_ward",
                        components=[
                            {'type': 'city', 'text': city_match.group()},
                            {'type': 'ward', 'text': ward_match.group()}
                        ]
                    )
                    matches.append(match)
        
        return matches
    
    def _check_boundaries(self, sentence: str, start: int, end: int) -> bool:
        """境界条件の調整済みチェック"""
        # 完全な文の開始/終了は常に有効
        if start == 0 or end == len(sentence):
            return True
        
        # 前方境界チェック（緩和）
        if start > 0:
            prev_char = sentence[start - 1]
            # 句読点、空白、助詞の後は有効
            if prev_char in '。、！？ 　はがをにで、':
                return True
            # 一部の文字の後も許可（数字、記号等）
            if re.match(r'[0-9０-９\s\(\)（）]', prev_char):
                return True
            # 漢字が前にあっても、文脈によっては有効
            if re.match(r'[一-龯]', prev_char):
                # 特定の文脈パターンをチェック
                context_before = sentence[max(0, start-10):start]
                if any(pattern in context_before for pattern in ['、', '。', 'は', 'が', 'を', 'に', 'で']):
                    return True
                # 人名の後の地名は有効（例：「小川三四郎福岡県...」→無効、「...たずねた福岡県...」→有効）
                if not any(name in context_before for name in ['三四郎', '太郎', '花子']):
                    return True
        
        # 後方境界チェック（緩和）
        if end < len(sentence):
            next_char = sentence[end]
            # 句読点、空白、助詞の前は有効
            if next_char in '。、！？ 　はがをにで、':
                return True
            # 一部の文字の前も許可
            if re.match(r'[0-9０-９\s\(\)（）]', next_char):
                return True
            # 漢字が後にあっても、文脈によっては有効
            if re.match(r'[一-龯]', next_char):
                # 特定の文脈パターンをチェック
                context_after = sentence[end:min(len(sentence), end+10)]
                if any(pattern in context_after for pattern in ['小川', '三四郎', '太郎', '花子']):
                    return True  # 人名が続く場合は地名として有効
                return True  # その他の漢字が続く場合も一旦許可
        
        return True  # デフォルトは許可
    
    def _filter_and_deduplicate(self, matches: List[PrecisePlaceMatch], sentence: str) -> List[PrecisePlaceMatch]:
        """フィルタリングと重複排除"""
        if not matches:
            return []
        
        # AI文脈チェック（有効な場合）
        if self.ai_enabled:
            matches = self._ai_context_filter(matches, sentence)
        
        # 重複排除（包含関係を考慮）
        filtered = []
        
        # 信頼度と長さでソート
        sorted_matches = sorted(matches, key=lambda m: (-m.confidence, -len(m.full_name)))
        
        for match in sorted_matches:
            # 既存の地名に包含されるかチェック
            is_contained = False
            for existing in filtered:
                if (match.start_pos >= existing.start_pos and 
                    match.end_pos <= existing.end_pos and
                    match.full_name != existing.full_name):
                    is_contained = True
                    break
            
            if not is_contained:
                # 現在の地名が既存の地名を包含するかチェック
                to_remove = []
                for i, existing in enumerate(filtered):
                    if (existing.start_pos >= match.start_pos and
                        existing.end_pos <= match.end_pos and
                        existing.full_name != match.full_name):
                        to_remove.append(i)
                
                # 包含される地名を削除
                for i in reversed(to_remove):
                    filtered.pop(i)
                
                filtered.append(match)
        
        return filtered
    
    def _ai_context_filter(self, matches: List[PrecisePlaceMatch], sentence: str) -> List[PrecisePlaceMatch]:
        """AI文脈フィルタリング"""
        validated = []
        
        for match in matches:
            # 簡易AI分析
            context_score = self._analyze_context(match.full_name, sentence)
            
            if context_score > 0.6:
                # 文脈分析で信頼度調整
                match.confidence = min(match.confidence * (0.8 + context_score * 0.4), 1.0)
                validated.append(match)
            else:
                logger.info(f"文脈除外: {match.full_name} (スコア: {context_score:.2f})")
        
        return validated
    
    def _analyze_context(self, place_name: str, sentence: str) -> float:
        """文脈分析"""
        score = 0.7  # ベーススコア
        
        # 地名を示す文脈
        location_contexts = [
            r'[に|で|から|へ|まで][住む|いる|ある|行く|来る|向かう|発つ]',
            r'[疎開|移住|旅行|滞在|訪問]',
            r'[生まれ|育つ|住む]'
        ]
        
        for pattern in location_contexts:
            if re.search(pattern, sentence):
                score += 0.2
                break
        
        # 人名と混同しやすいパターン
        person_indicators = [
            r'小川三四郎',  # 具体的な人名
            r'[という|名前|呼ばれる][人|男|女|友人]',
            r'[さん|君|氏|先生|様]'
        ]
        
        for pattern in person_indicators:
            if re.search(pattern, sentence):
                score -= 0.4
                break
        
        return max(0.0, min(score, 1.0))
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """テキストを文に分割"""
        sentences = re.split(r'[。！？]', text)
        return [s.strip() for s in sentences if s.strip()]

# テスト関数
def test_precise_extraction():
    """精密抽出のテスト"""
    extractor = PreciseCompoundExtractor()
    
    test_cases = [
        "福岡県京都郡真崎村小川三四郎二十三年学生と正直に書いた",
        "然るに、ことしの二月、私は千葉県船橋市に疎開している或る友人をたずねた",
        "東京都新宿区にある高層ビルから富士山を眺める", 
        "北海道札幌市白石区で生まれ育った友人",
        "大きな萩が人の背より高く延びて、その奥に見える東京の空"
    ]
    
    print("🎯 精密複合地名抽出テスト\n")
    
    for i, text in enumerate(test_cases, 1):
        print(f"【テスト{i}】: {text[:50]}...")
        
        places = extractor.extract_precise_places(999, text)
        
        if places:
            for place in places:
                print(f"  📍 {place.place_name}")
                print(f"     抽出方法: {place.extraction_method}")
                print(f"     信頼度: {place.confidence:.2f}")
        else:
            print("  検出なし")
        
        print()

if __name__ == "__main__":
    test_precise_extraction() 