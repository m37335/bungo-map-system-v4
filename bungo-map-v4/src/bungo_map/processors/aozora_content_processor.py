#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📚 青空文庫コンテンツ処理システム
メタデータ除去、本文抽出、適切な文分割と文脈取得

Features:
- 青空文庫メタデータの完全除去
- 本文の正確な抽出
- 自然な文分割
- 地名周辺の適切な文脈取得
- 注釈・ルビの処理
"""

import re
import logging
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SentenceContext:
    """文脈情報"""
    sentence: str           # メイン文
    before_text: str       # 前文脈
    after_text: str        # 後文脈
    sentence_index: int    # 文番号
    char_position: int     # 文字位置

class AozoraContentProcessor:
    """青空文庫コンテンツ処理クラス"""
    
    def __init__(self):
        """初期化"""
        
        # 青空文庫メタデータパターン
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
        ]
        
        # ルビ・注釈パターン
        self.ruby_patterns = [
            r'《[^》]*》',           # ルビ
            r'｜[^《]*《[^》]*》',    # ルビ（縦棒付き）
            r'［＃[^］]*］',         # 注釈
            r'〔[^〕]*〕',           # 編集注
        ]
        
        # 本文開始の指標
        self.content_start_indicators = [
            # 明確な本文開始
            r'^[　\s]*一[　\s]*$',           # 章番号
            r'^[　\s]*１[　\s]*$',
            r'^[　\s]*第.*章[　\s]*$',       # 第○章
            r'^[　\s]*序[　\s]*$',           # 序
            r'^[　\s]*はじめに[　\s]*$',     # はじめに
            r'^[　\s]*その一[　\s]*$',       # その一
            r'^[　\s]*上[　\s]*$',           # 上巻
            r'^[　\s]*下[　\s]*$',           # 下巻
            
            # 物語的な開始
            r'^[　\s]*[「『][^」』]*[」』]',  # 台詞から始まる
            r'^[　\s]*[私僕俺わたし]',       # 一人称から始まる
            r'^[　\s]*[親父母親お父さんお母さん]', # 家族関係
            r'^[　\s]*その[日時頃]',         # 時間表現
            r'^[　\s]*[昔昨日今日明日]',     # 時間表現
            r'^[　\s]*ある[日時晴雨]',       # ある日
            r'^[　\s]*[十二三四五六七八九０-９][年月日時]', # 日付
            
            # 固有名詞から始まる
            r'^[　\s]*[頼山陽]',            # 人名（この作品特有）
            r'^[　\s]*[A-Z][a-z]+',        # 外国人名
        ]
        
        print("📚 青空文庫コンテンツ処理システム初期化完了")
    
    def extract_main_content(self, raw_content: str) -> str:
        """青空文庫の生データから本文を抽出"""
        
        if not raw_content or len(raw_content) < 100:
            logger.warning("コンテンツが短すぎます")
            return ""
        
        # 1. メタデータの除去
        cleaned = self._remove_metadata(raw_content)
        
        # 2. 本文開始位置の特定
        main_content = self._find_main_content_start(cleaned)
        
        # 3. ルビ・注釈の処理
        main_content = self._clean_ruby_and_annotations(main_content)
        
        # 4. 基本的なクリーニング
        main_content = self._basic_cleaning(main_content)
        
        logger.info(f"📖 本文抽出完了: {len(raw_content)}文字 → {len(main_content)}文字")
        
        return main_content
    
    def _remove_metadata(self, content: str) -> str:
        """メタデータの除去（本文を保護）"""
        
        # まず明確な区切り線でメタデータセクションを特定
        sections = re.split(r'\n-{5,}\n', content)
        
        if len(sections) > 1:
            # 区切り線がある場合、最後のセクションを本文として扱う
            logger.info(f"🔍 区切り線による分割: {len(sections)}セクション")
            main_section = sections[-1]
        else:
            main_section = content
        
        # 軽微なメタデータのみ除去
        cleaned = main_section
        
        # 安全なメタデータパターンのみ除去
        safe_patterns = [
            r'●[^●]+●[^●]*',
            r'図書カード[：:][^\n]*',
            r'No\.\d+',
            r'NDC \d+',
            r'\[ファイルの.*?\]',
            r'いますぐ.*?で読む',
            r'XHTML版.*?',
        ]
        
        for pattern in safe_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE | re.IGNORECASE)
        
        # 連続する改行・空白の整理
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = re.sub(r'[　\s]{3,}', '　', cleaned)
        
        return cleaned.strip()
    
    def _find_main_content_start(self, content: str) -> str:
        """本文開始位置の特定"""
        
        lines = content.split('\n')
        start_index = 0
        
        # まず明確なメタデータ終了位置を探す
        metadata_end = self._find_metadata_end(lines)
        if metadata_end > 0:
            start_index = metadata_end
            logger.info(f"📍 メタデータ終了位置: 行{metadata_end}")
        
        # 本文開始の指標を探す
        for i in range(start_index, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
                
            # 本文開始指標の確認
            for pattern in self.content_start_indicators:
                if re.match(pattern, line):
                    start_index = i
                    logger.info(f"📍 本文開始位置特定: 行{i} - {line[:30]}...")
                    break
            
            if start_index > i:
                break
            
            # ある程度の文章量がある行で、メタデータっぽくない行を本文開始とみなす
            if (len(line) > 20 and 
                not any(meta in line for meta in ['作品', '著者', '分類', '初出', '【', '】', '（例）', '-------']) and
                not re.match(r'^[A-Za-z\s]+$', line) and  # 英語のみの行は除外
                '：' not in line and
                'について' not in line):
                start_index = i
                logger.info(f"📍 推定本文開始: 行{i} - {line[:30]}...")
                break
        
        # 本文部分を抽出
        main_lines = lines[start_index:]
        return '\n'.join(main_lines)
    
    def _find_metadata_end(self, lines: List[str]) -> int:
        """メタデータ終了位置の特定"""
        
        # 区切り線を探す
        for i, line in enumerate(lines):
            line = line.strip()
            
            # 明確な区切り線
            if re.match(r'^[-=]{5,}$', line):
                return i + 1
            
            # 【】で囲まれたセクションの終了
            if line.endswith('】') and i < len(lines) - 1:
                next_line = lines[i + 1].strip()
                if re.match(r'^[-=]{3,}$', next_line):
                    return i + 2
        
        return 0
    
    def _clean_ruby_and_annotations(self, content: str) -> str:
        """ルビ・注釈の処理"""
        
        cleaned = content
        
        # ルビ・注釈パターンを除去
        for pattern in self.ruby_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # 縦棒だけが残った場合の処理
        cleaned = re.sub(r'｜(?![《「])', '', cleaned)
        
        return cleaned
    
    def _basic_cleaning(self, content: str) -> str:
        """基本的なクリーニング"""
        
        # 不要な文字の除去
        cleaned = content
        
        # 特殊な空白の統一
        cleaned = re.sub(r'[　\u3000]+', '　', cleaned)
        
        # 連続する句読点の整理
        cleaned = re.sub(r'[。]{2,}', '。', cleaned)
        cleaned = re.sub(r'[、]{2,}', '、', cleaned)
        
        # 空行の整理
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        
        return cleaned.strip()
    
    def split_into_sentences(self, content: str) -> List[str]:
        """多様な文体対応の文分割（超長文対策版）"""
        
        if not content:
            return []
        
        sentences = []
        
        # 1. まず句点（。）がある場合の処理
        if '。' in content:
            # 従来の句点ベース分割
            potential_sentences = re.split(r'(。)', content)
            
            current_sentence = ""
            for i, part in enumerate(potential_sentences):
                if part == '。':
                    if current_sentence.strip():
                        complete_sentence = (current_sentence + part).strip()
                        if len(complete_sentence) >= 5:
                            sentences.append(complete_sentence)
                        elif sentences:
                            sentences[-1] += complete_sentence
                    current_sentence = ""
                else:
                    current_sentence += part
            
            # 最後の部分処理
            if current_sentence.strip():
                final_text = current_sentence.strip()
                if len(final_text) >= 5:
                    sentences.append(final_text)
                elif sentences:
                    sentences[-1] += final_text
        
        # 2. 句点がない場合（短歌・俳句・散文詩など）
        else:
            # 改行ベース分割を優先（超長文対策）
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # 空行や短すぎる行をスキップ
                if not line or len(line) < 5:
                    continue
                
                # メタデータ行をスキップ
                if self._is_metadata_line(line):
                    continue
                
                # 超長文の強制分割（1000文字以上）
                if len(line) > 1000:
                    # 全角空白で分割を試行
                    if '　' in line:
                        parts = line.split('　')
                        for part in parts:
                            part = part.strip()
                            if len(part) >= 5 and not self._is_metadata_line(part):
                                # さらに長い場合は句読点で分割
                                if len(part) > 200:
                                    sub_sentences = self._force_split_long_text(part)
                                    sentences.extend(sub_sentences)
                                else:
                                    sentences.append(part)
                    else:
                        # 句読点で強制分割
                        sub_sentences = self._force_split_long_text(line)
                        sentences.extend(sub_sentences)
                
                # 通常の長さの行（短歌・俳句等）
                elif len(line) <= 200:
                    # 全角空白での更なる分割
                    if '　' in line:
                        parts = line.split('　')
                        for part in parts:
                            part = part.strip()
                            if len(part) >= 5 and not self._is_metadata_line(part):
                                sentences.append(part)
                    else:
                        sentences.append(line)
                
                # 中程度の長さの行
                else:
                    # 適度な分割を試行
                    if '　' in line:
                        parts = line.split('　')
                        for part in parts:
                            part = part.strip()
                            if len(part) >= 5 and not self._is_metadata_line(part):
                                sentences.append(part)
                    else:
                        # 句読点での分割を試行
                        sub_sentences = self._split_by_punctuation(line)
                        sentences.extend(sub_sentences)
        
        # 3. 最終クリーニング
        cleaned_sentences = []
        for sentence in sentences:
            cleaned = sentence.strip()
            
            # 不要な文をフィルタリング
            if (cleaned and 
                len(cleaned) >= 5 and 
                len(cleaned) <= 500 and  # 最大文字数制限を追加
                not re.match(r'^[\s\n　]*$', cleaned) and
                not self._is_metadata_line(cleaned)):
                
                # 改行・空白の正規化
                cleaned = re.sub(r'\s+', ' ', cleaned)
                cleaned = re.sub(r'　+', '　', cleaned)
                cleaned_sentences.append(cleaned)
        
        logger.info(f"📝 文分割完了: {len(cleaned_sentences)}文（句点{'あり' if '。' in content else 'なし'}）")
        return cleaned_sentences
    
    def _force_split_long_text(self, text: str) -> List[str]:
        """超長文の強制分割"""
        sentences = []
        
        # 1. 句読点での分割を試行
        punct_sentences = self._split_by_punctuation(text)
        
        for sentence in punct_sentences:
            # まだ長すぎる場合は文字数で強制分割
            if len(sentence) > 300:
                # 300文字ごとに分割
                for i in range(0, len(sentence), 300):
                    chunk = sentence[i:i+300].strip()
                    if len(chunk) >= 5:
                        sentences.append(chunk)
            else:
                if len(sentence) >= 5:
                    sentences.append(sentence)
        
        return sentences
    
    def _split_by_punctuation(self, text: str) -> List[str]:
        """句読点での分割"""
        sentences = []
        
        # 句読点での分割パターン
        patterns = [
            r'[。！？]',    # 文末記号
            r'[、；：]',    # 中間記号
        ]
        
        current_text = text
        
        # 文末記号での分割を優先
        parts = re.split(r'([。！？])', current_text)
        
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
            # まだ長すぎる場合は読点で分割
            if len(current_sentence) > 200:
                comma_parts = current_sentence.split('、')
                for comma_part in comma_parts:
                    comma_part = comma_part.strip()
                    if len(comma_part) >= 5:
                        sentences.append(comma_part)
            else:
                sentences.append(current_sentence.strip())
        
        return sentences if sentences else [text]
    
    def _is_metadata_line(self, line: str) -> bool:
        """メタデータ行の判定"""
        
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
        ]
        
        for pattern in metadata_indicators:
            if re.search(pattern, line):
                return True
        
        return False
    
    def get_sentence_context(self, sentences: List[str], target_index: int, context_length: int = 1) -> SentenceContext:
        """指定した文の前後文脈を取得"""
        
        if not sentences or target_index < 0 or target_index >= len(sentences):
            return SentenceContext("", "", "", -1, -1)
        
        # メイン文
        main_sentence = sentences[target_index]
        
        # 前文脈
        before_start = max(0, target_index - context_length)
        before_sentences = sentences[before_start:target_index]
        before_text = "".join(before_sentences)
        
        # 後文脈
        after_end = min(len(sentences), target_index + context_length + 1)
        after_sentences = sentences[target_index + 1:after_end]
        after_text = "".join(after_sentences)
        
        return SentenceContext(
            sentence=main_sentence,
            before_text=before_text,
            after_text=after_text,
            sentence_index=target_index,
            char_position=sum(len(s) for s in sentences[:target_index])
        )
    
    def process_work_content(self, work_id: int, raw_content: str) -> Dict:
        """作品コンテンツの完全処理"""
        
        logger.info(f"📚 作品{work_id}の処理開始")
        
        # 1. 本文抽出
        main_content = self.extract_main_content(raw_content)
        
        if len(main_content) < 100:
            logger.warning(f"⚠️ 作品{work_id}: 本文が短すぎます ({len(main_content)}文字)")
            return {
                'success': False,
                'main_content': main_content,
                'sentences': [],
                'error': '本文が短すぎる'
            }
        
        # 2. 文分割
        sentences = self.split_into_sentences(main_content)
        
        if len(sentences) < 5:
            logger.warning(f"⚠️ 作品{work_id}: 文数が少なすぎます ({len(sentences)}文)")
            return {
                'success': False,
                'main_content': main_content,
                'sentences': sentences,
                'error': '文数が少なすぎる'
            }
        
        logger.info(f"✅ 作品{work_id}処理完了: {len(main_content)}文字, {len(sentences)}文")
        
        return {
            'success': True,
            'main_content': main_content,
            'sentences': sentences,
            'stats': {
                'original_length': len(raw_content),
                'processed_length': len(main_content),
                'sentence_count': len(sentences)
            }
        }

# テスト用の関数
def test_aozora_processor():
    """テスト実行"""
    import sqlite3
    
    processor = AozoraContentProcessor()
    
    # データベースから実データでテスト
    with sqlite3.connect('data/bungo_production.db') as conn:
        cursor = conn.execute("SELECT work_id, title, content FROM works LIMIT 3")
        
        for work_id, title, content in cursor.fetchall():
            print(f"\n{'='*50}")
            print(f"📚 作品: {title}")
            print(f"📊 元データ: {len(content)}文字")
            
            result = processor.process_work_content(work_id, content)
            
            if result['success']:
                sentences = result['sentences']
                print(f"✅ 処理成功: {len(result['main_content'])}文字, {len(sentences)}文")
                
                if sentences:
                    print(f"📝 最初の文: {sentences[0][:100]}...")
                    if len(sentences) > 1:
                        print(f"📝 2番目の文: {sentences[1][:100]}...")
            else:
                print(f"❌ 処理失敗: {result['error']}")

if __name__ == "__main__":
    test_aozora_processor() 