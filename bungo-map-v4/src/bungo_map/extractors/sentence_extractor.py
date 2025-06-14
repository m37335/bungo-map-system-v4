"""
Bungo Map System v4.0 Sentence-Based Extractor

センテンス中心の地名抽出器
- 1センテンスから複数地名を抽出
- v3.0の4つの抽出器を統合利用
- 重複排除・正規化処理
"""

import re
import sys
import os
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

# v3.0抽出器を利用（統合後のパス）
from bungo_map.extractors.simple_place_extractor import SimplePlaceExtractor
from bungo_map.extractors.enhanced_place_extractor import EnhancedPlaceExtractor


@dataclass
class ExtractedPlace:
    """抽出された地名情報"""
    place_name: str
    extraction_method: str
    confidence: float
    position: int  # 文中での位置
    matched_text: str  # 実際にマッチした文字列
    context_before: str = ""
    context_after: str = ""


class SentenceBasedExtractor:
    """センテンス中心の地名抽出器"""
    
    def __init__(self):
        # v3.0抽出器を初期化
        self.simple_extractor = SimplePlaceExtractor()
        self.enhanced_extractor = EnhancedPlaceExtractor()
        
        # 抽出手法の優先度
        self.method_priority = {
            'regex_有名地名': 1,
            'regex_市区町村': 2, 
            'regex_都道府県': 3,
            'regex_郡': 4,
            'enhanced_compound': 5
        }
    
    def extract_places_from_sentence(self, sentence_text: str, work_id: int = None, author_id: int = None) -> List[ExtractedPlace]:
        """センテンスから地名を抽出"""
        extracted_places = []
        
        # 1. Simple抽出器による抽出
        simple_results = self._extract_with_simple(sentence_text, work_id, author_id)
        extracted_places.extend(simple_results)
        
        # 2. Enhanced抽出器による抽出
        enhanced_results = self._extract_with_enhanced(sentence_text, work_id, author_id)
        extracted_places.extend(enhanced_results)
        
        # 3. 重複排除・統合
        unified_places = self._unify_extracted_places(extracted_places)
        
        # 4. 位置情報付与
        positioned_places = self._add_position_info(unified_places, sentence_text)
        
        return positioned_places
    
    def _extract_with_simple(self, sentence_text: str, work_id: int, author_id: int) -> List[ExtractedPlace]:
        """Simple抽出器を使用"""
        results = []
        
        try:
            # v3.0のextract_places_from_textメソッドを呼び出し
            extracted_places = self.simple_extractor.extract_places_from_text(
                work_id or 0, sentence_text
            )
            
            for place in extracted_places:
                extracted_place = ExtractedPlace(
                    place_name=place.place_name,
                    extraction_method=place.extraction_method,
                    confidence=place.confidence,
                    position=0,  # 後で計算
                    matched_text=place.place_name,
                    context_before=place.before_text,
                    context_after=place.after_text
                )
                results.append(extracted_place)
                
        except Exception as e:
            print(f"⚠️ Simple抽出器エラー: {e}")
        
        return results
    
    def _extract_with_enhanced(self, sentence_text: str, work_id: int, author_id: int) -> List[ExtractedPlace]:
        """Enhanced抽出器を使用"""
        results = []
        
        try:
            # Enhanced抽出器のextract_places_from_workメソッドを呼び出し
            enhanced_places = self.enhanced_extractor.extract_places_from_work(
                work_id or 0, sentence_text
            )
            
            for place in enhanced_places:
                extracted_place = ExtractedPlace(
                    place_name=place.place_name,
                    extraction_method=place.extraction_method,
                    confidence=place.confidence,
                    position=0,  # 後で計算
                    matched_text=place.place_name,
                    context_before=place.before_text,
                    context_after=place.after_text
                )
                results.append(extracted_place)
                
        except Exception as e:
            print(f"⚠️ Enhanced抽出器エラー: {e}")
        
        return results
    
    def _unify_extracted_places(self, places: List[ExtractedPlace]) -> List[ExtractedPlace]:
        """重複地名の統合・優先度処理"""
        if not places:
            return []
        
        # 地名ごとにグループ化
        place_groups = {}
        for place in places:
            canonical_name = self._normalize_place_name(place.place_name)
            if canonical_name not in place_groups:
                place_groups[canonical_name] = []
            place_groups[canonical_name].append(place)
        
        # 各グループから最適な1つを選択
        unified_places = []
        for canonical_name, group in place_groups.items():
            best_place = self._select_best_place(group)
            unified_places.append(best_place)
        
        return unified_places
    
    def _select_best_place(self, places: List[ExtractedPlace]) -> ExtractedPlace:
        """同一地名の複数抽出結果から最適なものを選択"""
        if len(places) == 1:
            return places[0]
        
        # 優先度とconfidenceで評価
        best_place = places[0]
        best_score = self._calculate_place_score(best_place)
        
        for place in places[1:]:
            score = self._calculate_place_score(place)
            if score > best_score:
                best_place = place
                best_score = score
        
        return best_place
    
    def _calculate_place_score(self, place: ExtractedPlace) -> float:
        """地名抽出結果のスコア計算"""
        # 手法優先度（数値が小さいほど高優先度）
        method_score = 1.0 / self.method_priority.get(place.extraction_method, 10)
        
        # 信頼度
        confidence_score = place.confidence
        
        # 地名の長さ（長いほど具体的）
        length_score = len(place.place_name) / 20.0  # 最大20文字として正規化
        
        # 総合スコア
        total_score = method_score * 0.5 + confidence_score * 0.3 + length_score * 0.2
        
        return total_score
    
    def _add_position_info(self, places: List[ExtractedPlace], sentence_text: str) -> List[ExtractedPlace]:
        """地名の文中位置情報を付与"""
        for place in places:
            # 地名の出現位置を検索
            position = sentence_text.find(place.matched_text)
            if position == -1:
                # 完全一致しない場合は類似文字列検索
                position = self._find_similar_position(place.matched_text, sentence_text)
            
            place.position = position if position != -1 else 0
            
            # 前後文脈の再設定
            if position != -1:
                start = max(0, position - 20)
                end = min(len(sentence_text), position + len(place.matched_text) + 20)
                
                place.context_before = sentence_text[start:position]
                place.context_after = sentence_text[position + len(place.matched_text):end]
        
        # 位置順でソート
        places.sort(key=lambda p: p.position)
        
        return places
    
    def _find_similar_position(self, target: str, sentence: str) -> int:
        """類似文字列の位置検索"""
        # 部分文字列として検索
        for i in range(len(sentence) - len(target) + 1):
            substring = sentence[i:i + len(target)]
            if self._similarity(target, substring) > 0.8:
                return i
        return -1
    
    def _similarity(self, s1: str, s2: str) -> float:
        """文字列類似度計算（簡易版）"""
        if not s1 or not s2:
            return 0.0
        
        # 共通文字数 / 最大文字数
        common_chars = sum(1 for c in s1 if c in s2)
        max_length = max(len(s1), len(s2))
        
        return common_chars / max_length
    
    def _normalize_place_name(self, place_name: str) -> str:
        """地名正規化（重複判定用）"""
        # 基本的な正規化
        normalized = place_name.strip()
        
        # 全角・半角統一
        normalized = normalized.replace('　', ' ')
        
        # よくある表記揺れの統一
        normalized = normalized.replace('ヶ', 'が')
        normalized = normalized.replace('ケ', 'が')
        
        return normalized
    
    def extract_and_analyze_sentence(self, sentence_text: str, work_id: int = None, author_id: int = None) -> Dict[str, Any]:
        """センテンス解析（統計情報付き）"""
        places = self.extract_places_from_sentence(sentence_text, work_id, author_id)
        
        # 統計情報
        method_counts = {}
        total_confidence = 0.0
        
        for place in places:
            method = place.extraction_method
            method_counts[method] = method_counts.get(method, 0) + 1
            total_confidence += place.confidence
        
        avg_confidence = total_confidence / len(places) if places else 0.0
        
        return {
            'sentence_text': sentence_text,
            'places': [place.__dict__ for place in places],
            'place_count': len(places),
            'method_distribution': method_counts,
            'average_confidence': avg_confidence,
            'has_multiple_places': len(places) > 1
        } 