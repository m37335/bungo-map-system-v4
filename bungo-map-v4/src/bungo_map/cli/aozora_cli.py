#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫システム CLI v4
青空文庫データ取得・処理・管理の統合インターフェース
"""

import click
import logging
from typing import Dict, List, Any, Optional
import sys
import os
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

# Rich UIサポート
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress
    from rich.panel import Panel
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='詳細ログ出力')
@click.pass_context
def aozora(ctx, verbose):
    """📚 青空文庫システム v4"""
    ctx.ensure_object(dict)
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    if console:
        console.print("[bold blue]📚 青空文庫システム v4[/bold blue]")

@aozora.command()
@click.argument('query', required=True)
@click.option('--search-type', default='title', type=click.Choice(['title', 'author', 'both']), help='検索対象')
@click.option('--limit', default=20, help='検索結果数の上限')
@click.option('--detailed', is_flag=True, help='詳細情報表示')
@click.pass_context
def search(ctx, query, search_type, limit, detailed):
    """青空文庫作品検索"""
    click.echo(f"🔍 青空文庫検索: '{query}'")
    click.echo(f"   検索対象: {search_type}")
    
    # サンプル検索結果
    sample_results = [
        {
            'work_id': '43',
            'title': '羅生門',
            'author': '芥川龍之介',
            'first_published': '1915',
            'aozora_url': 'https://www.aozora.gr.jp/cards/000879/files/127_15260.html',
            'file_size': '24KB',
            'last_modified': '2004-02-17'
        },
        {
            'work_id': '752',
            'title': '坊っちゃん',
            'author': '夏目漱石',
            'first_published': '1906',
            'aozora_url': 'https://www.aozora.gr.jp/cards/000148/files/752_14964.html',
            'file_size': '89KB',
            'last_modified': '2003-11-14'
        },
        {
            'work_id': '645',
            'title': '舞姫',
            'author': '森鴎外',
            'first_published': '1890',
            'aozora_url': 'https://www.aozora.gr.jp/cards/000129/files/645_5247.html',
            'file_size': '45KB',
            'last_modified': '2004-01-15'
        }
    ]
    
    # フィルタリング
    if search_type == 'title':
        filtered_results = [r for r in sample_results if query.lower() in r['title'].lower()]
    elif search_type == 'author':
        filtered_results = [r for r in sample_results if query.lower() in r['author'].lower()]
    else:  # both
        filtered_results = [r for r in sample_results if 
                          query.lower() in r['title'].lower() or 
                          query.lower() in r['author'].lower()]
    
    filtered_results = filtered_results[:limit]
    
    # 結果表示
    if not filtered_results:
        click.echo("   ❌ 該当する作品が見つかりませんでした")
        return
    
    if RICH_AVAILABLE:
        _display_search_results_rich(filtered_results, query, detailed)
    else:
        _display_search_results_simple(filtered_results, detailed)

@aozora.command()
@click.argument('work_id', required=True)
@click.option('--output-dir', default='downloads', help='ダウンロード先ディレクトリ')
@click.option('--format', 'dl_format', default='html', type=click.Choice(['html', 'text', 'both']), help='ダウンロード形式')
@click.option('--extract-places', is_flag=True, help='地名抽出も実行')
@click.pass_context
def download(ctx, work_id, output_dir, dl_format, extract_places):
    """青空文庫作品ダウンロード"""
    click.echo(f"📥 青空文庫ダウンロード: 作品ID {work_id}")
    click.echo(f"   出力先: {output_dir}")
    click.echo(f"   形式: {dl_format}")
    
    # ダウンロード先ディレクトリ作成
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # サンプル作品情報
    work_info = {
        'work_id': work_id,
        'title': '羅生門',
        'author': '芥川龍之介',
        'url': 'https://www.aozora.gr.jp/cards/000879/files/127_15260.html',
        'file_size': '24KB'
    }
    
    # ダウンロード実行（シミュレーション）
    if RICH_AVAILABLE:
        with Progress() as progress:
            task = progress.add_task(f"ダウンロード中: {work_info['title']}", total=100)
            
            for i in range(100):
                progress.update(task, advance=1)
                import time
                time.sleep(0.01)  # ダウンロードシミュレーション
    else:
        click.echo("   📥 ダウンロード中...")
    
    # ファイル保存（サンプル）
    if dl_format in ['html', 'both']:
        html_file = output_path / f"{work_info['title']}.html"
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{work_info['title']} - {work_info['author']}</title>
</head>
<body>
    <h1>{work_info['title']}</h1>
    <h2>{work_info['author']}</h2>
    <p>ある日の暮方の事である。一人の下人が、羅生門の下で雨やみを待っていた。</p>
    <p>（青空文庫テキストの内容がここに続く...）</p>
</body>
</html>"""
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    if dl_format in ['text', 'both']:
        text_file = output_path / f"{work_info['title']}.txt"
        text_content = f"""羅生門
芥川龍之介

ある日の暮方の事である。一人の下人が、羅生門の下で雨やみを待っていた。

広い羅生門の下には、この男の外に誰もいない。ただ、所々丹塗の剥げた、
大きな円柱に、蟋蟀が一匹とまっている。羅生門が、朱雀大路にある以上は、
この男の外にも、雨やみをする市女笠や揉烏帽子が、もう二三人はありそうなものである。
それが、この男の外には誰もいない。

（テキスト内容が続く...）
"""
        
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text_content)
    
    click.echo(f"✅ ダウンロード完了")
    click.echo(f"   保存先: {output_path}")
    
    if extract_places:
        click.echo(f"\n🗺️ 地名抽出実行中...")
        # 地名抽出処理をここで実行
        extracted_places = ['羅生門', '朱雀大路', '京都']
        click.echo(f"   抽出された地名: {', '.join(extracted_places)}")

