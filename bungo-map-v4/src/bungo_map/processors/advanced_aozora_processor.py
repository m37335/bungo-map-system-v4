#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高度青空文庫処理システム v4
v3の569行システムを移植・強化した包括的テキスト処理
"""

import re
import logging
import unicodedata
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SentenceContext:
    """文脈情報"""
    sentence: str
    before_text: str
    after_text: str
    sentence_index: int
    char_position: int

@dataclass
class DocumentStructure:
    """文書構造情報"""
    title: str
    author: str
    chapters: List[str]
    sections: List[str]
    metadata: Dict[str, str]

@dataclass
class ProcessingStats:
    """処理統計情報"""
    original_chars: int = 0
    processed_chars: int = 0
    sentences_extracted: int = 0
    metadata_removed: int = 0
    ruby_processed: int = 0
    annotations_processed: int = 0

class AdvancedAozoraProcessor:
    """高度青空文庫処理システム v4"""
    
    def __init__(self):
        """初期化"""
        
        # 青空文庫メタデータパターン（v3から拡張）
        self.metadata_patterns = [
            # ナビゲーション
            r'●[^●]+●[^●]*',
            r'図書カード[：:][^\n]*',
            r'作品名[：:][^\n]*',
            r'作品名読み[：:][^\n]*',
            r'著者名[：:][^\n]*',
            r'作家名[：:][^\n]*',
            r'作家名読み[：:][^\n]*',
            
            # データ情報
            r'分類[：:][^\n]*',
            r'初出[：:][^\n]*',
            r'作品について[：:][^\n]*',
            r'文字遣い種別[：:][^\n]*',
            r'備考[：:][^\n]*',
            r'人物について[：:][^\n]*',
            r'生年[：:][^\n]*',
            r'没年[：:][^\n]*',
            
            # ファイル情報
            r'\[ファイルの.*?\]',
            r'いますぐ.*?で読む',
            r'XHTML版.*?',
            r'ファイル作成日[：:][^\n]*',
            r'最終更新日[：:][^\n]*',
            
            # 青空文庫特有のメタデータ
            r'【[^】]*について】[^】]*',        # 【テキスト中に現れる記号について】
            r'【[^】]*】[^】]*',               # その他の【】囲み
            r'-------+[^-]*-------+',        # 区切り線
            r'［＃[^］]*］',                  # 編集注
            r'《[^》]*》',                   # ルビの説明
            r'（例）[^\n]*',                 # 例示
            r'No\.\d+',
            r'NDC \d+',
            r'ローマ字表記[：:][^\n]*',
            r'［.*?］',
            r'青空文庫.*',
            
            # 区切り文字
            r'[-=]{3,}',
            r'[*＊]{3,}',
            
            # v4追加: 更なるメタデータパターン
            r'底本[：:][^\n]*',
            r'底本の親本[：:][^\n]*',
            r'入力[：:][^\n]*',
            r'校正[：:][^\n]*',
            r'プルーフ[：:][^\n]*',
            r'※このファイル[^\n]*',
            r'新潮文庫[^\n]*',
            r'日本近代文学館[^\n]*',
            r'複刻[^\n]*',
            r'[発刊]行[：:][^\n]*',
        ]
        
        # ルビ・注釈パターン（拡張）
        self.ruby_patterns = [
            r'《[^》]*》',           # 標準ルビ
            r'｜[^《]*《[^》]*》',    # ルビ（縦棒付き）
            r'［＃[^］]*］',         # 編集注
            r'〔[^〕]*〕',           # 編集注（角括弧）
            r'〈[^〉]*〉',           # 編集注（山括弧）
            r'※[^※]*※',           # 注記（米印）
            r'＊[^＊]*＊',           # 注記（アスタリスク）
        ]
        
        # 本文開始の指標（拡張）
        self.content_start_indicators = [
            # 明確な本文開始
            r'^[　\s]*[一二三四五六七八九十]{1,3}[　\s]*$',           # 章番号（漢数字）
            r'^[　\s]*[１２３４５６７８９０]{1,3}[　\s]*$',         # 章番号（全角数字）
            r'^[　\s]*[1-9][0-9]*[　\s]*$',                      # 章番号（半角数字）
            r'^[　\s]*第[一二三四五六七八九十１-９0-9]+[章節部編巻][　\s]*$', # 第○章
            r'^[　\s]*[序破急][　\s]*$',                         # 序・破・急
            r'^[　\s]*[はじめにおわりにあとがき序章終章][　\s]*$',      # 前書き・後書き
            r'^[　\s]*その[一二三四五六七八九十１-９0-9]+[　\s]*$',  # その一
            r'^[　\s]*[上中下前後左右][巻編部][　\s]*$',            # 上巻・下巻等
            
            # 物語的な開始
            r'^[　\s]*[「『][^」』]*[」』]',                      # 台詞から始まる
            r'^[　\s]*[私僕俺わたし彼彼女]',                      # 一人称から始まる
            r'^[　\s]*[親父母親お父さんお母さん兄弟姉妹]',             # 家族関係
            r'^[　\s]*その[日時頃朝夜晩昼夕方明方]',                # 時間表現
            r'^[　\s]*[昔昨日今日明日先日最近当時]',                # 時間表現
            r'^[　\s]*ある[日時晴雨朝夜夕方]',                    # ある日
            r'^[　\s]*[明治大正昭和平成令和][一二三四五六七八九十元０-９0-9]+年', # 年号
            r'^[　\s]*[十二三四五六七八九０-９0-9]+[年月日時分秒]',   # 日付・時刻
            
            # 固有名詞から始まる
            r'^[　\s]*[頼山陽夏目漱石芥川龍之介太宰治][　\s]',        # 文豪名
            r'^[　\s]*[A-Z][a-z]+[　\s]',                       # 外国人名
            r'^[　\s]*[東京大阪京都名古屋横浜神戸福岡][　\s]',        # 地名
            
            # 小説特有の開始
            r'^[　\s]*[雨雪風雲雷][が]',                         # 天候から始まる
            r'^[　\s]*[春夏秋冬][が]',                           # 季節から始まる
            r'^[　\s]*[朝昼夜夕方明方][が]',                     # 時間帯から始まる
        ]
        
        # 文書終了の指標
        self.content_end_indicators = [
            r'底本[：:]',
            r'底本の親本[：:]',
            r'入力[：:]',
            r'校正[：:]',
            r'プルーフ[：:]',
            r'※このファイル',
            r'青空文庫',
            r'---+',
            r'===+',
            r'[0-9]{4}年[0-9]{1,2}月',
            r'複刻',
            r'新潮文庫',
            r'日本近代文学館',
        ]
        
        # 処理統計
        self.stats = ProcessingStats()
        
        logger.info("📚 高度青空文庫処理システム v4 初期化完了")
    
    def process_aozora_document(self, raw_content: str, preserve_structure: bool = True) -> Dict[str, Any]:
        """青空文庫文書の包括的処理"""
        
        if not raw_content or len(raw_content) < 100:
            logger.warning("コンテンツが短すぎます")
            return self._create_empty_result()
        
        # 統計初期化
        self.stats.original_chars = len(raw_content)
        
        result = {
            'raw_content': raw_content,
            'processed_content': '',
            'sentences': [],
            'structure': None,
            'metadata': {},
            'stats': None,
            'quality_score': 0.0
        }
        
        try:
            # 1. エンコーディング正規化
            normalized_content = self._normalize_encoding(raw_content)
            
            # 2. 文書構造解析
            if preserve_structure:
                structure = self._analyze_document_structure(normalized_content)
                result['structure'] = structure
                result['metadata'] = structure.metadata
            
            # 3. メタデータ抽出・除去
            cleaned_content = self._advanced_metadata_removal(normalized_content)
            
            # 4. 本文抽出
            main_content = self._extract_main_content_advanced(cleaned_content)
            
            # 5. ルビ・注釈の高度処理
            processed_content = self._advanced_ruby_processing(main_content)
            
            # 6. 文書構造保持クリーニング
            processed_content = self._structure_aware_cleaning(processed_content)
            
            # 7. 高度文分割
            sentences = self._advanced_sentence_splitting(processed_content)
            
            # 8. 品質評価
            quality_score = self._calculate_quality_score(raw_content, processed_content, sentences)
            
            # 結果セット
            result.update({
                'processed_content': processed_content,
                'sentences': sentences,
                'quality_score': quality_score
            })
            
            # 統計更新
            self.stats.processed_chars = len(processed_content)
            self.stats.sentences_extracted = len(sentences)
            result['stats'] = self.stats
            
            logger.info(f"📖 文書処理完了: {self.stats.original_chars}→{self.stats.processed_chars}文字, {len(sentences)}文抽出")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 文書処理エラー: {e}")
            return self._create_error_result(str(e))
    
    def _normalize_encoding(self, content: str) -> str:
        """エンコーディング・文字コード正規化"""
        
        # Unicode正規化
        normalized = unicodedata.normalize('NFKC', content)
        
        # 青空文庫特有の文字変換
        char_replacements = {
            # 旧字体→新字体
            '國': '国', '學': '学', '會': '会', '來': '来',
            '時': '時', '實': '実', '變': '変', '經': '経',
            
            # 異体字統一
            '髙': '高', '﨑': '崎', '邊': '辺', '澤': '沢',
            
            # 句読点統一
            '、': '、', '。': '。', '！': '！', '？': '？',
            
            # 括弧統一
            '（': '（', '）': '）', '［': '［', '］': '］',
            
            # 空白統一
            '\u3000': '　',  # 全角空白
            '\u00A0': '　',  # ノーブレークスペース
        }
        
        for old_char, new_char in char_replacements.items():
            normalized = normalized.replace(old_char, new_char)
        
        # 改行コード統一
        normalized = re.sub(r'\r\n|\r', '\n', normalized)
        
        return normalized
    
    def _analyze_document_structure(self, content: str) -> DocumentStructure:
        """文書構造の詳細解析"""
        
        lines = content.split('\n')
        
        structure = DocumentStructure(
            title="",
            author="",
            chapters=[],
            sections=[],
            metadata={}
        )
        
        # メタデータ抽出
        for line in lines[:50]:  # 最初の50行をメタデータ候補として検査
            line = line.strip()
            
            # タイトル抽出
            if not structure.title and re.match(r'^作品名[：:]\s*(.+)$', line):
                structure.title = re.sub(r'^作品名[：:]\s*', '', line).strip()
            
            # 著者抽出
            if not structure.author and re.match(r'^著者名[：:]\s*(.+)$', line):
                structure.author = re.sub(r'^著者名[：:]\s*', '', line).strip()
            
            # その他メタデータ
            metadata_patterns = {
                'classification': r'^分類[：:]\s*(.+)$',
                'first_published': r'^初出[：:]\s*(.+)$',
                'character_type': r'^文字遣い種別[：:]\s*(.+)$',
                'notes': r'^備考[：:]\s*(.+)$',
            }
            
            for key, pattern in metadata_patterns.items():
                match = re.match(pattern, line)
                if match:
                    structure.metadata[key] = match.group(1).strip()
        
        # 章・節構造の抽出
        in_main_content = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 本文開始の判定
            if not in_main_content:
                for pattern in self.content_start_indicators:
                    if re.match(pattern, line):
                        in_main_content = True
                        break
            
            if in_main_content:
                # 章の検出
                chapter_patterns = [
                    r'^[　\s]*第[一二三四五六七八九十１-９0-9]+[章編部巻][　\s]*(.*)$',
                    r'^[　\s]*[一二三四五六七八九十]{1,3}[　\s]*(.*)$',
                    r'^[　\s]*[１２３４５６７８９０]{1,3}[　\s]*(.*)$',
                ]
                
                for pattern in chapter_patterns:
                    match = re.match(pattern, line)
                    if match:
                        structure.chapters.append(line)
                        break
                
                # 節の検出
                section_patterns = [
                    r'^[　\s]*その[一二三四五六七八九十１-９0-9]+[　\s]*(.*)$',
                    r'^[　\s]*[序破急][　\s]*(.*)$',
                ]
                
                for pattern in section_patterns:
                    match = re.match(pattern, line)
                    if match:
                        structure.sections.append(line)
                        break
        
        logger.info(f"📖 文書構造解析: タイトル='{structure.title}', 著者='{structure.author}', 章={len(structure.chapters)}個")
        
        return structure
    
    def _advanced_metadata_removal(self, content: str) -> str:
        """高度メタデータ除去"""
        
        # 区切り線による分割を優先
        sections = re.split(r'\n-{5,}\n', content)
        
        if len(sections) > 1:
            logger.info(f"🔍 区切り線による分割: {len(sections)}セクション")
            main_section = sections[-1]
        else:
            main_section = content
        
        # 段階的メタデータ除去
        cleaned = main_section
        
        # 1. 明確なメタデータパターン除去
        for pattern in self.metadata_patterns:
            before_len = len(cleaned)
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE | re.IGNORECASE)
            if len(cleaned) < before_len:
                self.stats.metadata_removed += 1
        
        # 2. 行単位でのメタデータ除去
        lines = cleaned.split('\n')
        content_lines = []
        in_content = False
        
        for line in lines:
            original_line = line
            line = line.strip()
            
            # 空行は保持
            if not line:
                if in_content:
                    content_lines.append('')
                continue
            
            # メタデータ行の判定
            if not in_content and self._is_metadata_line(line):
                continue
            
            # 本文開始の判定
            if not in_content:
                for pattern in self.content_start_indicators:
                    if re.match(pattern, line):
                        in_content = True
                        break
                
                # ある程度の文章量がある行で、メタデータっぽくない行を本文開始とみなす
                if not in_content and len(line) > 20 and not self._is_metadata_line(line):
                    in_content = True
            
            # 本文終了の判定
            if in_content:
                for pattern in self.content_end_indicators:
                    if re.search(pattern, line):
                        break
                else:
                    content_lines.append(original_line)
                    continue
                break
        
        cleaned = '\n'.join(content_lines)
        
        # 3. 最終クリーニング
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = re.sub(r'[　\s]{3,}', '　', cleaned)
        
        return cleaned.strip()
    
    def _extract_main_content_advanced(self, content: str) -> str:
        """高度本文抽出"""
        
        lines = content.split('\n')
        
        # 本文範囲の特定
        start_index = self._find_content_start_advanced(lines)
        end_index = self._find_content_end_advanced(lines)
        
        if start_index >= 0 and end_index > start_index:
            main_lines = lines[start_index:end_index]
            logger.info(f"📍 本文範囲特定: 行{start_index}〜{end_index} ({end_index - start_index}行)")
        else:
            main_lines = lines
            logger.warning("⚠️ 本文範囲特定失敗、全体を対象とします")
        
        return '\n'.join(main_lines)
    
    def _find_content_start_advanced(self, lines: List[str]) -> int:
        """高度本文開始位置特定"""
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # 本文開始指標の確認
            for pattern in self.content_start_indicators:
                if re.match(pattern, line):
                    logger.info(f"📍 本文開始位置特定: 行{i} - {line[:50]}...")
                    return i
            
            # 推定的本文開始
            if (len(line) > 30 and 
                not self._is_metadata_line(line) and
                not re.match(r'^[A-Za-z\s]+$', line) and
                '：' not in line and
                'について' not in line):
                
                logger.info(f"📍 推定本文開始: 行{i} - {line[:50]}...")
                return i
        
        return 0
    
    def _find_content_end_advanced(self, lines: List[str]) -> int:
        """高度本文終了位置特定"""
        
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if not line:
                continue
            
            # 本文終了指標の確認
            for pattern in self.content_end_indicators:
                if re.search(pattern, line):
                    logger.info(f"📍 本文終了位置特定: 行{i} - {line[:50]}...")
                    return i
        
        return len(lines)
    
    def _advanced_ruby_processing(self, content: str) -> str:
        """高度ルビ・注釈処理"""
        
        processed = content
        
        # 1. ルビの詳細解析・処理
        ruby_count = 0
        
        # 標準ルビ処理: ｜漢字《かんじ》 → 漢字
        ruby_matches = re.findall(r'｜([^《]+)《[^》]+》', processed)
        ruby_count += len(ruby_matches)
        processed = re.sub(r'｜([^《]+)《[^》]+》', r'\1', processed)
        
        # 自動ルビ処理: 漢字《かんじ》 → 漢字
        auto_ruby_matches = re.findall(r'([一-龯]+)《[^》]+》', processed)
        ruby_count += len(auto_ruby_matches)
        processed = re.sub(r'([一-龯]+)《[^》]+》', r'\1', processed)
        
        # 2. 注釈の高度処理
        annotation_count = 0
        
        # 編集注記の処理
        annotation_patterns = [
            (r'［＃[^］]*］', ''),           # 編集注
            (r'〔[^〕]*〕', ''),             # 編集注（角括弧）
            (r'〈[^〉]*〉', ''),             # 編集注（山括弧）
            (r'※[^※\n]*※', ''),           # 注記（米印）
            (r'＊[^＊\n]*＊', ''),           # 注記（アスタリスク）
        ]
        
        for pattern, replacement in annotation_patterns:
            matches = re.findall(pattern, processed)
            annotation_count += len(matches)
            processed = re.sub(pattern, replacement, processed)
        
        # 3. 残ったルビ記号の除去
        processed = re.sub(r'《[^》]*》', '', processed)
        processed = re.sub(r'｜(?![《「])', '', processed)
        
        # 統計更新
        self.stats.ruby_processed = ruby_count
        self.stats.annotations_processed = annotation_count
        
        logger.info(f"🎋 ルビ・注釈処理: ルビ{ruby_count}個, 注釈{annotation_count}個除去")
        
        return processed
    
    def _structure_aware_cleaning(self, content: str) -> str:
        """文書構造を考慮したクリーニング"""
        
        # 1. 段落構造の保持
        paragraphs = content.split('\n\n')
        cleaned_paragraphs = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
            
            # 段落内クリーニング
            cleaned_para = self._clean_paragraph(paragraph)
            if cleaned_para:
                cleaned_paragraphs.append(cleaned_para)
        
        # 2. 文字レベルクリーニング
        cleaned = '\n\n'.join(cleaned_paragraphs)
        
        # 特殊文字の正規化
        cleaned = re.sub(r'[　\u3000]+', '　', cleaned)  # 全角空白統一
        cleaned = re.sub(r'[、]{2,}', '、', cleaned)    # 連続読点
        cleaned = re.sub(r'[。]{2,}', '。', cleaned)    # 連続句点
        cleaned = re.sub(r'[！]{2,}', '！', cleaned)    # 連続感嘆符
        cleaned = re.sub(r'[？]{2,}', '？', cleaned)    # 連続疑問符
        
        # 3. 改行の正規化
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)  # 3連続以上の改行を2つに
        cleaned = re.sub(r'[ \t]+\n', '\n', cleaned)         # 行末空白除去
        
        return cleaned.strip()
    
    def _clean_paragraph(self, paragraph: str) -> str:
        """段落単位のクリーニング"""
        
        lines = paragraph.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # メタデータ行のスキップ
            if self._is_metadata_line(line.strip()):
                continue
            
            # 行内クリーニング
            cleaned_line = line.strip()
            
            # 短すぎる行のフィルタリング（ただし章番号等は保持）
            if len(cleaned_line) < 3 and not re.match(r'^[一二三四五六七八九十１-９0-9]+$', cleaned_line):
                continue
            
            cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _advanced_sentence_splitting(self, content: str) -> List[str]:
        """高度文分割システム"""
        
        if not content:
            return []
        
        sentences = []
        
        # 1. 句点ベース分割（従来手法の強化）
        if '。' in content:
            sentences.extend(self._split_by_periods(content))
        
        # 2. 句点なし文書の処理（詩歌・散文詩等）
        else:
            sentences.extend(self._split_poetic_content(content))
        
        # 3. 長文の強制分割
        final_sentences = []
        for sentence in sentences:
            if len(sentence) > 500:  # 500文字以上の超長文
                sub_sentences = self._force_split_long_sentence(sentence)
                final_sentences.extend(sub_sentences)
            else:
                final_sentences.append(sentence)
        
        # 4. 最終フィルタリング・クリーニング
        cleaned_sentences = self._filter_and_clean_sentences(final_sentences)
        
        logger.info(f"📝 文分割完了: {len(cleaned_sentences)}文抽出")
        
        return cleaned_sentences
    
    def _split_by_periods(self, content: str) -> List[str]:
        """句点ベース分割（強化版）"""
        
        # 句点での分割（句点を保持）
        parts = re.split(r'(。)', content)
        
        sentences = []
        current_sentence = ""
        
        for part in parts:
            if part == '。':
                if current_sentence.strip():
                    complete_sentence = (current_sentence + part).strip()
                    if len(complete_sentence) >= 5:
                        sentences.append(complete_sentence)
                    elif sentences:  # 短すぎる場合は前の文に結合
                        sentences[-1] += complete_sentence
                current_sentence = ""
            else:
                current_sentence += part
        
        # 最後の部分の処理
        if current_sentence.strip():
            final_text = current_sentence.strip()
            if len(final_text) >= 5:
                sentences.append(final_text)
            elif sentences:
                sentences[-1] += final_text
        
        return sentences
    
    def _split_poetic_content(self, content: str) -> List[str]:
        """詩歌コンテンツの分割"""
        
        sentences = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # メタデータ行をスキップ
            if self._is_metadata_line(line):
                continue
            
            # 長い行の分割
            if len(line) > 200:
                # 全角空白で分割
                if '　' in line:
                    parts = line.split('　')
                    for part in parts:
                        part = part.strip()
                        if len(part) >= 5:
                            sentences.append(part)
                else:
                    # 句読点で分割
                    sub_sentences = self._split_by_punctuation(line)
                    sentences.extend(sub_sentences)
            else:
                # 短い行はそのまま
                if len(line) >= 5:
                    sentences.append(line)
        
        return sentences
    
    def _split_by_punctuation(self, text: str) -> List[str]:
        """句読点による分割"""
        
        # 文末記号での分割を優先
        parts = re.split(r'([。！？])', text)
        
        sentences = []
        current_sentence = ""
        
        for part in parts:
            if re.match(r'[。！？]', part):
                if current_sentence.strip():
                    complete = (current_sentence + part).strip()
                    if len(complete) >= 5:
                        sentences.append(complete)
                current_sentence = ""
            else:
                current_sentence += part
        
        # 残りの部分
        if current_sentence.strip() and len(current_sentence.strip()) >= 5:
            if len(current_sentence) > 150:
                # まだ長い場合は読点で分割
                comma_parts = current_sentence.split('、')
                for comma_part in comma_parts:
                    comma_part = comma_part.strip()
                    if len(comma_part) >= 5:
                        sentences.append(comma_part)
            else:
                sentences.append(current_sentence.strip())
        
        return sentences if sentences else [text]
    
    def _force_split_long_sentence(self, sentence: str) -> List[str]:
        """超長文の強制分割"""
        
        # 1. 句読点での分割を試行
        punctuation_split = self._split_by_punctuation(sentence)
        if len(punctuation_split) > 1:
            return punctuation_split
        
        # 2. 接続詞での分割
        conjunction_patterns = [
            r'(そして)', r'(しかし)', r'(だが)', r'(ところが)', r'(すると)',
            r'(それで)', r'(そこで)', r'(ただし)', r'(なお)', r'(また)',
            r'(さらに)', r'(一方)', r'(他方)', r'(例えば)', r'(つまり)'
        ]
        
        for pattern in conjunction_patterns:
            parts = re.split(pattern, sentence)
            if len(parts) > 2:
                result = []
                current = ""
                for i, part in enumerate(parts):
                    current += part
                    if i % 2 == 0 and len(current) > 100:  # 接続詞の前で区切り
                        result.append(current.strip())
                        current = ""
                if current.strip():
                    result.append(current.strip())
                return result
        
        # 3. 長さベースの強制分割
        if len(sentence) > 300:
            mid_point = len(sentence) // 2
            # 適切な分割点を探す
            for i in range(mid_point - 50, mid_point + 50):
                if i < len(sentence) and sentence[i] in '、。　':
                    return [sentence[:i+1].strip(), sentence[i+1:].strip()]
            
            # 最後の手段：中央で分割
            return [sentence[:mid_point].strip(), sentence[mid_point:].strip()]
        
        return [sentence]
    
    def _filter_and_clean_sentences(self, sentences: List[str]) -> List[str]:
        """文の最終フィルタリング・クリーニング"""
        
        cleaned_sentences = []
        
        for sentence in sentences:
            cleaned = sentence.strip()
            
            # フィルタリング条件
            if (cleaned and 
                len(cleaned) >= 5 and 
                len(cleaned) <= 800 and  # 最大文字数制限
                not re.match(r'^[\s\n　]*$', cleaned) and
                not self._is_metadata_line(cleaned)):
                
                # 文レベルクリーニング
                cleaned = re.sub(r'\s+', ' ', cleaned)
                cleaned = re.sub(r'　+', '　', cleaned)
                cleaned = re.sub(r'[、]{2,}', '、', cleaned)
                cleaned = re.sub(r'[。]{2,}', '。', cleaned)
                
                cleaned_sentences.append(cleaned)
        
        return cleaned_sentences
    
    def _is_metadata_line(self, line: str) -> bool:
        """メタデータ行の判定（拡張版）"""
        
        metadata_indicators = [
            r'^底本[：:]',
            r'^底本の親本[：:]',
            r'^初出[：:]',
            r'^※このファイル',
            r'青空文庫',
            r'新潮文庫',
            r'日本近代文学館',
            r'^\d{4}（[^）]+）年',
            r'^No\.\d+',
            r'^NDC \d+',
            r'発行$',
            r'刊行$',
            r'複刻',
            r'^入力[：:]',
            r'^校正[：:]',
            r'^プルーフ[：:]',
            r'^ファイル作成日[：:]',
            r'^最終更新日[：:]',
            r'^【[^】]*について】',
            r'^-------+$',
            r'^===+$',
            r'作品について',
            r'人物について',
            r'テキスト中に現れる記号について',
        ]
        
        for pattern in metadata_indicators:
            if re.search(pattern, line):
                return True
        
        return False
    
    def get_sentence_context_advanced(self, sentences: List[str], target_index: int, 
                                    context_length: int = 2) -> SentenceContext:
        """高度文脈取得"""
        
        if not sentences or target_index < 0 or target_index >= len(sentences):
            return SentenceContext("", "", "", -1, -1)
        
        # メイン文
        main_sentence = sentences[target_index]
        
        # 前文脈（拡張）
        before_start = max(0, target_index - context_length)
        before_sentences = sentences[before_start:target_index]
        before_text = "".join(before_sentences)
        
        # 後文脈（拡張）
        after_end = min(len(sentences), target_index + context_length + 1)
        after_sentences = sentences[target_index + 1:after_end]
        after_text = "".join(after_sentences)
        
        # 文字位置計算
        char_position = sum(len(s) for s in sentences[:target_index])
        
        return SentenceContext(
            sentence=main_sentence,
            before_text=before_text,
            after_text=after_text,
            sentence_index=target_index,
            char_position=char_position
        )
    
    def _calculate_quality_score(self, raw_content: str, processed_content: str, 
                               sentences: List[str]) -> float:
        """処理品質スコア計算"""
        
        if not raw_content or not processed_content:
            return 0.0
        
        # 各種品質指標
        indicators = {
            'length_ratio': min(1.0, len(processed_content) / len(raw_content)),  # 長さ比率
            'sentence_count': min(1.0, len(sentences) / 100),  # 文数（100文で満点）
            'avg_sentence_length': 0.0,  # 平均文長
            'metadata_removal': 1.0 if self.stats.metadata_removed > 0 else 0.5,  # メタデータ除去
            'ruby_processing': 1.0 if self.stats.ruby_processed > 0 else 0.8,  # ルビ処理
        }
        
        # 平均文長計算
        if sentences:
            avg_length = sum(len(s) for s in sentences) / len(sentences)
            indicators['avg_sentence_length'] = min(1.0, avg_length / 50)  # 50文字で満点
        
        # 重み付き品質スコア
        weights = {
            'length_ratio': 0.3,
            'sentence_count': 0.2,
            'avg_sentence_length': 0.2,
            'metadata_removal': 0.2,
            'ruby_processing': 0.1,
        }
        
        quality_score = sum(indicators[key] * weights[key] for key in weights)
        
        return round(quality_score, 3)
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """空の結果作成"""
        return {
            'raw_content': '',
            'processed_content': '',
            'sentences': [],
            'structure': None,
            'metadata': {},
            'stats': self.stats,
            'quality_score': 0.0
        }
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """エラー結果作成"""
        result = self._create_empty_result()
        result['error'] = error_message
        return result
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """処理統計の取得"""
        return {
            'original_chars': self.stats.original_chars,
            'processed_chars': self.stats.processed_chars,
            'reduction_ratio': round((self.stats.original_chars - self.stats.processed_chars) / self.stats.original_chars, 3) if self.stats.original_chars > 0 else 0,
            'sentences_extracted': self.stats.sentences_extracted,
            'metadata_removed': self.stats.metadata_removed,
            'ruby_processed': self.stats.ruby_processed,
            'annotations_processed': self.stats.annotations_processed,
        }

def main():
    """高度青空文庫処理システムのテスト実行"""
    processor = AdvancedAozoraProcessor()
    
    # サンプルテキストでのテスト
    sample_text = """
作品名：羅生門
著者名：芥川龍之介
分類：近代文学
初出：帝国文学、大正4年11月
---------------------------------

　ある日の暮方の事である。一人の下人が、羅生門の下で雨やみを待っていた。
　広い門の下には、この男のほかに誰もいない。ただ、所々丹塗の剥げた、大きな円柱に、蟋蟀が一匹とまっている。

底本：筑摩書房版『芥川龍之介全集』
入力：青空文庫
校正：青空文庫
    """
    
    result = processor.process_aozora_document(sample_text)
    
    print(f"処理結果:")
    print(f"  品質スコア: {result['quality_score']}")
    print(f"  文数: {len(result['sentences'])}")
    print(f"  処理統計: {processor.get_processing_statistics()}")
    
    return result

if __name__ == '__main__':
    main() 