#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫データベース構築CLI
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

import click
import aiohttp
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from bungo_map.core.database import Database
from bungo_map.extractors.aozora_csv_downloader import AozoraCSVDownloader
from bungo_map.utils.logger import setup_logger

console = Console()
logger = setup_logger(__name__)


@click.group()
def aozora():
    """青空文庫データベース構築コマンド"""
    pass


@aozora.command()
@click.option('--force', '-f', is_flag=True, help='強制的にCSVを再ダウンロード')
def download_csv(force: bool):
    """青空文庫公式CSVファイルをダウンロード"""
    console.print("📚 青空文庫CSVファイルをダウンロード中...", style="blue")
    
    try:
        downloader = AozoraCSVDownloader()
        csv_content = downloader.download_csv_data()
        
        if csv_content:
            console.print("✅ CSVファイルをダウンロードしました", style="green")
            
            # 統計表示
            works = downloader.parse_csv_data(csv_content)
            table = Table(title="青空文庫統計")
            table.add_column("項目", style="cyan")
            table.add_column("件数", style="magenta")
            
            table.add_row("総作品数", f"{len(works):,}")
            
            copyright_free = [w for w in works if w.get('copyright_flag') == 'なし']
            table.add_row("著作権フリー作品", f"{len(copyright_free):,}")
            
            authors = set()
            for w in works:
                if w.get('author_last_name'):
                    authors.add(w['author_last_name'] + w.get('author_first_name', ''))
            table.add_row("ユニーク作家数", f"{len(authors):,}")
            
            console.print(table)
        else:
            console.print("❌ CSVファイルのダウンロードに失敗しました", style="red")
        
    except Exception as e:
        console.print(f"❌ エラー: {e}", style="red")
        sys.exit(1)


@aozora.command()
@click.option('--authors', '-a', help='対象作家（カンマ区切り）')
@click.option('--limit', '-l', type=int, help='作品数制限')
@click.option('--test', '-t', is_flag=True, help='テストモード（実際には登録しない）')
def build_database(authors: Optional[str], limit: Optional[int], test: bool):
    """青空文庫データからデータベースを構築"""
    
    # デフォルト作家リスト
    default_authors = [
        "夏目漱石", "芥川竜之介", "太宰治", "宮沢賢治", "森鴎外",
        "中島敦", "梶井基次郎", "坂口安吾", "与謝野晶子", "中原中也"
    ]
    
    target_authors = authors.split(',') if authors else default_authors
    
    console.print(f"🏗️  青空文庫データベース構築開始", style="blue")
    console.print(f"対象作家: {', '.join(target_authors)}")
    if limit:
        console.print(f"作品数制限: {limit}")
    if test:
        console.print("⚠️ テストモード: 実際の登録は行いません", style="yellow")
    
    try:
        downloader = AozoraCSVDownloader()
        
        # CSVデータを取得
        console.print("📥 青空文庫CSVデータを取得中...", style="yellow")
        csv_content = downloader.download_csv_data()
        if not csv_content:
            console.print("❌ CSVデータの取得に失敗しました", style="red")
            return
        
        asyncio.run(_build_database_async(downloader, csv_content, target_authors, limit, test))
        
    except Exception as e:
        console.print(f"❌ エラー: {e}", style="red")
        logger.exception("Database build failed")
        sys.exit(1)


