#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫テキストクリーニング
作品テキストのクリーニングと正規化を行う
"""

import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CleanedText:
    """クリーニング済みテキストデータクラス"""
    text: str
    removed_ruby: List[str]
    removed_notes: List[str]
    removed_headers: List[str]
    removed_footers: List[str]

class AozoraCleaner:
    """青空文庫テキストクリーニングクラス"""
    
    def __init__(self):
        """初期化"""
        # ルビのパターン
        self.ruby_pattern = re.compile(r'《.*?》')
        
        # 注記のパターン
        self.note_pattern = re.compile(r'［.*?］')
        
        # ヘッダーのパターン
        self.header_pattern = re.compile(r'^.*?【.*?】.*?$', re.MULTILINE)
        
        # フッターのパターン
        self.footer_pattern = re.compile(r'底本：.*?$', re.MULTILINE)
        
        logger.info("🧹 青空文庫テキストクリーニングクラス初期化完了")
    
    def clean_text(self, text: str) -> CleanedText:
        """テキストのクリーニング"""
        # ルビの除去
        removed_ruby = self.ruby_pattern.findall(text)
        text = self.ruby_pattern.sub('', text)
        
        # 注記の除去
        removed_notes = self.note_pattern.findall(text)
        text = self.note_pattern.sub('', text)
        
        # ヘッダーの除去
        removed_headers = self.header_pattern.findall(text)
        text = self.header_pattern.sub('', text)
        
        # フッターの除去
        removed_footers = self.footer_pattern.findall(text)
        text = self.footer_pattern.sub('', text)
        
        # 空行の除去
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # 前後の空白を除去
        text = text.strip()
        
        return CleanedText(
            text=text,
            removed_ruby=removed_ruby,
            removed_notes=removed_notes,
            removed_headers=removed_headers,
            removed_footers=removed_footers
        )
    
    def normalize_text(self, text: str) -> str:
        """テキストの正規化"""
        # 全角数字を半角に変換
        text = re.sub(r'[０-９]', lambda m: str('０１２３４５６７８９'.index(m.group())), text)
        
        # 全角英字を半角に変換
        text = re.sub(r'[Ａ-Ｚａ-ｚ]', lambda m: chr(ord(m.group()) - 0xFEE0), text)
        
        # 全角記号を半角に変換
        text = re.sub(r'[！＂＃＄％＆＇（）＊＋，－．／：；＜＝＞？＠［＼］＾＿｀｛｜｝～]',
                     lambda m: chr(ord(m.group()) - 0xFEE0), text)
        
        # 空白の正規化
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def clean_and_normalize(self, text: str) -> CleanedText:
        """テキストのクリーニングと正規化"""
        # クリーニング
        cleaned = self.clean_text(text)
        
        # 正規化
        cleaned.text = self.normalize_text(cleaned.text)
        
        return cleaned 