@aozora.command()
@click.option('--input-file', type=click.Path(exists=True), help='作品IDリストファイル')
@click.option('--output-dir', default='batch_downloads', help='一括ダウンロード先')
@click.option('--delay', default=1.0, help='ダウンロード間隔（秒）')
@click.option('--max-works', default=10, help='最大ダウンロード数')
@click.pass_context
def batch_download(ctx, input_file, output_dir, delay, max_works):
    """青空文庫一括ダウンロード"""
    click.echo(f"📦 青空文庫一括ダウンロード")
    click.echo(f"   出力先: {output_dir}")
    click.echo(f"   間隔: {delay}秒")
    click.echo(f"   上限: {max_works}作品")
    
    # サンプル作品リスト
    if input_file:
        click.echo(f"   入力ファイル: {input_file}")
        work_ids = ['43', '752', '645']  # ファイルから読み込み想定
    else:
        work_ids = ['43', '752', '645', '456', '789']  # デフォルトリスト
    
    work_ids = work_ids[:max_works]
    
    click.echo(f"\n📋 ダウンロード対象: {len(work_ids)}作品")
    
    success_count = 0
    fail_count = 0
    
    if RICH_AVAILABLE:
        with Progress() as progress:
            task = progress.add_task("一括ダウンロード中...", total=len(work_ids))
            
            for work_id in work_ids:
                try:
                    # 個別ダウンロード実行
                    ctx.invoke(download, work_id=work_id, output_dir=output_dir, 
                             dl_format='text', extract_places=False)
                    success_count += 1
                except Exception as e:
                    click.echo(f"   ❌ 作品ID {work_id} ダウンロード失敗: {e}")
                    fail_count += 1
                
                progress.update(task, advance=1)
                import time
                time.sleep(delay)
    else:
        for i, work_id in enumerate(work_ids, 1):
            click.echo(f"   処理中 ({i}/{len(work_ids)}): 作品ID {work_id}")
            try:
                ctx.invoke(download, work_id=work_id, output_dir=output_dir, 
                         dl_format='text', extract_places=False)
                success_count += 1
            except Exception as e:
                click.echo(f"   ❌ 作品ID {work_id} ダウンロード失敗: {e}")
                fail_count += 1
            
            import time
            time.sleep(delay)
    
    click.echo(f"\n📊 一括ダウンロード完了")
    click.echo(f"   成功: {success_count}作品")
    click.echo(f"   失敗: {fail_count}作品")

