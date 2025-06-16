#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫スクレイパーCLI
"""

import click
import json
import os
from pathlib import Path
from ..extractors.aozora_scraper import AozoraScraper

@click.group()
def aozora():
    """青空文庫スクレイパー"""
    pass

@aozora.command()
@click.option('--author', required=True, help='作家名（例：夏目 漱石）')
@click.option('--output-dir', default='data/aozora', help='出力ディレクトリ')
def scrape_author(author, output_dir):
    """指定作家の全作品を取得"""
    scraper = AozoraScraper()
    
    # 出力ディレクトリ作成
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 作者の作品を取得
    works = scraper.process_author(author)
    
    if not works:
        click.echo(f"❌ 作品が見つかりませんでした: {author}")
        return
    
    # 結果を保存
    author_dir = output_path / author.replace(' ', '_')
    author_dir.mkdir(exist_ok=True)
    
    for work in works:
        title = work['title']
        text = work['text']
        
        # ファイル名を安全に作成
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        
        # テキストファイルとして保存
        text_file = author_dir / f"{safe_title}.txt"
        text_file.write_text(text, encoding='utf-8')
        
        click.echo(f"✅ 保存: {text_file}")
    
    click.echo(f"✨ 完了: {len(works)}作品を保存しました")

if __name__ == '__main__':
    aozora() 