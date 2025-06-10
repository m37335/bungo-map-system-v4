#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧹 青空文庫テキストクリーナー
青空文庫特有のマークアップを除去し、地名抽出に適したテキストに前処理
"""

import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

class AozoraTextCleaner:
    """青空文庫テキストの前処理クラス"""
    
    def __init__(self):
        # 強力なクリーニングパターン
        self.strong_patterns = [
            # ルビ記号の完全除去
            (r'《[^》]*》', ''),  # 《ルビ》
            (r'｜', ''),          # ルビ開始記号
            
            # 入力者注の完全除去
            (r'［＃[^］]*］', ''),  # ［＃注釈］
            (r'※［＃[^］]*］', ''), # ※［＃外字］
            
            # 青空文庫メタ情報の完全除去
            (r'【[^】]*】.*?(?=\n\n|\n[^【])', '', re.DOTALL),  # 【説明】セクション
            (r'底本：.*?(?=\n\n|$)', '', re.DOTALL),           # 底本情報
            (r'入力：.*?(?=\n\n|$)', '', re.DOTALL),           # 入力者情報
            (r'校正：.*?(?=\n\n|$)', '', re.DOTALL),           # 校正者情報
            (r'初版発行.*?(?=\n\n|$)', '', re.DOTALL),         # 発行情報
            (r'\d{4}（[^）]*）年.*?月.*?日.*?発行', ''),        # 発行日
            
            # 区切り線の除去
            (r'-{5,}', ''),
            (r'={5,}', ''),
            (r'─{5,}', ''),
            
            # 記号説明パターン
            (r'（例）[^）]*）[^。]*', ''),
            (r'：[^。\n]*記号', ''),
            (r'：[^。\n]*注.*?指定', ''),
            
            # 作品タイトル・作者名の除去（単独行）
            (r'^[^\n]{1,20}\n[^\n]{1,20}\n(?=\n)', '', re.MULTILINE),
            
            # 空行と空白の整理
            (r'\n\s*\n\s*\n+', '\n\n'),
            (r'^\s+', '', re.MULTILINE),
            (r'\s+$', '', re.MULTILINE),
        ]
        
        # 除去対象のメタテキスト（完全一致・部分一致）
        self.remove_patterns = [
            r'【テキスト中に現れる記号について】',
            r'※表題、副題は、底本編集時に与えられたものです',
            r'このファイルは、著作権者によって公開されているものです',
            r'転載・複製・翻案等は、著作権者に許可を得てください',
            r'：ルビ$',
            r'：入力者注',
            r'主に外字の説明',
            r'傍点の位置の指定',
            r'ルビの付く文字列の始まりを特定する記号',
        ]
    
    def clean_text(self, text: str) -> str:
        """テキスト全体をクリーンアップ"""
        if not text:
            return ""
        
        cleaned = text
        
        # 1. 特定パターンの除去
        for pattern in self.remove_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE)
        
        # 2. 強力なパターンマッチング
        for pattern, replacement, *flags in self.strong_patterns:
            flag = flags[0] if flags else 0
            cleaned = re.sub(pattern, replacement, cleaned, flags=flag)
        
        # 3. 最終整形
        cleaned = self._final_formatting(cleaned)
        
        return cleaned
    
    def clean_sentence(self, sentence: str) -> str:
        """文レベルでのクリーンアップ（地名抽出用）"""
        if not sentence:
            return ""
        
        cleaned = sentence
        
        # ルビ除去
        cleaned = re.sub(r'《[^》]*》', '', cleaned)
        cleaned = re.sub(r'｜', '', cleaned)
        
        # 注釈除去
        cleaned = re.sub(r'［＃[^］]*］', '', cleaned)
        cleaned = re.sub(r'※［＃[^］]*］', '', cleaned)
        
        # メタ情報らしき文字列の除去
        meta_patterns = [
            r'底本：.*',
            r'入力：.*',
            r'校正：.*',
            r'\d{4}（[^）]*）年.*',
            r'【[^】]*】',
            r'：ルビ.*',
            r'：入力者注.*',
        ]
        
        for pattern in meta_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # 余分な空白・記号除去
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'^[：（）\s]*', '', cleaned)  # 行頭の記号除去
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _final_formatting(self, text: str) -> str:
        """最終整形"""
        cleaned = text
        
        # 連続する空行を整理
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        
        # 行の整理
        lines = cleaned.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            # 空行や無意味な行をスキップ
            if (line and 
                len(line) > 2 and  # 短すぎる行は除外
                not re.match(r'^[：（）\s]*$', line) and  # 記号のみの行は除外
                not re.match(r'^[─\-=]{3,}$', line)):   # 区切り線は除外
                clean_lines.append(line)
        
        cleaned = '\n'.join(clean_lines)
        return cleaned.strip()
    
    def extract_clean_sentences(self, text: str, min_length: int = 10) -> List[str]:
        """クリーンな文を抽出"""
        cleaned_text = self.clean_text(text)
        
        # 文境界で分割（句点、感嘆符、疑問符）
        sentences = re.split(r'[。！？]', cleaned_text)
        
        # フィルタリング
        clean_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if (len(sentence) >= min_length and 
                not self._is_meta_text(sentence)):
                # 最終クリーニング
                clean_sentence = self.clean_sentence(sentence)
                if len(clean_sentence) >= min_length:
                    clean_sentences.append(clean_sentence)
        
        return clean_sentences
    
    def _is_meta_text(self, sentence: str) -> bool:
        """メタテキストかどうかの判定"""
        meta_indicators = [
            '底本', '初版', '入力', '校正', '発行',
            'ファイル', '著作権', '転載', '複製',
            '［＃', '※［＃', '《', '｜',
            '：ルビ', '：入力者注', '記号について',
            '外字の説明', '傍点の位置'
        ]
        
        return any(indicator in sentence for indicator in meta_indicators)

# 既存の抽出器に統合するためのヘルパー関数
def clean_aozora_text(text: str) -> str:
    """グローバル関数として提供"""
    cleaner = AozoraTextCleaner()
    return cleaner.clean_text(text)

def clean_aozora_sentence(sentence: str) -> str:
    """文レベルクリーニングのグローバル関数"""
    cleaner = AozoraTextCleaner()
    return cleaner.clean_sentence(sentence)

def test_cleaner():
    """テスト用関数"""
    cleaner = AozoraTextCleaner()
    
    # より実際的なテストケース
    test_text = """
山椒大夫
森鴎外

-------------------------------------------------------
【テキスト中に現れる記号について】

《》：ルビ
（例）越後《えちご》の

｜：ルビの付く文字列の始まりを特定する記号
（例）一番｜隅《すみ》へはいって

［＃］：入力者注　主に外字の説明や、傍点の位置の指定
-------------------------------------------------------

これは｜越後《えちご》の山｜奥《おく》の話である。
安寿《あんじゅ》と厨子王《ずしおう》は［＃「厨子王」に傍点］父を探しに旅に出た。
長い旅路の果てに、ついに｜丹後《たんご》の国に着いた。

底本：「山椒大夫」岩波文庫
　　　1977（昭和52）年6月13日初版発行
※表題、副題は、底本編集時に与えられたものです。
    """
    
    print("=== 元テキスト ===")
    print(test_text)
    print("\n=== クリーンアップ後 ===")
    cleaned = cleaner.clean_text(test_text)
    print(cleaned)
    print("\n=== 文抽出 ===")
    sentences = cleaner.extract_clean_sentences(test_text)
    for i, sentence in enumerate(sentences, 1):
        print(f"{i}. {sentence}")

if __name__ == "__main__":
    test_cleaner() 