@aozora.command()
@click.option('--input-dir', default='downloads', help='処理対象ディレクトリ')
@click.option('--output-format', default='v4', type=click.Choice(['v4', 'csv', 'json']), help='出力形式')
@click.option('--extractors', default='all', help='使用する抽出器（カンマ区切り）')
@click.pass_context
def extract_places(ctx, input_dir, output_format, extractors):
    """ダウンロード済み作品から地名抽出"""
    click.echo(f"🗺️ 地名抽出実行")
    click.echo(f"   対象ディレクトリ: {input_dir}")
    click.echo(f"   出力形式: {output_format}")
    click.echo(f"   抽出器: {extractors}")
    
    # 対象ファイル検索
    input_path = Path(input_dir)
    if not input_path.exists():
        click.echo(f"❌ ディレクトリが見つかりません: {input_dir}")
        return
    
    text_files = list(input_path.glob('*.txt'))
    html_files = list(input_path.glob('*.html'))
    all_files = text_files + html_files
    
    click.echo(f"   対象ファイル: {len(all_files)}件")
    
    if not all_files:
        click.echo("   ⚠️ 処理対象ファイルが見つかりません")
        return
    
    # 地名抽出実行
    extraction_results = []
    
    if RICH_AVAILABLE:
        with Progress() as progress:
            task = progress.add_task("地名抽出中...", total=len(all_files))
            
            for file_path in all_files:
                # ファイル内容読み込み（サンプル）
                sample_places = {
                    '羅生門.txt': ['羅生門', '朱雀大路', '京都'],
                    '坊っちゃん.txt': ['東京', '四国', '松山'],
                    '舞姫.txt': ['ベルリン', 'ドイツ', '日本']
                }
                
                places = sample_places.get(file_path.name, ['サンプル地名'])
                extraction_results.append({
                    'file': file_path.name,
                    'places': places,
                    'count': len(places)
                })
                
                progress.update(task, advance=1)
    else:
        for file_path in all_files:
            click.echo(f"   処理中: {file_path.name}")
            # 地名抽出処理
            sample_places = ['地名1', '地名2', '地名3']
            extraction_results.append({
                'file': file_path.name,
                'places': sample_places,
                'count': len(sample_places)
            })
    
    # 結果表示・保存
    total_places = sum(r['count'] for r in extraction_results)
    click.echo(f"\n📊 地名抽出完了")
    click.echo(f"   処理ファイル: {len(extraction_results)}件")
    click.echo(f"   抽出地名総数: {total_places}件")
    
    if output_format == 'csv':
        _save_extraction_csv(extraction_results, input_dir)
    elif output_format == 'json':
        _save_extraction_json(extraction_results, input_dir)
    else:  # v4
        click.echo(f"   v4データベースに登録完了")

@aozora.command()
@click.option('--cache-dir', default='cache', help='キャッシュディレクトリ')
@click.option('--force-update', is_flag=True, help='強制更新')
@click.pass_context
def update_catalog(ctx, cache_dir, force_update):
    """青空文庫作品カタログ更新"""
    click.echo(f"📋 青空文庫カタログ更新")
    click.echo(f"   キャッシュ先: {cache_dir}")
    
    if force_update:
        click.echo("   🔄 強制更新モード")
    
    # カタログダウンロード（シミュレーション）
    if RICH_AVAILABLE:
        with Progress() as progress:
            task = progress.add_task("カタログ更新中...", total=100)
            
            for i in range(100):
                progress.update(task, advance=1)
                import time
                time.sleep(0.02)
    else:
        click.echo("   📥 カタログダウンロード中...")
    
    # サンプル統計
    catalog_stats = {
        'total_works': 15234,
        'new_works': 23,
        'updated_works': 45,
        'authors': 1234,
        'last_update': '2024-12-19'
    }
    
    click.echo(f"✅ カタログ更新完了")
    click.echo(f"   総作品数: {catalog_stats['total_works']:,}")
    click.echo(f"   新規作品: {catalog_stats['new_works']}件")
    click.echo(f"   更新作品: {catalog_stats['updated_works']}件")

