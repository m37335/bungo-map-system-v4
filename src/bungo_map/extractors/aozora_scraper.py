from typing import List, Dict, Tuple, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import chardet
import logging
import requests
import unicodedata
import re
import sys

class AozoraScraper:
    def __init__(self, db_manager=None):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.db_manager = db_manager
        self.base_url = "https://www.aozora.gr.jp"
        self.author_list_url = "https://www.aozora.gr.jp/index_pages/person_all.html"
    
    def scrape_author_works(self, author_name: str) -> Tuple[int, int]:
        """作者の作品をスクレイピングして保存"""
        self.logger.info(f"作者検索: {author_name}")
        
        try:
            # 作者ページのURLを取得
            author_url = self.get_author_url(author_name)
            print(f"【DEBUG: scrape_author_works内のauthor_url】author_url = {author_url}")
            self.logger.info(f"【DEBUG: get_author_urlの返り値】author_url = {author_url}")
            self.logger.info(f"DEBUG: scrape_author_works: author_url = {author_url}")
            
            if author_url is None:
                self.logger.error("作者ページが見つかりません")
                return None, 0
            
            # 作品リストを取得
            works = self.get_works_list(author_url)
            
            # 作者情報を保存
            author = {
                'author_name': author_name,
                'source_system': 'aozora'
            }
            author_id = self.db_manager.save_author(author)
            
            if not author_id:
                self.logger.error("作者情報の保存に失敗")
                return None, 0
            
            # 作品情報を保存
            saved_works = 0
            for work in works:
                work_info = {
                    'work_title': work['title'],
                    'author_id': author_id,
                    'aozora_url': work['url'],
                    'source_system': 'aozora'
                }
                if self.db_manager.save_work(work_info):
                    saved_works += 1
            
            return author_id, saved_works
            
        except Exception as e:
            self.logger.error(f"作者作品取得エラー: {e}")
            return None, 0
    
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
                print(f"href: {href}")
                # デバッグ出力
                self.logger.debug(f"リンク: {link_text} -> {normalized_text} (href: {href})")
                
                # 作者名が一致し、かつ有効なpersonXX.htmlの場合
                if normalized_text == target_name and is_valid_person_href(href):
                    # #以降を除去
                    href_clean = href.split('#')[0]
                    print(f"href_clean: {href_clean}")  
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
            
        except requests.RequestException as e:
            self.logger.error(f"作者リストページの取得に失敗: {e}")
            return None
        except Exception as e:
            self.logger.error(f"予期せぬエラー: {e}")
            return None
    
    def get_works_list(self, author_url: str) -> List[Dict[str, str]]:
        """作者ページから作品リストを取得（再設計・最小堅牢版）"""
        self.logger.info(f"作品リスト取得: {author_url}")
        works = []
        try:
            response = self.session.get(author_url)
            detected = chardet.detect(response.content)
            encoding = detected["encoding"] or "shift_jis"
            html = response.content.decode(encoding, errors="replace")
            soup = BeautifulSoup(html, 'html.parser', from_encoding=encoding)
            # 「公開中の作品」セクションを探す
            for h2 in soup.find_all('h2'):
                if h2.text.strip() == '公開中の作品':
                    ol = h2.find_next('ol')
                    if ol:
                        for li in ol.find_all('li'):
                            a_tag = li.find('a')
                            if a_tag:
                                title = a_tag.text.strip()
                                href = a_tag.get('href', '')
                                if href.startswith('/cards/'):
                                    work_url = 'https://www.aozora.gr.jp' + href
                                    works.append({'title': title, 'url': work_url})
            self.logger.info(f"作品数: {len(works)}件")
            return works
        except Exception as e:
            self.logger.error(f"作品リスト取得エラー: {e}")
            return [] 