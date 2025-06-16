#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪ゆかり地図システム v4.0
メインCLIインターフェース
"""

import click
import logging
from rich.console import Console
from rich.progress import Progress
from typing import List, Dict, Any
from pathlib import Path

from ..core.pipeline import MainPipeline
from ..database.manager import DatabaseManager
from ..database.schema_manager import SchemaManager
from ..extractors.aozora_scraper import AozoraScraper

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Richコンソール
console = Console()

@click.group()
def cli():
    """文豪ゆかり地図システム v4.0"""
    pass

@cli.command()
@click.option('--db-path', default='/app/bungo-map-v4/data/databases/bungo_v4.db',
              help='データベースファイルのパス')
@click.option('--author', required=True, help='著者名')
def process_author(db_path: str, author: str):
    """作者の全作品を処理"""
    try:
        # データベースの初期化
        schema_manager = SchemaManager(db_path)
        schema_manager._init_schema()
        
        # データベースマネージャーの初期化
        db_manager = DatabaseManager(db_path)
        
        # 青空文庫スクレイパーの初期化
        scraper = AozoraScraper(db_manager)
        
        # 作者の作品をスクレイピング
        console.print(f"[cyan]🔍 作者の作品を検索中: {author}[/cyan]")
        author_id, saved_works = scraper.scrape_author_works(author)
        
        if author_id:
            console.print(f"[green]✅ 作者の処理が完了しました[/green]")
            console.print(f"📚 保存された作品数: {saved_works}")
            
            # 統計情報の表示
            stats = db_manager.get_author_statistics(author_id)
            console.print("\n[bold]📊 作者の統計情報[/bold]")
            console.print(f"📝 総センテンス数: {stats['total_sentences']:,}")
            console.print(f"🗺️ 抽出地名数: {stats['total_places']:,}")
            console.print(f"🌍 ジオコーディング済み: {stats['geocoded_places']:,}")
        else:
            console.print(f"[red]❌ 作者の処理に失敗しました[/red]")
    
    except Exception as e:
        logger.error(f"作者処理エラー: {e}")
        console.print(f"[red]❌ エラー: {e}[/red]")

@cli.command()
@click.option('--db-path', default='/app/bungo-map-v4/data/databases/bungo_v4.db',
              help='データベースファイルのパス')
@click.option('--author', required=True, help='著者名')
@click.option('--title', required=True, help='作品タイトル')
def process_work(db_path: str, author: str, title: str):
    """単一作品の処理"""
    try:
        pipeline = MainPipeline(db_path)
        result = pipeline.process_work(author, title)
        
        if result.success:
            console.print(f"[green]✅ 処理完了: {author} - {title}[/green]")
            console.print(f"📊 抽出地名数: {len(result.extracted_places)}")
            console.print(f"⏱️ 処理時間: {result.processing_time:.1f}秒")
        else:
            console.print(f"[red]❌ 処理失敗: {result.error_message}[/red]")
    
    except Exception as e:
        logger.error(f"処理エラー: {e}")
        console.print(f"[red]❌ エラー: {e}[/red]")

@cli.command()
@click.option('--db-path', default='/app/bungo-map-v4/data/databases/bungo_v4.db',
              help='データベースファイルのパス')
@click.option('--input-file', required=True, type=click.Path(exists=True),
              help='作品リストのJSONファイル')
def process_batch(db_path: str, input_file: str):
    """複数作品の一括処理"""
    try:
        import json
        with open(input_file, 'r', encoding='utf-8') as f:
            works = json.load(f)
        
        pipeline = MainPipeline(db_path)
        results = pipeline.process_batch(works)
        
        # 結果集計
        success_count = sum(1 for r in results if r.success)
        total_places = sum(len(r.extracted_places) for r in results if r.success)
        avg_time = sum(r.processing_time for r in results) / len(results)
        
        console.print("\n[bold]📊 処理結果サマリー[/bold]")
        console.print(f"✅ 成功: {success_count}/{len(works)}")
        console.print(f"🗺️ 総地名数: {total_places}")
        console.print(f"⏱️ 平均処理時間: {avg_time:.1f}秒")
        
        # 失敗した作品の表示
        failed = [(w, r) for w, r in zip(works, results) if not r.success]
        if failed:
            console.print("\n[red]❌ 失敗した作品:[/red]")
            for work, result in failed:
                console.print(f"  • {work['author']} - {work['title']}: {result.error_message}")
    
    except Exception as e:
        logger.error(f"一括処理エラー: {e}")
        console.print(f"[red]❌ エラー: {e}[/red]")

@cli.command()
@click.option('--db-path', default='/app/bungo-map-v4/data/databases/bungo_v4.db',
              help='データベースファイルのパス')
def show_statistics(db_path: str):
    """統計情報の表示"""
    try:
        pipeline = MainPipeline(db_path)
        stats = pipeline.get_statistics()
        
        console.print("\n[bold]📊 システム統計情報[/bold]")
        console.print(f"👥 作家数: {stats['authors']:,}")
        console.print(f"📚 作品数: {stats['works']:,}")
        console.print(f"🗺️ 地名数: {stats['places']:,}")
        console.print(f"🌍 ジオコーディング済み: {stats['geocoded_places']:,}")
        console.print(f"⏱️ 平均処理時間: {stats['processing_time']:.1f}秒")
    
    except Exception as e:
        logger.error(f"統計情報取得エラー: {e}")
        console.print(f"[red]❌ エラー: {e}[/red]")

if __name__ == '__main__':
    cli() 