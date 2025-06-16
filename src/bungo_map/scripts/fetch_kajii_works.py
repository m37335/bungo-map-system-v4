"""
梶井基次郎の作品を取得するスクリプト

青空文庫から梶井基次郎の作品を取得し、データベースに保存する
"""

import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import sys
import os

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

from src.bungo_map.database.manager import DatabaseManager
from src.bungo_map.database.models import Author, Work, Sentence

logger = logging.getLogger(__name__)

class KajiiWorksFetcher:
    """梶井基次郎の作品取得クラス"""
    
    def __init__(self, db_path: str):
        self.db_manager = DatabaseManager(db_path)
        self.base_url = "https://www.aozora.gr.jp"
        self.author_url = f"{self.base_url}/index_pages/person156.html"
    
    def fetch_works(self):
        """作品一覧を取得"""
        try:
            # 作者情報の保存
            author = Author(
                author_name="梶井 基次郎",
                source_system="aozora"
            )
            author_id = self.db_manager.save_author(author)
            if not author_id:
                raise Exception("作者情報の保存に失敗しました")

            # 作品一覧ページの取得
            response = requests.get(self.author_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 作品リストの取得
            work_links = soup.select('ol li a')
            for link in work_links:
                work_title = link.text.strip()
                work_url = f"{self.base_url}/{link['href']}"
                
                # 作品情報の保存
                work = Work(
                    work_title=work_title,
                    author_id=author_id,
                    aozora_url=work_url,
                    source_system="aozora"
                )
                work_id = self.db_manager.save_work(work)
                if not work_id:
                    logger.error(f"作品の保存に失敗: {work_title}")
                    continue

                # 作品本文の取得と保存
                self._fetch_work_content(work_id, author_id, work_url)
                
                logger.info(f"作品を保存: {work_title}")

        except Exception as e:
            logger.error(f"作品取得エラー: {e}")
            raise

    def _fetch_work_content(self, work_id: int, author_id: int, work_url: str):
        """作品本文を取得して保存"""
        try:
            response = requests.get(work_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 本文の取得
            content = soup.select_one('.main_text')
            if not content:
                logger.error(f"本文が見つかりません: {work_url}")
                return

            # 本文をセンテンスに分割
            text = content.get_text()
            sentences = [s.strip() for s in text.split('。') if s.strip()]

            # センテンスの保存
            for i, sentence_text in enumerate(sentences):
                sentence = Sentence(
                    sentence_text=sentence_text,
                    work_id=work_id,
                    author_id=author_id,
                    position_in_work=i,
                    sentence_length=len(sentence_text)
                )
                if not self.db_manager.save_sentence(sentence):
                    logger.error(f"センテンスの保存に失敗: {i}")

        except Exception as e:
            logger.error(f"作品本文取得エラー: {e}")

def main():
    # ロギングの設定
    logging.basicConfig(level=logging.INFO)
    
    # データベースパスの設定
    db_path = str(Path(__file__).parent.parent.parent / "data" / "bungo_map.db")
    
    # 作品取得の実行
    fetcher = KajiiWorksFetcher(db_path)
    fetcher.fetch_works()

if __name__ == "__main__":
    main() 