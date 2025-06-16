#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文脈解析機能
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import spacy
from .base_extractor import ExtractedPlace

@dataclass
class ContextInfo:
    """文脈情報"""
    text: str
    place_name: str
    start_pos: int
    end_pos: int
    context_before: str
    context_after: str
    is_valid: bool
    confidence: float
    context_type: str
    related_places: List[str]

class ContextAnalyzer:
    """文脈解析クラス"""
    
    def __init__(self):
        self.nlp = spacy.load('ja_ginza')
        self.context_patterns = self._compile_context_patterns()
    
    def analyze(self, text: str, place: ExtractedPlace) -> ContextInfo:
        """
        地名の文脈を解析
        
        Args:
            text: 解析対象のテキスト
            place: 抽出された地名
            
        Returns:
            文脈情報
        """
        # 文脈の抽出
        context_before, context_after = self._extract_context(text, place)
        
        # 文脈の解析
        is_valid, confidence, context_type = self._analyze_context(
            text, place, context_before, context_after
        )
        
        # 関連地名の抽出
        related_places = self._extract_related_places(
            text, place, context_before, context_after
        )
        
        return ContextInfo(
            text=text,
            place_name=place.place_name,
            start_pos=place.start_pos,
            end_pos=place.end_pos,
            context_before=context_before,
            context_after=context_after,
            is_valid=is_valid,
            confidence=confidence,
            context_type=context_type,
            related_places=related_places
        )
    
    def _extract_context(self, text: str, place: ExtractedPlace) -> Tuple[str, str]:
        """文脈を抽出"""
        # 前後の文脈を抽出（最大100文字）
        start = max(0, place.start_pos - 100)
        end = min(len(text), place.end_pos + 100)
        
        context_before = text[start:place.start_pos].strip()
        context_after = text[place.end_pos:end].strip()
        
        return context_before, context_after
    
    def _analyze_context(self, text: str, place: ExtractedPlace,
                        context_before: str, context_after: str) -> Tuple[bool, float, str]:
        """文脈を解析"""
        # 文脈パターンのマッチング
        for pattern, context_type, confidence in self.context_patterns:
            if pattern.search(context_before) or pattern.search(context_after):
                return True, confidence, context_type
        
        # 文法的な解析
        doc = self.nlp(text)
        for token in doc:
            if token.text == place.place_name:
                # 地名の品詞と依存関係を確認
                if token.pos_ in ['PROPN', 'NOUN'] and token.dep_ in ['nsubj', 'dobj', 'pobj']:
                    return True, 0.8, 'grammatical'
        
        return False, 0.5, 'unknown'
    
    def _extract_related_places(self, text: str, place: ExtractedPlace,
                              context_before: str, context_after: str) -> List[str]:
        """関連地名を抽出"""
        related_places = []
        
        # 文脈内の地名を抽出
        doc = self.nlp(context_before + " " + context_after)
        for ent in doc.ents:
            if ent.label_ in ['LOC', 'GPE'] and ent.text != place.place_name:
                related_places.append(ent.text)
        
        return related_places
    
    def _compile_context_patterns(self) -> List[Tuple[re.Pattern, str, float]]:
        """文脈パターンをコンパイル"""
        patterns = [
            # 移動・位置に関する文脈
            (re.compile(r'(?:行く|来る|着く|向かう|移動する|位置する|ある|いる)'), 'movement', 0.9),
            # 描写に関する文脈
            (re.compile(r'(?:見える|見る|眺める|見渡す|見上げる|見下ろす)'), 'description', 0.8),
            # 時間に関する文脈
            (re.compile(r'(?:朝|昼|夕方|夜|午前|午後|夜中)'), 'time', 0.7),
            # 天候に関する文脈
            (re.compile(r'(?:晴れ|雨|曇り|雪|風|雷)'), 'weather', 0.7),
            # 季節に関する文脈
            (re.compile(r'(?:春|夏|秋|冬|季節)'), 'season', 0.7),
            # 距離に関する文脈
            (re.compile(r'(?:近い|遠い|隣|向かい|手前|奥)'), 'distance', 0.8),
            # 方向に関する文脈
            (re.compile(r'(?:東|西|南|北|上|下|左|右)'), 'direction', 0.8),
        ]
        return patterns
    
    def get_context_summary(self, context: ContextInfo) -> str:
        """
        文脈情報の要約を生成
        
        Args:
            context: 文脈情報
            
        Returns:
            要約文字列
        """
        summary = []
        summary.append(f"地名: {context.place_name}")
        summary.append(f"文脈タイプ: {context.context_type}")
        summary.append(f"信頼度: {context.confidence:.2f}")
        summary.append(f"妥当性: {'有効' if context.is_valid else '無効'}")
        
        if context.related_places:
            summary.append(f"関連地名: {', '.join(context.related_places)}")
        
        return "\n".join(summary) 