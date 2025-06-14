#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高度テキストクリーニングシステム v4
多様なテキスト形式・エンコーディングに対応した包括的クリーニング
"""

import re
import logging
import unicodedata
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from pathlib import Path
import html

logger = logging.getLogger(__name__)

@dataclass
class CleaningConfig:
    """クリーニング設定"""
    preserve_line_breaks: bool = True
    normalize_whitespace: bool = True
    remove_html_tags: bool = True
    process_ruby: bool = True
    handle_special_chars: bool = True
    normalize_punctuation: bool = True
    preserve_structure: bool = True

@dataclass
class CleaningStats:
    """クリーニング統計"""
    original_length: int = 0
    cleaned_length: int = 0
    html_tags_removed: int = 0
    ruby_processed: int = 0
    special_chars_processed: int = 0
    whitespace_normalized: int = 0

class AdvancedTextCleaner:
    """高度テキストクリーニングシステム v4"""
    
    def __init__(self, config: Optional[CleaningConfig] = None):
        """初期化"""
        self.config = config or CleaningConfig()
        self.stats = CleaningStats()
        
        # HTMLタグパターン（拡張）
        self.html_patterns = {
            # 基本HTMLタグ
            'basic_tags': r'<[^>]+>',
            'html_entities': r'&[a-zA-Z][a-zA-Z0-9]*;',
            'numeric_entities': r'&#[0-9]+;',
            'hex_entities': r'&#x[0-9a-fA-F]+;',
            
            # 青空文庫特有のタグ
            'aozora_tags': r'<[^>]*class="[^"]*"[^>]*>',
            'ruby_tags': r'<ruby[^>]*>.*?</ruby>',
            'rt_tags': r'<rt[^>]*>.*?</rt>',
            'rp_tags': r'<rp[^>]*>.*?</rp>',
            
            # スタイルタグ
            'style_tags': r'<style[^>]*>.*?</style>',
            'script_tags': r'<script[^>]*>.*?</script>',
            'comment_tags': r'<!--.*?-->',
        }
        
        # ルビパターン（拡張）
        self.ruby_patterns = {
            # 青空文庫ルビ
            'aozora_ruby': r'｜([^《]+)《[^》]+》',
            'auto_ruby': r'([一-龯]+)《[^》]+》',
            'remaining_ruby': r'《[^》]*》',
            
            # HTMLルビ
            'html_ruby': r'<ruby>([^<]+)<rt>[^<]*</rt></ruby>',
            'html_ruby_complex': r'<ruby[^>]*>([^<]+)<rt[^>]*>[^<]*</rt></ruby>',
            
            # その他のルビ記法
            'bracket_ruby': r'([^(]+)（[^)]+）',
            'parenthesis_ruby': r'([^【]+)【[^】]+】',
        }
        
        # 特殊文字パターン
        self.special_char_patterns = {
            # 青空文庫特有の記号
            'aozora_symbols': {
                r'［＃[^］]*］': '',  # 編集注記
                r'〔[^〕]*〕': '',    # 編集注記
                r'※[^※\n]*※': '',   # 注記
                r'＊[^＊\n]*＊': '',   # 注記
                r'〈[^〉]*〉': '',    # 注記
            },
            
            # 特殊空白・制御文字
            'whitespace': {
                r'\u00A0': '　',      # ノーブレークスペース
                r'\u2000': '　',      # En Quad
                r'\u2001': '　',      # Em Quad
                r'\u2002': '　',      # En Space
                r'\u2003': '　',      # Em Space
                r'\u2009': '　',      # Thin Space
                r'\u200A': '　',      # Hair Space
                r'\u3000': '　',      # 全角空白
            },
            
            # Unicode制御文字
            'control_chars': {
                r'\u200B': '',        # Zero Width Space
                r'\u200C': '',        # Zero Width Non-Joiner
                r'\u200D': '',        # Zero Width Joiner
                r'\uFEFF': '',        # Byte Order Mark
                r'\u2060': '',        # Word Joiner
            }
        }
        
        # 句読点正規化パターン
        self.punctuation_patterns = {
            # 句読点統一
            'periods': {
                r'[．。]': '。',
                r'[，、]': '、',
                r'[！!]': '！',
                r'[？?]': '？',
            },
            
            # 括弧統一
            'brackets': {
                r'[（(]': '（',
                r'[）)]': '）',
                r'[「『]': '「',
                r'[」』]': '」',
                r'[［\[]': '［',
                r'[］\]]': '］',
            },
            
            # 引用符統一（安全な形式）
            'quotes': {
                r'"': '"',
                r'"': '"',
                r''': "'",
                r''': "'",
                r'‹': '‹',
                r'›': '›',
                r'«': '«',
                r'»': '»',
            }
        }
        
        logger.info("🧹 高度テキストクリーニングシステム v4 初期化完了")
    
    def clean_text_comprehensive(self, text: str, custom_config: Optional[CleaningConfig] = None) -> Dict[str, Any]:
        """包括的テキストクリーニング"""
        
        if not text:
            return self._create_empty_result()
        
        # 設定の適用
        config = custom_config or self.config
        
        # 統計初期化
        self.stats = CleaningStats()
        self.stats.original_length = len(text)
        
        result = {
            'original_text': text,
            'cleaned_text': '',
            'config': config,
            'stats': None,
            'quality_score': 0.0,
            'issues_found': [],
        }
        
        try:
            cleaned_text = text
            issues = []
            
            # 1. エンコーディング正規化
            cleaned_text, encoding_issues = self._normalize_encoding(cleaned_text)
            issues.extend(encoding_issues)
            
            # 2. HTMLタグ・エンティティ処理
            if config.remove_html_tags:
                cleaned_text, html_issues = self._remove_html_content(cleaned_text)
                issues.extend(html_issues)
            
            # 3. ルビ処理
            if config.process_ruby:
                cleaned_text, ruby_issues = self._process_ruby_advanced(cleaned_text)
                issues.extend(ruby_issues)
            
            # 4. 特殊文字処理
            if config.handle_special_chars:
                cleaned_text, special_issues = self._handle_special_characters(cleaned_text)
                issues.extend(special_issues)
            
            # 5. 句読点正規化
            if config.normalize_punctuation:
                cleaned_text, punct_issues = self._normalize_punctuation(cleaned_text)
                issues.extend(punct_issues)
            
            # 6. 空白・改行正規化
            if config.normalize_whitespace:
                cleaned_text, ws_issues = self._normalize_whitespace(cleaned_text)
                issues.extend(ws_issues)
            
            # 7. 構造保持クリーニング
            if config.preserve_structure:
                cleaned_text = self._preserve_text_structure(cleaned_text)
            
            # 8. 最終品質チェック
            quality_score = self._calculate_cleaning_quality(text, cleaned_text)
            
            # 統計更新
            self.stats.cleaned_length = len(cleaned_text)
            
            # 結果設定
            result.update({
                'cleaned_text': cleaned_text,
                'stats': self.stats,
                'quality_score': quality_score,
                'issues_found': issues,
            })
            
            logger.info(f"🧹 テキストクリーニング完了: {self.stats.original_length}→{self.stats.cleaned_length}文字")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ テキストクリーニングエラー: {e}")
            return self._create_error_result(str(e))
    
    def _normalize_encoding(self, text: str) -> Tuple[str, List[str]]:
        """エンコーディング正規化"""
        
        issues = []
        
        # Unicode正規化
        try:
            normalized = unicodedata.normalize('NFKC', text)
            if len(normalized) != len(text):
                issues.append("Unicode正規化によりテキストが変更されました")
        except Exception as e:
            normalized = text
            issues.append(f"Unicode正規化エラー: {e}")
        
        # 文字コード問題の検出・修正
        encoding_fixes = {
            # よくある文字化け
            'ï¿½': '',              # Unicode replacement character
            'â€™': "'",             # Right single quotation mark
            'â€œ': '"',             # Left double quotation mark
            'â€': '"',              # Right double quotation mark
            'â€"': '—',             # Em dash
            'â€"': '–',             # En dash
            
            # 日本語特有の問題
            'ã': 'あ',               # 文字化け例
            'ï¼': '！',              # 全角感嘆符の文字化け
        }
        
        for broken, fixed in encoding_fixes.items():
            if broken in normalized:
                normalized = normalized.replace(broken, fixed)
                issues.append(f"文字化け修正: '{broken}' → '{fixed}'")
        
        return normalized, issues
    
    def _remove_html_content(self, text: str) -> Tuple[str, List[str]]:
        """HTML要素の除去"""
        
        issues = []
        cleaned = text
        
        # HTMLエンティティのデコード
        try:
            decoded = html.unescape(cleaned)
            if decoded != cleaned:
                issues.append("HTMLエンティティをデコードしました")
                cleaned = decoded
        except Exception as e:
            issues.append(f"HTMLエンティティデコードエラー: {e}")
        
        # HTMLタグの除去
        for tag_type, pattern in self.html_patterns.items():
            matches = re.findall(pattern, cleaned, re.DOTALL | re.IGNORECASE)
            if matches:
                self.stats.html_tags_removed += len(matches)
                issues.append(f"{tag_type}: {len(matches)}個のタグを除去")
                cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # 残ったHTMLっぽい記号の処理
        html_remnants = {
            r'&lt;': '<',
            r'&gt;': '>',
            r'&amp;': '&',
            r'&quot;': '"',
            r'&apos;': "'",
        }
        
        for entity, char in html_remnants.items():
            if entity in cleaned:
                cleaned = cleaned.replace(entity, char)
                issues.append(f"HTML残留記号を修正: {entity} → {char}")
        
        return cleaned, issues
    
    def _process_ruby_advanced(self, text: str) -> Tuple[str, List[str]]:
        """高度ルビ処理"""
        
        issues = []
        processed = text
        
        # 各種ルビパターンの処理
        for ruby_type, pattern in self.ruby_patterns.items():
            if ruby_type in ['aozora_ruby', 'auto_ruby']:
                # ルビを親文字に置換
                matches = re.findall(pattern, processed)
                if matches:
                    self.stats.ruby_processed += len(matches)
                    issues.append(f"{ruby_type}: {len(matches)}個のルビを処理")
                    if ruby_type == 'aozora_ruby':
                        processed = re.sub(pattern, r'\1', processed)
                    else:
                        processed = re.sub(pattern, r'\1', processed)
            
            elif ruby_type in ['html_ruby', 'html_ruby_complex']:
                # HTMLルビの処理
                matches = re.findall(pattern, processed)
                if matches:
                    self.stats.ruby_processed += len(matches)
                    issues.append(f"{ruby_type}: {len(matches)}個のHTMLルビを処理")
                    processed = re.sub(pattern, r'\1', processed)
            
            else:
                # その他のルビ記法を除去
                matches = re.findall(pattern, processed)
                if matches:
                    issues.append(f"{ruby_type}: {len(matches)}個の記号を除去")
                    processed = re.sub(pattern, '', processed)
        
        # 残った縦棒の除去
        if '｜' in processed:
            processed = re.sub(r'｜(?![《「])', '', processed)
            issues.append("残った縦棒記号を除去")
        
        return processed, issues
    
    def _handle_special_characters(self, text: str) -> Tuple[str, List[str]]:
        """特殊文字の処理"""
        
        issues = []
        processed = text
        
        # 各カテゴリの特殊文字を処理
        for category, patterns in self.special_char_patterns.items():
            for pattern, replacement in patterns.items():
                matches = re.findall(pattern, processed)
                if matches:
                    self.stats.special_chars_processed += len(matches)
                    issues.append(f"{category}: {len(matches)}個の特殊文字を処理")
                    processed = re.sub(pattern, replacement, processed)
        
        # 制御文字の除去
        control_chars = ''.join([chr(i) for i in range(32) if i not in [9, 10, 13]])  # タブ、改行、復帰以外
        for char in control_chars:
            if char in processed:
                processed = processed.replace(char, '')
                issues.append(f"制御文字を除去: U+{ord(char):04X}")
        
        return processed, issues
    
    def _normalize_punctuation(self, text: str) -> Tuple[str, List[str]]:
        """句読点正規化"""
        
        issues = []
        normalized = text
        
        # 各カテゴリの句読点を正規化（文字クラスを使わない安全な形式）
        for category, patterns in self.punctuation_patterns.items():
            for pattern, replacement in patterns.items():
                if pattern in normalized:
                    count = normalized.count(pattern)
                    if count > 0:
                        issues.append(f"{category}: {count}個の記号を正規化")
                        normalized = normalized.replace(pattern, replacement)
        
        # 連続する句読点の処理（安全な形式）
        consecutive_replacements = [
            ('。。', '。'),
            ('、、', '、'),
            ('！！', '！'),
            ('？？', '？'),
            ('……', '…'),
        ]
        
        for old_pattern, new_pattern in consecutive_replacements:
            while old_pattern in normalized:
                normalized = normalized.replace(old_pattern, new_pattern)
                issues.append(f"連続句読点を正規化: {old_pattern} → {new_pattern}")
        
        return normalized, issues
    
    def _normalize_whitespace(self, text: str) -> Tuple[str, List[str]]:
        """空白・改行の正規化"""
        
        issues = []
        normalized = text
        original_lines = len(text.split('\n'))
        
        # 空白の統一
        whitespace_patterns = {
            r'[ \t]+': ' ',           # 複数の半角空白・タブ → 単一空白
            r'[　\u3000]+': '　',     # 複数の全角空白 → 単一全角空白
            r' 　| 　': '　',         # 半角全角混在 → 全角
            r'　 |　 ': '　',         # 全角半角混在 → 全角
        }
        
        for pattern, replacement in whitespace_patterns.items():
            before_count = len(re.findall(pattern, normalized))
            if before_count > 0:
                self.stats.whitespace_normalized += before_count
                issues.append(f"空白正規化: {before_count}箇所")
                normalized = re.sub(pattern, replacement, normalized)
        
        # 改行の正規化
        if self.config.preserve_line_breaks:
            # 改行を保持しつつ整理
            normalized = re.sub(r'\n\s*\n\s*\n', '\n\n', normalized)  # 3連続以上→2つ
            normalized = re.sub(r'[ \t]+\n', '\n', normalized)         # 行末空白除去
            normalized = re.sub(r'\n[ \t]+', '\n', normalized)         # 行頭空白除去
        else:
            # 改行をすべて空白に変換
            normalized = re.sub(r'\n+', ' ', normalized)
            issues.append("改行を空白に変換")
        
        # 先頭・末尾の空白除去
        stripped = normalized.strip()
        if len(stripped) != len(normalized):
            issues.append("先頭・末尾の空白を除去")
            normalized = stripped
        
        final_lines = len(normalized.split('\n'))
        if original_lines != final_lines:
            issues.append(f"行数変更: {original_lines}→{final_lines}行")
        
        return normalized, issues
    
    def _preserve_text_structure(self, text: str) -> str:
        """テキスト構造の保持"""
        
        # 段落の保持
        paragraphs = text.split('\n\n')
        preserved_paragraphs = []
        
        for paragraph in paragraphs:
            if paragraph.strip():
                # 段落内の構造を保持
                lines = paragraph.split('\n')
                preserved_lines = []
                
                for line in lines:
                    line = line.strip()
                    if line:
                        preserved_lines.append(line)
                
                if preserved_lines:
                    preserved_paragraphs.append('\n'.join(preserved_lines))
        
        return '\n\n'.join(preserved_paragraphs)
    
    def _calculate_cleaning_quality(self, original: str, cleaned: str) -> float:
        """クリーニング品質スコア"""
        
        if not original or not cleaned:
            return 0.0
        
        # 品質指標
        indicators = {
            'length_preservation': min(1.0, len(cleaned) / len(original)),  # 長さ保持
            'content_preservation': self._calculate_content_similarity(original, cleaned),  # 内容保持
            'html_removal': 1.0 if self.stats.html_tags_removed > 0 else 0.8,  # HTML除去
            'ruby_processing': 1.0 if self.stats.ruby_processed > 0 else 0.9,  # ルビ処理
            'special_char_handling': 1.0 if self.stats.special_chars_processed > 0 else 0.9,  # 特殊文字処理
        }
        
        # 重み付け
        weights = {
            'length_preservation': 0.2,
            'content_preservation': 0.4,
            'html_removal': 0.15,
            'ruby_processing': 0.15,
            'special_char_handling': 0.1,
        }
        
        quality_score = sum(indicators[key] * weights[key] for key in weights)
        
        return round(quality_score, 3)
    
    def _calculate_content_similarity(self, text1: str, text2: str) -> float:
        """テキスト内容の類似度計算"""
        
        # 文字レベルの類似度（簡易版）
        chars1 = set(text1)
        chars2 = set(text2)
        
        if not chars1 and not chars2:
            return 1.0
        if not chars1 or not chars2:
            return 0.0
        
        intersection = len(chars1 & chars2)
        union = len(chars1 | chars2)
        
        return intersection / union if union > 0 else 0.0
    
    def clean_batch_texts(self, texts: List[str], config: Optional[CleaningConfig] = None) -> List[Dict[str, Any]]:
        """バッチテキストクリーニング"""
        
        results = []
        total_texts = len(texts)
        
        logger.info(f"🧹 バッチクリーニング開始: {total_texts}件")
        
        for i, text in enumerate(texts):
            try:
                result = self.clean_text_comprehensive(text, config)
                result['batch_index'] = i
                results.append(result)
                
                if (i + 1) % 100 == 0:
                    logger.info(f"📊 進捗: {i + 1}/{total_texts} ({((i + 1) / total_texts * 100):.1f}%)")
                    
            except Exception as e:
                error_result = self._create_error_result(f"テキスト{i}: {e}")
                error_result['batch_index'] = i
                results.append(error_result)
                logger.error(f"❌ バッチ処理エラー (テキスト{i}): {e}")
        
        logger.info(f"✅ バッチクリーニング完了: {len(results)}件処理")
        
        return results
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """空の結果作成"""
        return {
            'original_text': '',
            'cleaned_text': '',
            'config': self.config,
            'stats': self.stats,
            'quality_score': 0.0,
            'issues_found': [],
        }
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """エラー結果作成"""
        result = self._create_empty_result()
        result['error'] = error_message
        return result
    
    def get_cleaning_summary(self) -> Dict[str, Any]:
        """クリーニング概要取得"""
        return {
            'stats': {
                'original_length': self.stats.original_length,
                'cleaned_length': self.stats.cleaned_length,
                'reduction_ratio': round((self.stats.original_length - self.stats.cleaned_length) / self.stats.original_length, 3) if self.stats.original_length > 0 else 0,
                'html_tags_removed': self.stats.html_tags_removed,
                'ruby_processed': self.stats.ruby_processed,
                'special_chars_processed': self.stats.special_chars_processed,
                'whitespace_normalized': self.stats.whitespace_normalized,
            },
            'config': self.config,
        }

def main():
    """高度テキストクリーニングシステムのテスト実行"""
    
    # テスト設定
    config = CleaningConfig(
        preserve_line_breaks=True,
        normalize_whitespace=True,
        remove_html_tags=True,
        process_ruby=True,
        handle_special_chars=True,
        normalize_punctuation=True,
        preserve_structure=True
    )
    
    cleaner = AdvancedTextCleaner(config)
    
    # サンプルテキスト
    sample_text = """
<html><body>
<h1>吾輩は猫である</h1>
<p>　吾輩《わがはい》は猫である。名前はまだ無い。</p>
<ruby>吾輩<rt>わがはい</rt></ruby>は｜猫《ねこ》である。
［＃ここで改行］

&quot;ニャー&quot;と鳴いた。　　　
</body></html>
    """
    
    result = cleaner.clean_text_comprehensive(sample_text)
    
    print("🧹 高度テキストクリーニング結果:")
    print(f"元テキスト長: {len(sample_text)}文字")
    print(f"クリーニング後: {len(result['cleaned_text'])}文字")
    print(f"品質スコア: {result['quality_score']}")
    print(f"検出された問題: {len(result['issues_found'])}件")
    print("\nクリーニング後テキスト:")
    print(f"'{result['cleaned_text']}'")
    
    return result

if __name__ == '__main__':
    main() 