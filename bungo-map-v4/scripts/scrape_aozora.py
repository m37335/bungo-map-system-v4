#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫スクレイピングスクリプト

梶井基次郎の作品を青空文庫から取得し、データベースに保存する
"""

import logging
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.bungo_map.database.manager import DatabaseManager
from src.bungo_map.extractors.aozora_scraper import AozoraScraper

def main():
    """メイン関数"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    try:
        # データベースマネージャーの初期化
        logger.info("🗃️ データベースを初期化します")
        db_manager = DatabaseManager()
        logger.info("🌟 データベースマネージャーv4初期化完了")

        # スクレイパーの初期化
        scraper = AozoraScraper(db_manager=db_manager)

        # 梶井基次郎の作品をスクレイピング
        logger.info("📚 梶井基次郎の作品をスクレイピングします")
        author_name = "梶井 基次郎"
        author_id, saved_works = scraper.scrape_author_works(author_name)

        if author_id:
            logger.info(f"✅ 作者ID: {author_id}")
            logger.info(f"📚 保存された作品数: {len(saved_works)}")
            for work in saved_works:
                logger.info(f"📖 {work['title']}")
        else:
            logger.error("❌ スクレイピングに失敗しました")

    except Exception as e:
        logger.error(f"❌ エラーが発生しました: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 