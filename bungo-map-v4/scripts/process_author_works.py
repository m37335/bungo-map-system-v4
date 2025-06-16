#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
作者名を指定して青空文庫から作品を取得し、解析・DB保存まで一括実行するスクリプト
（青空文庫HTML階層自動追跡版）
"""

import sys
import os
import sqlite3
import requests
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import time
import re
from bs4 import BeautifulSoup
import urllib.parse
import unicodedata

# v4パスを追加
sys.path.insert(0, '/app/bungo-map-v4')

# v4システムをインポート
from src.bungo_map.database.manager import DatabaseManager
from src.bungo_map.extractors_v4.unified_place_extractor import UnifiedPlaceExtractor
from src.bungo_map.extractors_v4.place_normalizer import PlaceNormalizer
from src.bungo_map.optimization.performance_optimizer import PerformanceOptimizer, OptimizationConfig

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

AOZORA_BASE = "https://www.aozora.gr.jp"
AOZORA_AUTHOR_LIST = f"{AOZORA_BASE}/index_pages/person_all.html"

class AuthorWorksProcessor:
    """任意の作者の作品を処理するクラス（青空文庫HTML階層自動追跡版）"""
    def __init__(self, author_name: str, db_path: str = '/app/bungo-map-v4/data/databases/bungo_v4.db'):
        self.author_name = author_name
        self.db_path = db_path
        self.db_manager = DatabaseManager(db_path)
        self.unified_extractor = UnifiedPlaceExtractor()
        self.normalizer = PlaceNormalizer()
        self.optimizer = PerformanceOptimizer(db_path, OptimizationConfig())

    def _create_tables(self, conn: sqlite3.Connection):
        """テーブルの作成"""
        logger.info("🗄️ テーブル作成開始")
        
        # 作者テーブル
        conn.execute("""
            CREATE TABLE IF NOT EXISTS authors (
                author_id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 作品テーブル
        conn.execute("""
            CREATE TABLE IF NOT EXISTS works (
                work_id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id INTEGER,
                work_title TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES authors(author_id)
            )
        """)
        
        # センテンステーブル
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sentences (
                sentence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_id INTEGER,
                author_id INTEGER,
                sentence_text TEXT NOT NULL,
                before_text TEXT,
                after_text TEXT,
                position_in_work INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (work_id) REFERENCES works(work_id),
                FOREIGN KEY (author_id) REFERENCES authors(author_id)
            )
        """)
        
        # 地名マスターテーブル
        conn.execute("""
            CREATE TABLE IF NOT EXISTS places_master (
                place_id INTEGER PRIMARY KEY AUTOINCREMENT,
                place_name TEXT NOT NULL,
                canonical_name TEXT,
                latitude REAL,
                longitude REAL,
                prefecture TEXT,
                place_type TEXT,
                mention_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 文-地名関係テーブル
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sentence_places (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sentence_id INTEGER,
                place_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sentence_id) REFERENCES sentences(sentence_id),
                FOREIGN KEY (place_id) REFERENCES places_master(place_id)
            )
        """)
        
        # インデックスの作成
        conn.execute("CREATE INDEX IF NOT EXISTS idx_works_author_id ON works(author_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sentences_work_id ON sentences(work_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sentences_author_id ON sentences(author_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_places_name ON places_master(place_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sentence_places_sentence_id ON sentence_places(sentence_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sentence_places_place_id ON sentence_places(place_id)")
        
        logger.info("✅ テーブル作成完了")

    def initialize_database(self):
        """DB初期化（テーブル作成・最適化）"""
        logger.info("🗄️ データベース初期化・最適化")
        
        with sqlite3.connect(self.db_path) as conn:
            # 外部キー制約を一時的に無効化
            conn.execute("PRAGMA foreign_keys = OFF")
            
            # 既存のテーブルを削除（子テーブルから順に）
            conn.execute("DROP TABLE IF EXISTS sentence_places")
            conn.execute("DROP TABLE IF EXISTS sentences")
            conn.execute("DROP TABLE IF EXISTS works")
            conn.execute("DROP TABLE IF EXISTS places_master")
            conn.execute("DROP TABLE IF EXISTS authors")
            
            # テーブルの作成
            self._create_tables(conn)
            
            # 外部キー制約を再度有効化
            conn.execute("PRAGMA foreign_keys = ON")
            
            # 最適化の実行
            self.optimizer.optimize_database()
            
            conn.commit()
        
        logger.info("✅ データベース初期化完了")

    def get_person_page_url(self) -> Optional[str]:
        """作者名からperson{ID}.htmlへのURLを取得"""
        logger.info(f"🔍 作者personページ検索: {self.author_name}")
        try:
            r = requests.get(AOZORA_AUTHOR_LIST, timeout=10)
            r.raise_for_status()
            html = r.text
            # デバッグ用: 取得したHTMLを保存
            with open("author_list_debug.html", "w", encoding="utf-8") as f:
                f.write(html)
            soup = BeautifulSoup(html, 'html.parser')
            for link in soup.find_all('a'):
                raw_text = link.text
                stripped_text = raw_text.strip()
                normalized_text = unicodedata.normalize('NFKC', stripped_text)
                logger.info(f"DEBUG: raw_text={repr(raw_text)}, stripped_text={repr(stripped_text)}, normalized_text={repr(normalized_text)}")
                if self.author_name in normalized_text:
                    href = link.get('href', '')
                    if href.startswith('person') and href.endswith('.html'):
                        url = urllib.parse.urljoin(AOZORA_AUTHOR_LIST, href)
                        logger.info(f"✅ personページURL発見: {url}")
                        return url
            logger.error("指定した作者が見つかりません")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"青空文庫への接続に失敗しました: {e}")
            return None

    def get_cards_page_url(self, person_url: str) -> Optional[str]:
        """person{ID}.htmlからcards/000074/のURLを取得"""
        logger.info(f"🔍 cardsページURL検索: {person_url}")
        try:
            r = requests.get(person_url, timeout=10)
            r.raise_for_status()
            r.encoding = 'shift_jis'
            soup = BeautifulSoup(r.text, 'html.parser')
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if href.startswith('../cards/') and href.endswith('/'):
                    url = urllib.parse.urljoin(person_url, href)
                    logger.info(f"✅ cardsページURL発見: {url}")
                    return url
            logger.error("cardsページが見つかりません")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"cardsページ取得失敗: {e}")
            return None

    def fetch_works(self, cards_url: str) -> List[Dict[str, Any]]:
        """cards/000074/ページから作品リストを取得"""
        logger.info(f"📚 作品リスト取得: {cards_url}")
        try:
            r = requests.get(cards_url, timeout=10)
            r.raise_for_status()
            r.encoding = 'shift_jis'
            soup = BeautifulSoup(r.text, 'html.parser')
            works = []
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if href.startswith('files/') and href.endswith('.html'):
                    title = link.text.strip()
                    url = urllib.parse.urljoin(cards_url, href)
                    works.append({'title': title, 'url': url})
            logger.info(f"取得作品数: {len(works)}")
            return works
        except requests.exceptions.RequestException as e:
            logger.error(f"作品リスト取得に失敗: {e}")
            return []

    def fetch_main_text_url(self, work_url: str) -> Optional[str]:
        """作品詳細ページからテキスト/XHTMLファイルのURLを取得"""
        logger.info(f"📄 本文ファイルURL検索: {work_url}")
        try:
            r = requests.get(work_url, timeout=10)
            r.raise_for_status()
            r.encoding = 'shift_jis'
            soup = BeautifulSoup(r.text, 'html.parser')
            for link in soup.find_all('a'):
                text = link.text.strip()
                href = link.get('href', '')
                # テキストファイル優先、なければXHTML
                if 'テキストファイル' in text or 'XHTMLファイル' in text:
                    url = urllib.parse.urljoin(work_url, href)
                    logger.info(f"✅ 本文ファイルURL発見: {url}")
                    return url
            logger.warning("本文ファイルが見つかりません")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"本文ファイルURL取得失敗: {e}")
            return None

    def fetch_work_content(self, main_text_url: str) -> Optional[str]:
        """テキスト/XHTML本文をダウンロード"""
        try:
            r = requests.get(main_text_url, timeout=10)
            r.raise_for_status()
            # テキストファイルならそのまま、XHTMLならタグ除去
            if main_text_url.endswith('.txt'):
                r.encoding = 'shift_jis'
                return r.text
            else:
                r.encoding = 'shift_jis'
                soup = BeautifulSoup(r.text, 'html.parser')
                return soup.get_text()
        except requests.exceptions.RequestException as e:
            logger.warning(f"本文ダウンロード失敗: {main_text_url} - {e}")
            return None

    def process(self):
        """一連の処理"""
        self.initialize_database()
        person_url = self.get_person_page_url()
        if not person_url:
            logger.error("personページ取得失敗")
            return
        cards_url = self.get_cards_page_url(person_url)
        if not cards_url:
            logger.error("cardsページ取得失敗")
            return
        works = self.fetch_works(cards_url)
        if not works:
            logger.error("作品リスト取得失敗")
            return
        # DBに作者登録
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("INSERT INTO authors (author_name) VALUES (?)", (self.author_name,))
            local_author_id = cur.lastrowid
            conn.commit()
        for work in works:
            title = work['title']
            logger.info(f"--- 作品処理: {title} ---")
            main_text_url = self.fetch_main_text_url(work['url'])
            if not main_text_url:
                logger.warning(f"本文URL取得失敗: {title}")
                continue
            content = self.fetch_work_content(main_text_url)
            if not content:
                logger.warning(f"本文取得失敗: {title}")
                continue
            # 作品DB登録
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute(
                    "INSERT INTO works (author_id, work_title, content) VALUES (?, ?, ?)",
                    (local_author_id, title, content)
                )
                work_id = cur.lastrowid
                conn.commit()
            # センテンス分割
            sentences = self.unified_extractor.extract_sentences(content)
            logger.info(f"センテンス数: {len(sentences)}")
            for i, sentence in enumerate(sentences):
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT INTO sentences (work_id, author_id, sentence_text, before_text, after_text, position_in_work) VALUES (?, ?, ?, ?, ?, ?)",
                        (work_id, local_author_id, sentence['text'], sentence.get('before', ''), sentence.get('after', ''), i)
                    )
                    conn.commit()
            # 地名抽出
            for i, sentence in enumerate(sentences):
                places = self.unified_extractor.extract_places(sentence['text'], sentence.get('before', ''), sentence.get('after', ''))
                for place in places:
                    normalized = self.normalizer.normalize(place['name'])
                    with sqlite3.connect(self.db_path) as conn:
                        cur = conn.execute("SELECT place_id FROM places_master WHERE place_name = ?", (normalized,))
                        result = cur.fetchone()
                        if result:
                            place_id = result[0]
                            conn.execute("UPDATE places_master SET mention_count = mention_count + 1 WHERE place_id = ?", (place_id,))
                        else:
                            cur = conn.execute("INSERT INTO places_master (place_name, canonical_name, mention_count) VALUES (?, ?, 1)", (place['name'], normalized))
                            place_id = cur.lastrowid
                        conn.execute("INSERT INTO sentence_places (sentence_id, place_id) VALUES (?, ?)", (i+1, place_id))
                        conn.commit()
            logger.info(f"✅ 作品処理完了: {title}")
        logger.info("🎉 全作品処理完了")


def main():
    parser = argparse.ArgumentParser(description="作者名を指定して青空文庫作品を解析・DB保存")
    parser.add_argument('--author', type=str, required=True, help='作者名（例: 梶井 基次郎）')
    args = parser.parse_args()
    processor = AuthorWorksProcessor(args.author)
    processor.process()

if __name__ == "__main__":
    main() 