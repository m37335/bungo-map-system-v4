#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベース管理CLI
"""

import click
import logging
from rich.console import Console
from rich.panel import Panel
from ..database.init_db import DatabaseInitializer
from ..database.seed_data import TestDataSeeder

logger = logging.getLogger(__name__)
console = Console()

@click.group()
def database():
    """データベース管理コマンド"""
    pass

@database.command()
@click.option('--force', '-f', is_flag=True, help='既存のデータベースを上書き')
def init(force):
    """データベースの初期化"""
    try:
        initializer = DatabaseInitializer()
        
        if initializer.initialize():
            if initializer.verify_initialization():
                console.print(Panel(
                    "[green]✅ データベースの初期化と検証が成功しました[/green]",
                    title="データベース初期化"
                ))
            else:
                console.print(Panel(
                    "[red]❌ データベースの検証に失敗しました[/red]",
                    title="データベース初期化"
                ))
        else:
            console.print(Panel(
                "[red]❌ データベースの初期化に失敗しました[/red]",
                title="データベース初期化"
            ))
    
    except Exception as e:
        logger.error(f"データベース初期化エラー: {e}")
        console.print(Panel(
            f"[red]❌ エラー: {str(e)}[/red]",
            title="データベース初期化"
        ))

@database.command()
def seed():
    """テストデータの投入"""
    try:
        seeder = TestDataSeeder()
        
        if seeder.seed_test_data():
            console.print(Panel(
                "[green]✅ テストデータの投入が成功しました[/green]",
                title="テストデータ投入"
            ))
        else:
            console.print(Panel(
                "[red]❌ テストデータの投入に失敗しました[/red]",
                title="テストデータ投入"
            ))
    
    except Exception as e:
        logger.error(f"テストデータ投入エラー: {e}")
        console.print(Panel(
            f"[red]❌ エラー: {str(e)}[/red]",
            title="テストデータ投入"
        ))

@database.command()
def stats():
    """データベース統計情報の表示"""
    try:
        initializer = DatabaseInitializer()
        
        with initializer.schema_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # テーブルごとのレコード数を取得
            tables = ['authors', 'works', 'sentences', 'places_master', 'sentence_places']
            stats = {}
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            
            # 統計情報を表示
            console.print(Panel(
                f"[bold]📊 データベース統計[/bold]\n\n"
                f"👥 作者数: {stats['authors']:,}\n"
                f"📚 作品数: {stats['works']:,}\n"
                f"📝 センテンス数: {stats['sentences']:,}\n"
                f"🗺️ 地名数: {stats['places_master']:,}\n"
                f"🔗 文-地名関係数: {stats['sentence_places']:,}",
                title="データベース統計"
            ))
    
    except Exception as e:
        logger.error(f"統計情報取得エラー: {e}")
        console.print(Panel(
            f"[red]❌ エラー: {str(e)}[/red]",
            title="データベース統計"
        ))

def main():
    """メイン関数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    database()

if __name__ == "__main__":
    main() 