async def _build_database_async(downloader: AozoraCSVDownloader, 
                               csv_content: str,
                               target_authors: List[str], 
                               limit: Optional[int], 
                               test: bool):
    """非同期でデータベース構築"""
    
    db = Database()
    total_added = 0
    total_processed = 0
    
    # CSVデータを解析
    all_works = downloader.parse_csv_data(csv_content)
    
    stats_table = Table(title="作家別処理結果")
    stats_table.add_column("作家", style="cyan")
    stats_table.add_column("青空文庫作品数", style="blue")
    stats_table.add_column("フィルタ後", style="green")
    stats_table.add_column("追加作品数", style="magenta")
    
    for author_name in target_authors:
        console.print(f"\n📖 {author_name} の作品を処理中...", style="blue")
        
        try:
            # 作品検索とフィルタリング
            works = _search_author_works(all_works, author_name)
            console.print(f"青空文庫作品数: {len(works)}")
            
            filtered_works = _filter_literary_works(works)
            console.print(f"フィルタ後作品数: {len(filtered_works)}")
            
            if limit:
                filtered_works = filtered_works[:limit]
                console.print(f"制限適用後: {len(filtered_works)}")
            
            added_count = 0
            
            # 各作品を処理
            with Progress() as progress:
                task = progress.add_task(f"{author_name}の作品処理", total=len(filtered_works))
                
                async with aiohttp.ClientSession() as session:
                    for work in filtered_works:
                        if not test:
                            added = await _process_single_work(db, downloader, work, session)
                            if added:
                                added_count += 1
                        else:
                            added_count += 1  # テストモードでは全て追加したものとする
                        
                        total_processed += 1
                        progress.update(task, advance=1)
            
            total_added += added_count
            stats_table.add_row(
                author_name,
                str(len(works)),
                str(len(filtered_works)),
                str(added_count)
            )
            
        except Exception as e:
            console.print(f"❌ {author_name}の処理中にエラー: {e}", style="red")
            logger.exception(f"Error processing {author_name}")
    
    # 結果表示
    console.print(stats_table)
    
    summary_table = Table(title="処理サマリー")
    summary_table.add_column("項目", style="cyan")
    summary_table.add_column("値", style="magenta")
    
    summary_table.add_row("処理作品数", f"{total_processed:,}")
    summary_table.add_row("追加作品数", f"{total_added:,}")
    
    if not test:
        # データベース統計
        current_stats = db.get_stats()
        summary_table.add_row("総作品数", f"{current_stats['works']:,}")
        summary_table.add_row("URL設定済み", f"{current_stats['works_with_url']:,}")
        summary_table.add_row("コンテンツ設定済み", f"{current_stats['works_with_content']:,}")
    
    console.print(summary_table)
    
    if test:
        console.print("✅ テストモード完了（実際の登録は行われませんでした）", style="green")
    else:
        console.print("✅ データベース構築完了", style="green")


def _search_author_works(all_works: List[Dict], author_name: str) -> List[Dict]:
    """作家名から作品を検索"""
    author_works = []
    for work in all_works:
        full_name = f"{work['author_last_name']}{work['author_first_name']}"
        if full_name == author_name:
            author_works.append(work)
    return author_works


def _filter_literary_works(works: List[Dict]) -> List[Dict]:
    """文学作品のみフィルタリング"""
    exclude_keywords = [
        '詩集', '歌集', '全集', '書簡', '日記', '随筆集', '評論', 
        '講演', '座談', '対談', '翻訳', '童謡', '短歌', '俳句', '詩'
    ]
    
    filtered = []
    for work in works:
        title = work.get('title', '')
        if work.get('copyright_flag') == 'なし':  # 著作権フリーのみ
            exclude = False
            for keyword in exclude_keywords:
                if keyword in title:
                    exclude = True
                    break
            if not exclude:
                filtered.append(work)
    
    return filtered


async def _process_single_work(db: Database, downloader: AozoraCSVDownloader, 
                              work: dict, session: aiohttp.ClientSession) -> bool:
    """単一作品の処理"""
    try:
        # 作家情報の追加/取得
        author_id = db.add_author(
            name=work['author_last_name'] + work['author_first_name'],
            birth_year=None,  # 後で更新可能
            death_year=None
        )
        
        # 作品の追加
        work_id = db.add_work(
            title=work['title'],
            author_id=author_id,
            publication_year=None,  # 青空文庫CSVには発行年がない
            aozora_url=work.get('html_url'),
            text_url=work.get('text_url')
        )
        
        if work_id and work.get('text_url'):
            # テキストコンテンツの取得と設定
            try:
                content = downloader.extract_content_from_url(work['text_url'])
                if content:
                    db.set_work_content(work_id, content)
                    return True
            except Exception as e:
                logger.warning(f"Failed to get content for {work['title']}: {e}")
                return True  # URLは設定できているので部分的成功
        
        return bool(work_id)
        
    except Exception as e:
        logger.error(f"Failed to process work {work['title']}: {e}")
        return False


@aozora.command()
def stats():
    """現在のデータベース統計を表示"""
    console.print("📊 データベース統計", style="blue")
    
    try:
        db = Database()
        stats = db.get_stats()
        
        table = Table(title="データベース統計")
        table.add_column("項目", style="cyan")
        table.add_column("件数", style="magenta")
        table.add_column("割合", style="green")
        
        table.add_row("作家数", f"{stats['authors']:,}", "-")
        table.add_row("作品数", f"{stats['works']:,}", "-")
        table.add_row("地名数", f"{stats['places']:,}", "-")
        
        if stats['works'] > 0:
            url_rate = stats['works_with_url'] / stats['works'] * 100
            content_rate = stats['works_with_content'] / stats['works'] * 100
            
            table.add_row("URL設定済み", f"{stats['works_with_url']:,}", f"{url_rate:.1f}%")
            table.add_row("コンテンツ設定済み", f"{stats['works_with_content']:,}", f"{content_rate:.1f}%")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ エラー: {e}", style="red")
        sys.exit(1)


if __name__ == '__main__':
    aozora() 