#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検索システム CLI v4
地名・作品・作者の統合検索インターフェース
"""

import click
import logging
from typing import Dict, List, Any, Optional
import sys
import os

logger = logging.getLogger(__name__)

# Rich UIサポート
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='詳細ログ出力')
@click.pass_context
def search(ctx, verbose):
    """🔍 統合検索システム v4 - 地名・作品・作者検索"""
    ctx.ensure_object(dict)
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    if console:
        console.print("[bold green]🔍 統合検索システム v4[/bold green]")

@search.command()
@click.argument('query', required=True)
@click.option('--limit', default=20, help='検索結果数の上限')
@click.option('--confidence', default=0.0, help='信頼度の下限')
@click.option('--category', help='地名カテゴリーでフィルタ')
@click.option('--exact', is_flag=True, help='完全一致検索')
@click.pass_context
def places(ctx, query, limit, confidence, category, exact):
    """地名検索"""
    click.echo(f"🗺️ 地名検索: '{query}'")
    
    # 検索パラメータ表示
    params = []
    if limit != 20:
        params.append(f"上限: {limit}件")
    if confidence > 0:
        params.append(f"信頼度: {confidence}以上")
    if category:
        params.append(f"カテゴリー: {category}")
    if exact:
        params.append("完全一致")
    
    if params:
        click.echo(f"   検索条件: {', '.join(params)}")
    
    # サンプル検索結果
    sample_results = [
        {'place_name': '東京', 'confidence': 0.95, 'category': 'major_city', 'count': 145},
        {'place_name': '東京都', 'confidence': 0.93, 'category': 'prefecture', 'count': 89},
        {'place_name': '東京駅', 'confidence': 0.91, 'category': 'landmark', 'count': 23},
        {'place_name': '東京湾', 'confidence': 0.88, 'category': 'natural', 'count': 12}
    ]
    
    # フィルタリング
    if exact:
        sample_results = [r for r in sample_results if r['place_name'] == query]
    else:
        sample_results = [r for r in sample_results if query in r['place_name']]
    
    if confidence > 0:
        sample_results = [r for r in sample_results if r['confidence'] >= confidence]
    
    if category:
        sample_results = [r for r in sample_results if r['category'] == category]
    
    sample_results = sample_results[:limit]
    
    # 結果表示
    if not sample_results:
        click.echo("   ❌ 該当する地名が見つかりませんでした")
        return
    
    if RICH_AVAILABLE:
        _display_places_rich(sample_results, query)
    else:
        _display_places_simple(sample_results)

@search.command()
@click.argument('query', required=True)
@click.option('--limit', default=20, help='検索結果数の上限')
@click.option('--author', help='特定作者でフィルタ')
@click.option('--year-from', type=int, help='発表年の開始')
@click.option('--year-to', type=int, help='発表年の終了')
@click.pass_context
def works(ctx, query, limit, author, year_from, year_to):
    """作品検索"""
    click.echo(f"📚 作品検索: '{query}'")
    
    # 検索パラメータ表示
    params = []
    if limit != 20:
        params.append(f"上限: {limit}件")
    if author:
        params.append(f"作者: {author}")
    if year_from:
        params.append(f"年度: {year_from}年以降")
    if year_to:
        params.append(f"年度: {year_to}年以前")
    
    if params:
        click.echo(f"   検索条件: {', '.join(params)}")
    
    # サンプル検索結果
    sample_results = [
        {'title': '羅生門', 'author': '芥川龍之介', 'year': 1915, 'places_count': 12},
        {'title': '蜘蛛の糸', 'author': '芥川龍之介', 'year': 1918, 'places_count': 8},
        {'title': '坊っちゃん', 'author': '夏目漱石', 'year': 1906, 'places_count': 45},
        {'title': '吾輩は猫である', 'author': '夏目漱石', 'year': 1905, 'places_count': 23}
    ]
    
    # フィルタリング
    sample_results = [r for r in sample_results if query in r['title']]
    
    if author:
        sample_results = [r for r in sample_results if author in r['author']]
    
    if year_from:
        sample_results = [r for r in sample_results if r['year'] >= year_from]
    
    if year_to:
        sample_results = [r for r in sample_results if r['year'] <= year_to]
    
    sample_results = sample_results[:limit]
    
    # 結果表示
    if not sample_results:
        click.echo("   ❌ 該当する作品が見つかりませんでした")
        return
    
    if RICH_AVAILABLE:
        _display_works_rich(sample_results, query)
    else:
        _display_works_simple(sample_results)

@search.command()
@click.argument('query', required=True)
@click.option('--limit', default=20, help='検索結果数の上限')
@click.option('--birth-year', type=int, help='生年でフィルタ')
@click.option('--death-year', type=int, help='没年でフィルタ')
@click.option('--with-works', is_flag=True, help='代表作品も表示')
@click.pass_context
def authors(ctx, query, limit, birth_year, death_year, with_works):
    """作者検索"""
    click.echo(f"👤 作者検索: '{query}'")
    
    # 検索パラメータ表示
    params = []
    if limit != 20:
        params.append(f"上限: {limit}件")
    if birth_year:
        params.append(f"生年: {birth_year}年")
    if death_year:
        params.append(f"没年: {death_year}年")
    if with_works:
        params.append("代表作品表示")
    
    if params:
        click.echo(f"   検索条件: {', '.join(params)}")
    
    # サンプル検索結果
    sample_results = [
        {
            'name': '夏目漱石', 
            'birth_year': 1867, 
            'death_year': 1916,
            'works_count': 23,
            'places_count': 145,
            'major_works': ['坊っちゃん', 'こころ', '吾輩は猫である']
        },
        {
            'name': '芥川龍之介',
            'birth_year': 1892,
            'death_year': 1927,
            'works_count': 15,
            'places_count': 89,
            'major_works': ['羅生門', '蜘蛛の糸', '地獄変']
        },
        {
            'name': '森鴎外',
            'birth_year': 1862,
            'death_year': 1922,
            'works_count': 18,
            'places_count': 112,
            'major_works': ['舞姫', '高瀬舟', '山椒大夫']
        }
    ]
    
    # フィルタリング
    sample_results = [r for r in sample_results if query in r['name']]
    
    if birth_year:
        sample_results = [r for r in sample_results if r['birth_year'] == birth_year]
    
    if death_year:
        sample_results = [r for r in sample_results if r['death_year'] == death_year]
    
    sample_results = sample_results[:limit]
    
    # 結果表示
    if not sample_results:
        click.echo("   ❌ 該当する作者が見つかりませんでした")
        return
    
    if RICH_AVAILABLE:
        _display_authors_rich(sample_results, query, with_works)
    else:
        _display_authors_simple(sample_results, with_works)

@search.command()
@click.argument('query', required=True)
@click.option('--limit', default=10, help='検索結果数の上限')
@click.option('--context-window', default=50, help='文脈ウィンドウサイズ')
@click.pass_context
def sentences(ctx, query, limit, context_window):
    """センテンス内容検索"""
    click.echo(f"📝 センテンス検索: '{query}'")
    click.echo(f"   文脈ウィンドウ: {context_window}文字")
    
    # サンプル検索結果
    sample_results = [
        {
            'sentence': f"明治の{query}は文明開化の象徴として多くの文学作品に登場した。",
            'work_title': '坊っちゃん',
            'author': '夏目漱石',
            'places': ['東京', '明治'],
            'confidence': 0.92
        },
        {
            'sentence': f"古き良き{query}の街並みを懐かしく思い出していた。",
            'work_title': '羅生門',
            'author': '芥川龍之介',
            'places': ['東京', '江戸'],
            'confidence': 0.88
        }
    ]
    
    sample_results = sample_results[:limit]
    
    # 結果表示
    if RICH_AVAILABLE:
        _display_sentences_rich(sample_results, query)
    else:
        _display_sentences_simple(sample_results)

@search.command()
@click.argument('query', required=True)
@click.option('--search-type', default='all', type=click.Choice(['all', 'places', 'works', 'authors', 'sentences']), help='検索対象')
@click.option('--limit', default=5, help='各カテゴリーの検索結果数')
@click.pass_context
def all(ctx, query, search_type, limit):
    """統合検索（全カテゴリー）"""
    click.echo(f"🌟 統合検索: '{query}'")
    click.echo(f"   検索対象: {search_type}")
    
    if search_type in ['all', 'places']:
        click.echo("\n🗺️ 地名検索結果:")
        ctx.invoke(places, query=query, limit=limit)
    
    if search_type in ['all', 'works']:
        click.echo("\n📚 作品検索結果:")
        ctx.invoke(works, query=query, limit=limit)
    
    if search_type in ['all', 'authors']:
        click.echo("\n👤 作者検索結果:")
        ctx.invoke(authors, query=query, limit=limit)
    
    if search_type in ['all', 'sentences']:
        click.echo("\n📝 センテンス検索結果:")
        ctx.invoke(sentences, query=query, limit=limit)

def _display_places_rich(results: List[Dict], query: str):
    """Rich UI地名検索結果表示"""
    table = Table(title=f"🗺️ 地名検索結果: '{query}'")
    table.add_column("地名", style="cyan")
    table.add_column("カテゴリー", style="green")
    table.add_column("信頼度", style="yellow")
    table.add_column("出現数", style="red")
    
    for result in results:
        table.add_row(
            result['place_name'],
            result['category'],
            f"{result['confidence']:.2%}",
            str(result['count'])
        )
    
    console.print(table)

def _display_places_simple(results: List[Dict]):
    """シンプル地名検索結果表示"""
    click.echo(f"\n   📊 検索結果: {len(results)}件")
    for i, result in enumerate(results, 1):
        click.echo(f"   {i}. {result['place_name']} ({result['category']}) - 信頼度: {result['confidence']:.2%}, 出現: {result['count']}回")

def _display_works_rich(results: List[Dict], query: str):
    """Rich UI作品検索結果表示"""
    table = Table(title=f"📚 作品検索結果: '{query}'")
    table.add_column("作品名", style="cyan")
    table.add_column("作者", style="green")
    table.add_column("発表年", style="yellow")
    table.add_column("地名数", style="red")
    
    for result in results:
        table.add_row(
            result['title'],
            result['author'],
            str(result['year']),
            str(result['places_count'])
        )
    
    console.print(table)

def _display_works_simple(results: List[Dict]):
    """シンプル作品検索結果表示"""
    click.echo(f"\n   📊 検索結果: {len(results)}件")
    for i, result in enumerate(results, 1):
        click.echo(f"   {i}. {result['title']} - {result['author']} ({result['year']}年) - 地名: {result['places_count']}件")

def _display_authors_rich(results: List[Dict], query: str, with_works: bool):
    """Rich UI作者検索結果表示"""
    table = Table(title=f"👤 作者検索結果: '{query}'")
    table.add_column("作者名", style="cyan")
    table.add_column("生没年", style="green")
    table.add_column("作品数", style="yellow")
    table.add_column("地名数", style="red")
    
    if with_works:
        table.add_column("代表作品", style="magenta")
    
    for result in results:
        row = [
            result['name'],
            f"{result['birth_year']}-{result['death_year']}",
            str(result['works_count']),
            str(result['places_count'])
        ]
        
        if with_works:
            row.append(", ".join(result['major_works'][:3]))
        
        table.add_row(*row)
    
    console.print(table)

def _display_authors_simple(results: List[Dict], with_works: bool):
    """シンプル作者検索結果表示"""
    click.echo(f"\n   📊 検索結果: {len(results)}件")
    for i, result in enumerate(results, 1):
        works_info = f" - 代表作: {', '.join(result['major_works'][:3])}" if with_works else ""
        click.echo(f"   {i}. {result['name']} ({result['birth_year']}-{result['death_year']}) - 作品: {result['works_count']}件, 地名: {result['places_count']}件{works_info}")

def _display_sentences_rich(results: List[Dict], query: str):
    """Rich UIセンテンス検索結果表示"""
    console.print(Panel.fit(f"📝 センテンス検索結果: '{query}'", style="bold blue"))
    
    for i, result in enumerate(results, 1):
        panel_content = f"[bold]{result['work_title']}[/bold] - {result['author']}\n\n"
        panel_content += f"[italic]{result['sentence']}[/italic]\n\n"
        panel_content += f"関連地名: {', '.join(result['places'])} (信頼度: {result['confidence']:.1%})"
        
        console.print(Panel(panel_content, title=f"結果 {i}"))

def _display_sentences_simple(results: List[Dict]):
    """シンプルセンテンス検索結果表示"""
    click.echo(f"\n   📊 検索結果: {len(results)}件")
    for i, result in enumerate(results, 1):
        click.echo(f"\n   {i}. 【{result['work_title']}】{result['author']}")
        click.echo(f"      {result['sentence']}")
        click.echo(f"      関連地名: {', '.join(result['places'])} (信頼度: {result['confidence']:.1%})")

if __name__ == '__main__':
    search() 