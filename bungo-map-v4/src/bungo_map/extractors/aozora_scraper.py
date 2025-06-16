#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫スクレイパー

青空文庫から作品を取得し、データベースに保存する
"""

import requests
import time
import unicodedata
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import logging
import os
import chardet
import re
from ..database.models import Author, Work, Sentence
from ..database.manager import DatabaseManager

logger = logging.getLogger(__name__)

class AozoraScraper:
    """青空文庫スクレイパー"""
    
    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """初期化"""
        self.config = config or {}
        self.db_manager = db_manager
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.author_list_url = self.config.get('author_list_url', 'https://www.aozora.gr.jp/index_pages/person_all.html')
        self.logger = logging.getLogger(__name__)
    
    def get_author_url(self, author_name: str) -> Optional[str]:
        """作者名から作者ページのURLを取得
        
        Args:
            author_name (str): 作者名
            
        Returns:
            Optional[str]: 作者ページのURL。見つからない場合はNone
            
        Note:
            - 作者リストページから作者名に一致するリンクを探す
            - hrefが「personXX.html」の形式の場合のみ処理
            - 常に「https://www.aozora.gr.jp/index_pages/personXX.html」の形式を返す
        """
        def normalize_name(name: str) -> str:
            """作者名を正規化"""
            return unicodedata.normalize('NFKC', name).replace('\u3000', ' ').strip()
        
        def is_valid_person_href(href: str) -> bool:
            """hrefが有効なpersonXX.html形式かチェック"""
            if not href:
                return False
            # #以降を除去
            href = href.split('#')[0]
            # personXX.htmlの形式かチェック
            return bool(re.match(r'^person\d+\.html$', href))
        
        try:
            # 作者リストページのURL
            author_list_url = "https://www.aozora.gr.jp/index_pages/person_all.html"
            self.logger.info(f"作者リストページにアクセス: {author_list_url}")
            
            # ページ取得
            response = self.session.get(author_list_url)
            response.raise_for_status()  # エラーチェック
            
            # エンコーディング検出
            detected = chardet.detect(response.content)
            encoding = detected["encoding"] or "shift_jis"
            self.logger.info(f"検出されたエンコーディング: {encoding}")
            
            # HTMLパース
            html = response.content.decode(encoding, errors="replace")
            soup = BeautifulSoup(html, 'html.parser', from_encoding=encoding)
            
            # 作者名の正規化
            target_name = normalize_name(author_name)
            self.logger.info(f"検索する作者名: {target_name}")
            
            # リンク検索
            for link in soup.find_all('a'):
                link_text = link.text
                normalized_text = normalize_name(link_text)
                href = link.get('href')
                # デバッグ出力
                self.logger.debug(f"リンク: {link_text} -> {normalized_text} (href: {href})")
                
                # 作者名が一致し、かつ有効なpersonXX.htmlの場合
                if normalized_text == target_name and is_valid_person_href(href):
                    # #以降を除去
                    href_clean = href.split('#')[0]
                    # index_pages/の重複を防ぐ
                    if href_clean.startswith("index_pages/"):
                        author_url = f"https://www.aozora.gr.jp/{href_clean}"
                    else:
                        author_url = f"https://www.aozora.gr.jp/index_pages/{href_clean}"
                    self.logger.info(f"作者ページを発見: {author_url}")
                    return author_url
            
            # 作者が見つからない場合
            self.logger.warning(f"作者が見つかりません: {author_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"作者URL取得エラー: {e}")
            return None
    
    def get_works_list(self, author_url: str) -> List[Dict[str, str]]:
        """作者ページから作品リストを取得（<h2>公開中の作品</h2>直後の<ol>内<li>から/cards/リンクを抽出）"""
        self.logger.info(f"作品リスト取得: {author_url}")
        works = []
        try:
            response = self.session.get(author_url)
            detected = chardet.detect(response.content)
            encoding = detected["encoding"] or "shift_jis"
            html = response.content.decode(encoding, errors="replace")
            soup = BeautifulSoup(html, 'html.parser', from_encoding=encoding)

            # <h2>公開中の作品</h2>の直後の<ol>を取得
            h2 = soup.find('h2', string=lambda s: s and '公開中の作品' in s)
            if h2:
                self.logger.info(f"<h2>公開中の作品</h2>を発見: {h2}")
                ol = h2.find_next('ol')
                if ol:
                    self.logger.info(f"<ol>を発見: {ol}")
                else:
                    self.logger.warning('公開中の作品リストが見つかりません')
                    return []
            else:
                self.logger.warning('公開中の作品セクションが見つかりません')
                return []

            for li in ol.find_all('li'):
                a = li.find('a', href=True)
                if a and ('/cards/' in a['href'] or '../cards/' in a['href']):
                    title = a.get_text(strip=True)
                    # 相対パスを絶対パスに変換
                    href = a['href']
                    if href.startswith('../'):
                        href = href[3:]  # '../'を除去
                    xhtml_url = f"https://www.aozora.gr.jp/{href}"
                    # 作品ID抽出
                    m = re.search(r'作品ID：([0-9]+)', li.get_text())
                    work_id = m.group(1) if m else ''
                    works.append({'title': title, 'xhtml_url': xhtml_url, 'work_id': work_id})
                    self.logger.info(f"作品を発見: {title} - {xhtml_url} - 作品ID: {work_id}")

            self.logger.info(f"作品数: {len(works)}件")
            return works
        except Exception as e:
            self.logger.error(f"作品リスト取得エラー: {e}")
            return []
    
    def get_work_text(self, work_url: str) -> Optional[str]:
        """作品のテキストを取得"""
        self.logger.info(f"テキスト取得: {work_url}")
        try:
            xhtml_url = self.get_xhtml_url_from_work_page(work_url)
            if not xhtml_url:
                self.logger.warning(f"XHTML/テキストURLが見つかりません: {work_url}")
                return None
            response = self.session.get(xhtml_url)
            detected = chardet.detect(response.content)
            encoding = detected["encoding"] or "shift_jis"
            content = response.content.decode(encoding, errors="replace")
            self.logger.info(f"取得したXHTML/テキストの先頭: {content[:100]}")
            soup = BeautifulSoup(content, 'html.parser', from_encoding=encoding)
            main_text = None
            # まずdiv.main_textを探す
            main_div = soup.find('div', class_='main_text')
            if main_div:
                main_text = main_div.get_text(separator='\n', strip=True)
            # 見つからない場合はbodyタグから取得
            if not main_text:
                body = soup.find('body')
                if body:
                    # 不要なタグを削除
                    for tag in body.find_all(['script', 'style', 'nav', 'header', 'footer']):
                        tag.decompose()
                    main_text = body.get_text(separator='\n', strip=True)
            if not main_text:
                self.logger.warning(f"本文が見つかりません: {xhtml_url}")
                return None
            # テキストの正規化
            normalized_text = self._normalize_aozora_text(main_text)
            if len(normalized_text) < 100:  # 短すぎる場合は警告
                self.logger.warning(f"テキストが短すぎます: {len(normalized_text)}文字")
            return normalized_text
        except Exception as e:
            self.logger.error(f"テキスト取得エラー: {e}")
            return None
    
    def _normalize_aozora_text(self, raw_text: str) -> str:
        """青空文庫テキストの正規化"""
        text = raw_text
        
        # 1. ヘッダー・フッター除去
        text = self._remove_metadata(text)
        
        # 2. ルビ記法処理
        text = self._process_ruby(text)
        
        # 3. 注記・記法除去
        text = self._remove_annotations(text)
        
        # 4. 改行・空白正規化
        text = self._normalize_whitespace(text)
        
        return text.strip()
    
    def _remove_metadata(self, text: str) -> str:
        """ヘッダー・フッター情報を除去"""
        lines = text.split('\n')
        content_lines = []
        in_content = False
        
        for line in lines:
            line = line.strip()
            
            # ヘッダー終了・本文開始の検出
            if not in_content:
                # メタデータ行をスキップ
                if (line.startswith('底本：') or line.startswith('入力：') or 
                    line.startswith('校正：') or line.startswith('※') or
                    '------' in line or line == '' or 
                    '青空文庫' in line):
                    continue
                else:
                    # 本文開始
                    in_content = True
            
            if in_content:
                content_lines.append(line)
        
        return '\n'.join(content_lines)
    
    def _process_ruby(self, text: str) -> str:
        """ルビ記法を処理"""
        # ルビ記法を除去
        text = re.sub(r'《[^》]*》', '', text)
        return text
    
    def _remove_annotations(self, text: str) -> str:
        """注記・記法を除去"""
        # 注記を除去
        text = re.sub(r'［[^］]*］', '', text)
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """改行・空白を正規化"""
        # 連続する改行を1つに
        text = re.sub(r'\n+', '\n', text)
        # 連続する空白を1つに
        text = re.sub(r' +', ' ', text)
        return text.strip()
    
    def process_author(self, author_name: str) -> List[Dict[str, str]]:
        """作者の全作品を処理"""
        author_url = self.get_author_url(author_name)
        if not author_url:
            self.logger.warning(f"作者ページが見つかりません: {author_name}")
            return []
        
        works = self.get_works_list(author_url)
        if not works:
            self.logger.warning(f"作品リストが取得できませんでした: {author_name}")
            return []
            
        results = []
        for work in works:
            self.logger.info(f"作品テキスト取得開始: {work['title']}")
            text = self.get_work_text(work['xhtml_url'])
            if text:
                results.append({
                    'title': work['title'],
                    'text': text,
                    'url': work['xhtml_url']
                })
                self.logger.info(f"作品テキスト取得完了: {work['title']}")
            else:
                self.logger.warning(f"作品テキストの取得に失敗: {work['title']}")
            time.sleep(1)  # サーバー負荷軽減
        
        self.logger.info(f"全作品の処理が完了しました: {len(results)}件")
        return results

    def get_all_authors(self) -> List[str]:
        """青空文庫の全作家名を取得する"""
        try:
            # HTMLを取得
            response = requests.get(self.author_list_url)
            # エンコーディング自動判定
            detected = chardet.detect(response.content)
            encoding = detected["encoding"] or "shift_jis"
            html = response.content.decode(encoding, errors="replace")
            
            # デバッグ用にHTMLを保存
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(html)
            
            # BeautifulSoupでパース
            soup = BeautifulSoup(html, "html.parser", from_encoding=encoding)
            
            # デバッグ用に最初の10個のli要素を出力
            logger.info("First 10 li elements:")
            for li in soup.find_all("li")[:10]:
                logger.info(f"  {li.text.strip()}")
            
            # 作家名を抽出
            authors = []
            for li in soup.find_all("li"):
                text = li.text.strip()
                if "公開中：" in text:
                    # 「公開中：」の前の部分を作家名として抽出
                    author_name = text.split("公開中：")[0].strip()
                    # 正規化して追加
                    normalized_name = unicodedata.normalize("NFKC", author_name)
                    if normalized_name and not normalized_name.startswith("→"):
                        authors.append(normalized_name)
            
            # 重複を除去してソート
            authors = sorted(set(authors))
            
            # デバッグ用に最初の10件を出力
            logger.info(f"Found {len(authors)} authors. First 10: {authors[:10]}")
            
            return authors
            
        except Exception as e:
            logger.error(f"Error fetching authors: {e}")
            return []

    def save_authors_to_file(self, output_file: str = "authors.txt") -> None:
        """作家名リストをファイルに保存する"""
        authors = self.get_all_authors()
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(authors))
            logger.info(f"Saved {len(authors)} authors to {output_file}")
        except Exception as e:
            logger.error(f"Error saving authors to file: {e}")

    def get_author_page_url(self, author_name: str) -> Optional[str]:
        """作者ページのURLを取得"""
        try:
            # 作者検索ページのURL
            search_url = self.author_list_url
            response = requests.get(search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # 作者名でリンクを検索
            author_link = soup.find('a', text=re.compile(author_name))
            
            if author_link:
                return f"{self.author_list_url}/{author_link['href']}"
            return None
            
        except Exception as e:
            logger.error(f"作者ページURL取得エラー: {e}")
            return None

    def get_works_from_author_page(self, author_url: str) -> List[Dict[str, str]]:
        """作者ページから作品タイトルと作品ページURLのリストを取得"""
        self.logger.info(f"作品リスト取得: {author_url}")
        works = []
        try:
            # #sakuhin_list_1 を自動付加
            if '#sakuhin_list_1' not in author_url:
                if author_url.endswith('.html'):
                    author_url += '#sakuhin_list_1'
                else:
                    author_url = author_url.rstrip('/') + '.html#sakuhin_list_1'
            response = self.session.get(author_url)
            detected = chardet.detect(response.content)
            encoding = detected["encoding"] or "shift_jis"
            html = response.content.decode(encoding, errors="replace")
            soup = BeautifulSoup(html, 'html.parser', from_encoding=encoding)
            # <li>タグ内の<a>タグから作品リストを抽出
            for li in soup.find_all('li'):
                a = li.find('a')
                if a and a.get('href') and a.get('href').endswith('.html'):
                    title = a.get_text(strip=True)
                    work_link = urljoin(self.author_list_url, a.get('href'))
                    works.append({'title': title, 'work_url': work_link})
                    self.logger.info(f"作品: {title} - {work_link}")
            self.logger.info(f"作品数: {len(works)}件")
            return works
        except Exception as e:
            self.logger.error(f"作品リスト取得エラー: {e}")
            return []

    def get_xhtml_url_from_work_page(self, work_url: str) -> Optional[str]:
        """作品ページからXHTMLファイルまたはテキストファイルのURLを取得"""
        self.logger.info(f"XHTML/テキストリンク取得: {work_url}")
        try:
            response = self.session.get(work_url)
            detected = chardet.detect(response.content)
            encoding = detected["encoding"] or "shift_jis"
            html = response.content.decode(encoding, errors="replace")
            soup = BeautifulSoup(html, 'html.parser', from_encoding=encoding)
            # まずXHTMLファイルを探す
            for a in soup.find_all('a'):
                href = a.get('href')
                if href and href.endswith('.html') and 'files/' in href:
                    if 'XHTML' in a.text:
                        xhtml_url = urljoin(work_url, href)
                        self.logger.info(f"XHTMLリンク発見: {xhtml_url}")
                        return xhtml_url
            # 次にテキストファイル（*_*.html）を探す
            for a in soup.find_all('a'):
                href = a.get('href')
                if href and href.endswith('.html') and re.match(r'.*/\d+_\d+\.html$', href):
                    text_url = urljoin(work_url, href)
                    self.logger.info(f"テキストリンク発見: {text_url}")
                    return text_url
            self.logger.warning(f"XHTML/テキストリンクが見つかりません: {work_url}")
            return None
        except Exception as e:
            self.logger.error(f"XHTML/テキストリンク取得エラー: {e}")
            return None

    def get_text_from_xhtml_url(self, xhtml_url: str) -> Optional[str]:
        """XHTMLファイルのURLから本文テキストを抽出"""
        self.logger.info(f"本文取得: {xhtml_url}")
        try:
            response = self.session.get(xhtml_url)
            detected = chardet.detect(response.content)
            encoding = detected["encoding"] or "shift_jis"
            html = response.content.decode(encoding, errors="replace")
            soup = BeautifulSoup(html, 'html.parser', from_encoding=encoding)
            main_text = soup.find('div', class_='main_text')
            if not main_text:
                self.logger.warning("本文が見つかりません")
                return None
            text = main_text.get_text()
            text = unicodedata.normalize('NFKC', text)
            return text
        except Exception as e:
            self.logger.error(f"本文取得エラー: {e}")
            return None

    def save_author(self, author_name: str) -> Optional[int]:
        """作者情報を保存"""
        try:
            author = Author(
                author_name=author_name,
                source_system='aozora'
            )
            return self.db_manager.save_author(author)
        except Exception as e:
            logger.error(f"作者保存エラー: {e}")
            return None
    
    def save_work(self, author_id: int, title: str, aozora_url: str) -> Optional[int]:
        """作品情報を保存"""
        try:
            work = Work(
                work_title=title,
                author_id=author_id,
                aozora_url=aozora_url,
                source_system='aozora'
            )
            return self.db_manager.save_work(work)
        except Exception as e:
            logger.error(f"作品保存エラー: {e}")
            return None
    
    def save_sentences(self, content: str) -> List[Dict[str, Any]]:
        """センテンスを保存"""
        try:
            # テキストをセンテンスに分割
            sentences = re.split(r'[。．！？]', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            saved_sentences = []
            for i, text in enumerate(sentences):
                if len(text) < 5:  # 短すぎる文をスキップ
                    continue
                
                sentence = {
                    'sentence_text': text,
                    'position_in_work': i + 1,
                    'sentence_length': len(text)
                }
                saved_sentences.append(sentence)
            
            return saved_sentences
            
        except Exception as e:
            self.logger.error(f"センテンス保存エラー: {e}")
            return []
    
    def scrape_author_works(self, author_name: str) -> Tuple[Optional[int], int]:
        """作者の作品をスクレイピングして保存"""
        try:
            # 作者ページのURLを取得
            author_url = self.get_author_url(author_name)
            if not author_url:
                logger.error(f"作者ページが見つかりません: {author_name}")
                return None, 0
            
            # 作者情報を保存
            author_id = self.save_author(author_name)
            if not author_id:
                logger.error(f"作者情報の保存に失敗しました: {author_name}")
                return None, 0
            
            # 作品一覧を取得
            works = self.get_works_list(author_url)
            saved_works = 0
            
            for work in works:
                # 作品情報を保存
                work_id = self.save_work(author_id, work['title'], work['xhtml_url'])
                if not work_id:
                    continue
                
                # 作品本文を取得
                content = self.get_work_text(work['xhtml_url'])
                if not content:
                    continue
                
                # センテンスを保存
                saved_sentences = self.save_sentences(content)
                if saved_sentences:
                    saved_works += 1
            
            return author_id, saved_works
            
        except Exception as e:
            logger.error(f"作者作品スクレイピングエラー: {e}")
            return None, 0

# サンプルコード
if __name__ == "__main__":
    scraper = AozoraScraper()
    author_name = "梶井 基次郎"
    author_url = scraper.get_author_url(author_name)
    if author_url:
        works = scraper.get_works_list(author_url)
        print(f"取得した作品数: {len(works)}")
        for work in works:
            print(f"作品: {work['title']} - URL: {work['xhtml_url']}")
            text = scraper.get_work_text(work['xhtml_url'])
            if text:
                print(f"本文冒頭: {text[:100]}...")
            else:
                print("本文取得失敗")
    else:
        print(f"作者ページが見つかりません: {author_name}") 