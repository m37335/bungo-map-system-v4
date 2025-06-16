import click
import logging
from /app/src/bungo_map/extractors/aozora_scraper.py import AozoraScraper
import os

logger = logging.getLogger(__name__)

@click.group()
def cli():
    """青空文庫から作品を取得するCLIツール"""
    pass

@cli.command()
@click.option('--author', required=True, help='作家名')
@click.option('--output-dir', default='data/aozora', help='出力ディレクトリ')
def scrape_author(author: str, output_dir: str):
    """指定された作家の作品を取得する"""
    scraper = AozoraScraper()
    works = scraper.process_author(author)
    os.makedirs(output_dir, exist_ok=True)
    for work in works:
        safe_title = work['title'].replace('/', '_').replace('\\', '_')
        file_path = os.path.join(output_dir, f"{safe_title}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(work['text'])
    logger.info(f"{len(works)}件の作品を{output_dir}に保存しました")

@cli.command()
@click.option('--output-file', default='authors.txt', help='出力ファイル名')
def list_authors(output_file: str):
    """青空文庫の全作家名を取得してファイルに保存する"""
    scraper = AozoraScraper()
    scraper.save_authors_to_file(output_file) 