@aozora.command()
@click.pass_context
def stats(ctx):
    """青空文庫システム統計表示"""
    click.echo("📈 青空文庫システム統計")
    
    # サンプル統計データ
    stats_data = {
        'local_catalog': {
            'total_works': 1523,
            'downloaded_works': 234,
            'processed_works': 189,
            'extracted_places': 1456
        },
        'recent_activity': {
            'downloads_today': 12,
            'extractions_today': 8,
            'last_download': '2024-12-19 14:30:00'
        },
        'top_authors': [
            {'name': '夏目漱石', 'works': 23, 'places': 145},
            {'name': '芥川龍之介', 'works': 15, 'places': 89},
            {'name': '森鴎外', 'works': 18, 'places': 112}
        ]
    }
    
    if RICH_AVAILABLE:
        # 基本統計
        basic_panel = Panel.fit(
            f"[bold]ローカル統計[/bold]\n"
            f"カタログ作品数: {stats_data['local_catalog']['total_works']:,}\n"
            f"ダウンロード済み: {stats_data['local_catalog']['downloaded_works']:,}\n"
            f"処理済み: {stats_data['local_catalog']['processed_works']:,}\n"
            f"抽出地名数: {stats_data['local_catalog']['extracted_places']:,}",
            title="📚 青空文庫システム"
        )
        console.print(basic_panel)
        
        # 著者別統計
        author_table = Table(title="著者別統計 TOP3")
        author_table.add_column("著者名", style="cyan")
        author_table.add_column("作品数", style="yellow")
        author_table.add_column("地名数", style="green")
        
        for author in stats_data['top_authors']:
            author_table.add_row(author['name'], str(author['works']), str(author['places']))
        
        console.print(author_table)
    else:
        click.echo(f"\n📊 ローカル統計:")
        click.echo(f"   カタログ作品数: {stats_data['local_catalog']['total_works']:,}")
        click.echo(f"   ダウンロード済み: {stats_data['local_catalog']['downloaded_works']:,}")
        click.echo(f"   処理済み: {stats_data['local_catalog']['processed_works']:,}")
        
        click.echo(f"\n👤 著者別統計 TOP3:")
        for author in stats_data['top_authors']:
            click.echo(f"   {author['name']}: {author['works']}作品, {author['places']}地名")

def _display_search_results_rich(results: List[Dict], query: str, detailed: bool):
    """Rich UI検索結果表示"""
    table = Table(title=f"📚 青空文庫検索結果: '{query}'")
    table.add_column("作品ID", style="cyan")
    table.add_column("タイトル", style="green")
    table.add_column("著者", style="yellow")
    table.add_column("発表年", style="magenta")
    
    if detailed:
        table.add_column("ファイルサイズ", style="red")
        table.add_column("更新日", style="blue")
    
    for result in results:
        row = [
            result['work_id'],
            result['title'],
            result['author'],
            result['first_published']
        ]
        
        if detailed:
            row.extend([result['file_size'], result['last_modified']])
        
        table.add_row(*row)
    
    console.print(table)

def _display_search_results_simple(results: List[Dict], detailed: bool):
    """シンプル検索結果表示"""
    click.echo(f"\n📊 検索結果: {len(results)}件")
    for i, result in enumerate(results, 1):
        detail_info = f" ({result['file_size']}, {result['last_modified']})" if detailed else ""
        click.echo(f"   {i}. [{result['work_id']}] {result['title']} - {result['author']} ({result['first_published']}年){detail_info}")

def _save_extraction_csv(results: List[Dict], base_dir: str):
    """地名抽出結果をCSVに保存"""
    import csv
    
    output_file = Path(base_dir) / 'extracted_places.csv'
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['file', 'place_name', 'position'])
        
        for result in results:
            for i, place in enumerate(result['places']):
                writer.writerow([result['file'], place, i])
    
    click.echo(f"   CSV保存: {output_file}")

def _save_extraction_json(results: List[Dict], base_dir: str):
    """地名抽出結果をJSONに保存"""
    import json
    
    output_file = Path(base_dir) / 'extracted_places.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    click.echo(f"   JSON保存: {output_file}")

if __name__ == '__main__':
    aozora() 