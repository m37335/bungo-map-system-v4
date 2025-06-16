#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫クライアント
作品のダウンロードと前処理を行う
"""

import os
import re
import zipfile
import logging
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class AozoraWork:
    """青空文庫作品データクラス"""
    work_id: str
    title: str
    author: str
    copyright_flag: int
    text_url: str
    text: Optional[str] = None
    processed_text: Optional[str] = None

class AozoraClient:
    """青空文庫クライアント"""
    
    def __init__(self, cache_dir: str = "data/aozora_cache"):
        """初期化"""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 青空文庫のURL
        self.base_url = "https://www.aozora.gr.jp"
        self.catalog_url = f"{self.base_url}/cards/000000/files/catalog.csv.zip"
        
        logger.info(f"📚 青空文庫クライアント初期化: キャッシュディレクトリ={self.cache_dir}")
    
    def download_catalog(self) -> List[Dict]:
        """カタログのダウンロードと解析"""
        try:
            # ZIPファイルのダウンロード
            response = requests.get(self.catalog_url)
            response.raise_for_status()
            
            # 一時ファイルに保存
            zip_path = self.cache_dir / "catalog.zip"
            with open(zip_path, "wb") as f:
                f.write(response.content)
            
            # ZIPファイルの展開
            with zipfile.ZipFile(zip_path) as z:
                z.extractall(self.cache_dir)
            
            # CSVファイルの読み込み
            csv_path = self.cache_dir / "catalog.csv"
            works = []
            with open(csv_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("作品ID"):
                        continue
                    
                    fields = line.strip().split(",")
                    if len(fields) >= 4:
                        work = {
                            "work_id": fields[0],
                            "title": fields[1],
                            "author": fields[2],
                            "copyright_flag": int(fields[3])
                        }
                        works.append(work)
            
            logger.info(f"✅ カタログダウンロード完了: {len(works)}件の作品")
            return works
            
        except Exception as e:
            logger.error(f"❌ カタログダウンロード失敗: {e}")
            return []
    
    def download_work(self, work_id: str) -> Optional[AozoraWork]:
        """作品のダウンロード"""
        try:
            # キャッシュを確認
            cache_path = self.cache_dir / f"{work_id}.txt"
            if cache_path.exists():
                with open(cache_path, "r", encoding="utf-8") as f:
                    text = f.read()
                return AozoraWork(
                    work_id=work_id,
                    title="",  # カタログから取得
                    author="",  # カタログから取得
                    copyright_flag=0,
                    text_url="",
                    text=text
                )
            
            # 作品ページのURL
            work_url = f"{self.base_url}/cards/{work_id}/files/{work_id}.html"
            
            # 作品ページの取得
            response = requests.get(work_url)
            response.raise_for_status()
            
            # テキストファイルのURLを抽出
            text_url_match = re.search(r'href="(.*?\.txt)"', response.text)
            if not text_url_match:
                logger.error(f"❌ テキストURLが見つかりません: {work_id}")
                return None
            
            text_url = f"{self.base_url}/cards/{work_id}/files/{text_url_match.group(1)}"
            
            # テキストファイルのダウンロード
            response = requests.get(text_url)
            response.raise_for_status()
            text = response.text
            
            # キャッシュに保存
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            logger.info(f"✅ 作品ダウンロード完了: {work_id}")
            return AozoraWork(
                work_id=work_id,
                title="",  # カタログから取得
                author="",  # カタログから取得
                copyright_flag=0,
                text_url=text_url,
                text=text
            )
            
        except Exception as e:
            logger.error(f"❌ 作品ダウンロード失敗: {work_id} - {e}")
            return None
    
    def process_text(self, text: str) -> str:
        """テキストの前処理"""
        # ルビの除去
        text = re.sub(r'《.*?》', '', text)
        
        # 注記の除去
        text = re.sub(r'［.*?］', '', text)
        
        # 空行の除去
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # 前後の空白を除去
        text = text.strip()
        
        return text
    
    def get_work_with_context(self, work_id: str, sentence: str, context_size: int = 1) -> Tuple[str, str, str]:
        """文の前後文を取得"""
        work = self.download_work(work_id)
        if not work or not work.text:
            return "", "", ""
        
        # テキストを行に分割
        lines = work.text.split('\n')
        
        # 文を含む行を探す
        for i, line in enumerate(lines):
            if sentence in line:
                # 前後の文を取得
                before = '\n'.join(lines[max(0, i-context_size):i])
                after = '\n'.join(lines[i+1:i+1+context_size])
                return before, line, after
        
        return "", "", "" 