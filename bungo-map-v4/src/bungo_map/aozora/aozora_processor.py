#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫テキスト処理
作品テキストの前処理と地名抽出の準備を行う
"""

import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

from .aozora_client import AozoraClient, AozoraWork

logger = logging.getLogger(__name__)

@dataclass
class ProcessedWork:
    """処理済み作品データクラス"""
    work_id: str
    title: str
    author: str
    text: str
    sentences: List[str]
    metadata: Dict

class AozoraProcessor:
    """青空文庫テキスト処理クラス"""
    
    def __init__(self, client: Optional[AozoraClient] = None):
        """初期化"""
        self.client = client or AozoraClient()
        
        # 文分割用の正規表現
        self.sentence_pattern = re.compile(r'[。．！？!?]+')
        
        logger.info("📝 青空文庫テキスト処理クラス初期化完了")
    
    def process_work(self, work: AozoraWork) -> Optional[ProcessedWork]:
        """作品の処理"""
        if not work.text:
            logger.error(f"❌ テキストが空です: {work.work_id}")
            return None
        
        try:
            # テキストの前処理
            processed_text = self.client.process_text(work.text)
            
            # 文の分割
            sentences = self._split_sentences(processed_text)
            
            # メタデータの抽出
            metadata = self._extract_metadata(processed_text)
            
            logger.info(f"✅ 作品処理完了: {work.work_id} - {len(sentences)}文")
            
            return ProcessedWork(
                work_id=work.work_id,
                title=work.title,
                author=work.author,
                text=processed_text,
                sentences=sentences,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"❌ 作品処理失敗: {work.work_id} - {e}")
            return None
    
    def _split_sentences(self, text: str) -> List[str]:
        """文の分割"""
        # 改行を空白に置換
        text = text.replace('\n', ' ')
        
        # 文末記号で分割
        sentences = []
        current = ""
        
        for char in text:
            current += char
            if self.sentence_pattern.search(char):
                if current.strip():
                    sentences.append(current.strip())
                current = ""
        
        # 最後の文を追加
        if current.strip():
            sentences.append(current.strip())
        
        return sentences
    
    def _extract_metadata(self, text: str) -> Dict:
        """メタデータの抽出"""
        metadata = {}
        
        # タイトル
        title_match = re.search(r'【タイトル】\s*(.*?)(?:\n|$)', text)
        if title_match:
            metadata['title'] = title_match.group(1).strip()
        
        # 作者
        author_match = re.search(r'【作者】\s*(.*?)(?:\n|$)', text)
        if author_match:
            metadata['author'] = author_match.group(1).strip()
        
        # 底本
        source_match = re.search(r'【底本】\s*(.*?)(?:\n|$)', text)
        if source_match:
            metadata['source'] = source_match.group(1).strip()
        
        # 入力
        input_match = re.search(r'【入力】\s*(.*?)(?:\n|$)', text)
        if input_match:
            metadata['input'] = input_match.group(1).strip()
        
        # 校正
        proof_match = re.search(r'【校正】\s*(.*?)(?:\n|$)', text)
        if proof_match:
            metadata['proof'] = proof_match.group(1).strip()
        
        return metadata
    
    def get_sentence_with_context(self, work_id: str, sentence: str, context_size: int = 1) -> tuple[str, str, str]:
        """文の前後文を取得"""
        return self.client.get_work_with_context(work_id, sentence, context_size) 