#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫公式CSVデータダウンローダー・パーサー
公式CSVファイルから正確な作品情報とURL情報を取得
"""

import requests
import zipfile
import csv
import os
import time
import logging
from typing import Dict, List, Optional, Tuple
from io import StringIO
import tempfile
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AozoraCSVDownloader:
    """青空文庫公式CSVファイルのダウンロードと解析を行うクラス"""
    
    def __init__(self):
        # 青空文庫公式CSVファイルのURL
        self.csv_url = "https://www.aozora.gr.jp/index_pages/list_person_all_extended_utf8.zip"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.cache_dir = "/tmp/aozora_csv_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def download_csv_data(self) -> Optional[str]:
        """
        青空文庫公式CSVファイルをダウンロードしてCSVデータを返す
        
        Returns:
            str: CSVファイルの内容（UTF-8）
        """
        try:
            logger.info("青空文庫公式CSVファイルをダウンロード中...")
            response = requests.get(self.csv_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # ZIPファイルを一時ディレクトリに保存
            zip_path = os.path.join(self.cache_dir, "aozora_list.zip")
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            # ZIPファイルを展開してCSVを読取
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # ZIPファイル内のCSVファイル名を取得
                csv_files = [name for name in zip_ref.namelist() if name.endswith('.csv')]
                if not csv_files:
                    logger.error("ZIPファイル内にCSVファイルが見つかりません")
                    return None
                    
                # 最初のCSVファイルを読み込み
                csv_filename = csv_files[0]
                logger.info(f"CSVファイル '{csv_filename}' を読み込み中...")
                
                with zip_ref.open(csv_filename) as csv_file:
                    # UTF-8でデコード
                    csv_content = csv_file.read().decode('utf-8')
                    return csv_content
                    
        except requests.RequestException as e:
            logger.error(f"CSVファイルのダウンロードに失敗: {e}")
            return None
        except zipfile.BadZipFile as e:
            logger.error(f"ZIPファイルの展開に失敗: {e}")
            return None
        except Exception as e:
            logger.error(f"CSVデータの取得に失敗: {e}")
            return None
    
    def parse_csv_data(self, csv_content: str) -> List[Dict]:
        """
        CSVデータを解析して作品情報のリストを返す
        
        Args:
            csv_content (str): CSVファイルの内容
            
        Returns:
            List[Dict]: 作品情報のリスト
        """
        try:
            works = []
            csv_reader = csv.DictReader(StringIO(csv_content))
            
            for row in csv_reader:
                # 作品情報を構造化
                work_info = {
                    'work_id': row.get('作品ID', '').strip(),
                    'title': row.get('作品名', '').strip(),
                    'title_yomi': row.get('作品名読み', '').strip(),
                    'author_id': row.get('人物ID', '').strip(),
                    'author_last_name': row.get('姓', '').strip(),
                    'author_first_name': row.get('名', '').strip(),
                    'author_last_name_yomi': row.get('姓読み', '').strip(),
                    'author_first_name_yomi': row.get('名読み', '').strip(),
                    'text_url': row.get('テキストファイルURL', '').strip(),
                    'html_url': row.get('XHTML/HTMLファイルURL', '').strip(),
                    'card_url': row.get('図書カードURL', '').strip(),
                    'copyright_flag': row.get('作品著作権フラグ', '').strip(),
                    'character_type': row.get('文字遣い種別', '').strip(),
                    'first_appearance': row.get('初出', '').strip(),
                    'classification': row.get('分類番号', '').strip(),
                    'release_date': row.get('公開日', '').strip(),
                    'last_modified': row.get('最終更新日', '').strip()
                }
                
                # 有効な作品情報のみ追加（work_idは必須ではない）
                if work_info['title'] and work_info['author_last_name']:
                    works.append(work_info)
            
            logger.info(f"CSVから {len(works)} 件の作品情報を解析しました")
            return works
            
        except Exception as e:
            logger.error(f"CSVデータの解析に失敗: {e}")
            return []
    
    def get_work_by_title_and_author(self, title: str, author_name: str) -> Optional[Dict]:
        """
        作品名と著者名から作品情報を検索
        
        Args:
            title (str): 作品名
            author_name (str): 著者名
            
        Returns:
            Dict: 作品情報（見つからない場合はNone）
        """
        csv_content = self.download_csv_data()
        if not csv_content:
            return None
            
        works = self.parse_csv_data(csv_content)
        
        # タイトルと著者名でマッチング
        for work in works:
            author_full_name = f"{work['author_last_name']}{work['author_first_name']}"
            
            # 完全一致
            if work['title'] == title and author_full_name == author_name:
                return work
            
            # 部分一致（タイトル）
            if title in work['title'] and author_full_name == author_name:
                return work
                
            # 読み仮名での一致
            if work['title_yomi'] and title in work['title_yomi'] and author_full_name == author_name:
                return work
        
        return None
    
    def get_works_by_author(self, author_name: str) -> List[Dict]:
        """
        著者名から全作品を検索
        
        Args:
            author_name (str): 著者名
            
        Returns:
            List[Dict]: 作品情報のリスト
        """
        csv_content = self.download_csv_data()
        if not csv_content:
            return []
            
        works = self.parse_csv_data(csv_content)
        author_works = []
        
        for work in works:
            author_full_name = f"{work['author_last_name']}{work['author_first_name']}"
            if author_full_name == author_name:
                author_works.append(work)
        
        return author_works
    
    def extract_content_from_url(self, url: str) -> Optional[str]:
        """
        URLからテキストコンテンツを取得
        
        Args:
            url (str): テキストファイルのURL
            
        Returns:
            str: テキストコンテンツ（取得失敗時はNone）
        """
        try:
            time.sleep(1)  # レート制限
            
            if not url:
                return None
                
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # ZIPファイルの場合
            if url.endswith('.zip'):
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(response.content)
                    temp_file.flush()
                    
                    try:
                        with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
                            # ZIP内のテキストファイルを検索
                            txt_files = [name for name in zip_ref.namelist() if name.endswith('.txt')]
                            if txt_files:
                                with zip_ref.open(txt_files[0]) as txt_file:
                                    # Shift_JISでデコード
                                    content = txt_file.read().decode('shift_jis', errors='ignore')
                                    return content
                    finally:
                        os.unlink(temp_file.name)
            
            # HTMLファイルの場合
            elif url.endswith('.html'):
                # HTMLファイルはShift_JISでエンコードされている
                response.encoding = 'shift_jis'
                return response.text
            
            return None
            
        except Exception as e:
            logger.error(f"コンテンツ取得エラー ({url}): {e}")
            return None
    
    def search_and_get_content(self, title: str, author_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        作品名と著者名からURLとコンテンツを取得
        
        Args:
            title (str): 作品名
            author_name (str): 著者名
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (URL, コンテンツ)
        """
        work_info = self.get_work_by_title_and_author(title, author_name)
        if not work_info:
            return None, None
        
        # テキストファイルのURLを優先
        url = work_info.get('text_url') or work_info.get('html_url')
        if not url:
            return None, None
            
        content = self.extract_content_from_url(url)
        return url, content
    
    def get_copyright_free_works(self) -> List[Dict]:
        """
        著作権が切れている作品のみを取得
        
        Returns:
            List[Dict]: 著作権フリーの作品リスト
        """
        csv_content = self.download_csv_data()
        if not csv_content:
            return []
            
        works = self.parse_csv_data(csv_content)
        
        # 著作権フラグが空文字列または"なし"の作品のみ
        copyright_free_works = []
        for work in works:
            copyright_flag = work.get('copyright_flag', '').strip()
            if not copyright_flag or copyright_flag == 'なし':
                copyright_free_works.append(work)
        
        logger.info(f"著作権フリー作品: {len(copyright_free_works)} 件")
        return copyright_free_works


def test_csv_downloader():
    """CSVダウンローダーのテスト"""
    downloader = AozoraCSVDownloader()
    
    # テストケース1: 夏目漱石「こころ」
    print("\n=== テスト1: 夏目漱石「こころ」を検索 ===")
    url, content = downloader.search_and_get_content("こころ", "夏目漱石")
    if url:
        print(f"✅ URL発見: {url}")
        if content:
            print(f"✅ コンテンツ取得成功 (長さ: {len(content)} 文字)")
            print(f"   先頭100文字: {content[:100]}...")
        else:
            print("❌ コンテンツ取得失敗")
    else:
        print("❌ URL未発見")
    
    # テストケース2: 芥川龍之介「羅生門」
    print("\n=== テスト2: 芥川龍之介「羅生門」を検索 ===")
    url, content = downloader.search_and_get_content("羅生門", "芥川龍之介")
    if url:
        print(f"✅ URL発見: {url}")
        if content:
            print(f"✅ コンテンツ取得成功 (長さ: {len(content)} 文字)")
            print(f"   先頭100文字: {content[:100]}...")
        else:
            print("❌ コンテンツ取得失敗")
    else:
        print("❌ URL未発見")


if __name__ == "__main__":
    test_csv_downloader() 