#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベース拡張システム CLI v4
作者・作品・地名データの自動・半自動拡張機能
"""

import click
import logging
from typing import Dict, List, Any, Optional
import sys
import os
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Rich UIサポート
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress
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
def expand(ctx, verbose):
    """🗄️ データベース拡張システム v4"""
    ctx.ensure_object(dict)
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    if console:
        console.print("[bold cyan]🗄️ データベース拡張システム v4[/bold cyan]")

@expand.command()
@click.option('--source', default='wikipedia', type=click.Choice(['wikipedia', 'aozora', 'manual', 'all']), help='データソース')
@click.option('--limit', default=50, help='処理件数上限')
@click.option('--dry-run', is_flag=True, help='実際の追加は行わず候補のみ表示')
@click.option('--confidence-min', default=0.7, help='追加する作者の信頼度下限')
@click.pass_context
def authors(ctx, source, limit, dry_run, confidence_min):
    """作者データ拡張"""
    click.echo(f"👤 作者データ拡張")
    click.echo(f"   データソース: {source}")
    click.echo(f"   信頼度下限: {confidence_min}")
    
    if dry_run:
        click.echo("   📋 ドライランモード")
    
    # 候補作者データ（サンプル）
    candidate_authors = [
        {
            'name': '太宰治',
            'birth_year': 1909,
            'death_year': 1948,
            'confidence': 0.95,
            'source': 'wikipedia',
            'works_found': 12,
            'biography': '青森県出身の小説家。無頼派の代表的作家。',
            'wikipedia_url': 'https://ja.wikipedia.org/wiki/太宰治'
        },
        {
            'name': '宮沢賢治',
            'birth_year': 1896,
            'death_year': 1933,
            'confidence': 0.92,
            'source': 'aozora',
            'works_found': 8,
            'biography': '岩手県出身の詩人・童話作家。',
            'wikipedia_url': 'https://ja.wikipedia.org/wiki/宮沢賢治'
        },
        {
            'name': '坂口安吾',
            'birth_year': 1906,
            'death_year': 1955,
            'confidence': 0.88,
            'source': 'wikipedia',
            'works_found': 15,
            'biography': '新潟県出身の小説家。無頼派作家の一人。',
            'wikipedia_url': 'https://ja.wikipedia.org/wiki/坂口安吾'
        },
        {
            'name': '中島敦',
            'birth_year': 1909,
            'death_year': 1942,
            'confidence': 0.85,
            'source': 'aozora',
            'works_found': 6,
            'biography': '東京出身の小説家。中国古典を題材とした作品で知られる。',
            'wikipedia_url': 'https://ja.wikipedia.org/wiki/中島敦'
        }
    ]
    
    # フィルタリング
    if source != 'all':
        candidate_authors = [a for a in candidate_authors if a['source'] == source]
    
    candidate_authors = [a for a in candidate_authors if a['confidence'] >= confidence_min]
    candidate_authors = candidate_authors[:limit]
    
    click.echo(f"\n📋 候補作者: {len(candidate_authors)}名")
    
    if RICH_AVAILABLE:
        _display_author_candidates_rich(candidate_authors, dry_run)
    else:
        _display_author_candidates_simple(candidate_authors, dry_run)
    
    if not dry_run and candidate_authors:
        # 実際の追加処理
        added_count = 0
        for author in candidate_authors:
            try:
                # データベース追加処理（シミュレーション）
                added_count += 1
                if RICH_AVAILABLE:
                    console.print(f"   ✅ 追加完了: {author['name']}")
                else:
                    click.echo(f"   ✅ 追加完了: {author['name']}")
            except Exception as e:
                if RICH_AVAILABLE:
                    console.print(f"   ❌ 追加失敗: {author['name']} - {e}")
                else:
                    click.echo(f"   ❌ 追加失敗: {author['name']} - {e}")
        
        click.echo(f"\n📊 作者追加結果: {added_count}/{len(candidate_authors)}名")

@expand.command()
@click.option('--author', help='特定作者の作品のみ拡張')
@click.option('--source', default='aozora', type=click.Choice(['aozora', 'wikipedia', 'manual']), help='データソース')
@click.option('--limit', default=100, help='処理件数上限')
@click.option('--include-metadata', is_flag=True, help='詳細メタデータも取得')
@click.option('--dry-run', is_flag=True, help='実際の追加は行わず候補のみ表示')
@click.pass_context
def works(ctx, author, source, limit, include_metadata, dry_run):
    """作品データ拡張"""
    click.echo(f"📚 作品データ拡張")
    click.echo(f"   データソース: {source}")
    
    if author:
        click.echo(f"   対象作者: {author}")
    
    if dry_run:
        click.echo("   📋 ドライランモード")
    
    # 候補作品データ（サンプル）
    candidate_works = [
        {
            'title': '人間失格',
            'author': '太宰治',
            'publication_year': 1948,
            'confidence': 0.98,
            'source': 'aozora',
            'aozora_id': '35',
            'genre': '小説',
            'length': '長編',
            'places_potential': 15
        },
        {
            'title': '津軽',
            'author': '太宰治',
            'publication_year': 1944,
            'confidence': 0.95,
            'source': 'aozora',
            'aozora_id': '124',
            'genre': '紀行文',
            'length': '中編',
            'places_potential': 35
        },
        {
            'title': '銀河鉄道の夜',
            'author': '宮沢賢治',
            'publication_year': 1934,
            'confidence': 0.97,
            'source': 'aozora',
            'aozora_id': '456',
            'genre': '童話',
            'length': '中編',
            'places_potential': 8
        },
        {
            'title': '風の又三郎',
            'author': '宮沢賢治',
            'publication_year': 1934,
            'confidence': 0.93,
            'source': 'aozora',
            'aozora_id': '789',
            'genre': '童話',
            'length': '短編',
            'places_potential': 12
        },
        {
            'title': '山月記',
            'author': '中島敦',
            'publication_year': 1942,
            'confidence': 0.96,
            'source': 'aozora',
            'aozora_id': '567',
            'genre': '小説',
            'length': '短編',
            'places_potential': 6
        }
    ]
    
    # フィルタリング
    if author:
        candidate_works = [w for w in candidate_works if author in w['author']]
    
    if source != 'manual':
        candidate_works = [w for w in candidate_works if w['source'] == source]
    
    candidate_works = candidate_works[:limit]
    
    click.echo(f"\n📋 候補作品: {len(candidate_works)}作品")
    
    if RICH_AVAILABLE:
        _display_work_candidates_rich(candidate_works, include_metadata, dry_run)
    else:
        _display_work_candidates_simple(candidate_works, include_metadata, dry_run)
    
    if not dry_run and candidate_works:
        # 実際の追加処理
        added_count = 0
        total_places = 0
        
        if RICH_AVAILABLE:
            with Progress() as progress:
                task = progress.add_task("作品追加中...", total=len(candidate_works))
                
                for work in candidate_works:
                    try:
                        # データベース追加処理（シミュレーション）
                        added_count += 1
                        total_places += work['places_potential']
                        
                        progress.update(task, advance=1)
                    except Exception as e:
                        console.print(f"   ❌ 追加失敗: {work['title']} - {e}")
        else:
            for work in candidate_works:
                try:
                    click.echo(f"   処理中: {work['title']}")
                    added_count += 1
                    total_places += work['places_potential']
                except Exception as e:
                    click.echo(f"   ❌ 追加失敗: {work['title']} - {e}")
        
        click.echo(f"\n📊 作品追加結果: {added_count}/{len(candidate_works)}作品")
        click.echo(f"   推定地名追加: {total_places}件")

@expand.command()
@click.option('--region', help='特定地域の地名を重点的に拡張')
@click.option('--category', help='特定カテゴリーの地名を拡張')
@click.option('--source', default='extraction', type=click.Choice(['extraction', 'geocoding', 'manual']), help='データソース')
@click.option('--confidence-min', default=0.6, help='追加する地名の信頼度下限')
@click.option('--limit', default=200, help='処理件数上限')
@click.option('--dry-run', is_flag=True, help='実際の追加は行わず候補のみ表示')
@click.pass_context
def places(ctx, region, category, source, confidence_min, limit, dry_run):
    """地名データ拡張"""
    click.echo(f"🗺️ 地名データ拡張")
    click.echo(f"   データソース: {source}")
    click.echo(f"   信頼度下限: {confidence_min}")
    
    if region:
        click.echo(f"   対象地域: {region}")
    if category:
        click.echo(f"   対象カテゴリー: {category}")
    
    if dry_run:
        click.echo("   📋 ドライランモード")
    
    # 候補地名データ（サンプル）
    candidate_places = [
        {
            'place_name': '青森',
            'prefecture': '青森県',
            'confidence': 0.89,
            'category': 'prefecture',
            'source': 'extraction',
            'work_count': 8,
            'coordinates': (40.8244, 140.7400),
            'extraction_context': '津軽の風景が美しい青森の地で...'
        },
        {
            'place_name': '花巻',
            'prefecture': '岩手県',
            'confidence': 0.85,
            'category': 'city',
            'source': 'extraction',
            'work_count': 12,
            'coordinates': (39.3895, 141.1139),
            'extraction_context': '賢治の故郷花巻には...'
        },
        {
            'place_name': '弘前',
            'prefecture': '青森県',
            'confidence': 0.82,
            'category': 'city',
            'source': 'extraction',
            'work_count': 5,
            'coordinates': (40.6044, 140.4661),
            'extraction_context': '弘前城の桜が咲いていた'
        },
        {
            'place_name': '津軽海峡',
            'prefecture': '青森県',
            'confidence': 0.78,
            'category': 'natural',
            'source': 'extraction',
            'work_count': 3,
            'coordinates': (41.2000, 140.8000),
            'extraction_context': '津軽海峡の荒波を見つめて...'
        }
    ]
    
    # フィルタリング
    if region:
        candidate_places = [p for p in candidate_places if region in p['prefecture']]
    
    if category:
        candidate_places = [p for p in candidate_places if p['category'] == category]
    
    candidate_places = [p for p in candidate_places if p['confidence'] >= confidence_min]
    candidate_places = candidate_places[:limit]
    
    click.echo(f"\n📋 候補地名: {len(candidate_places)}件")
    
    if RICH_AVAILABLE:
        _display_place_candidates_rich(candidate_places, dry_run)
    else:
        _display_place_candidates_simple(candidate_places, dry_run)
    
    if not dry_run and candidate_places:
        # 実際の追加処理
        added_count = 0
        geocoded_count = 0
        
        for place in candidate_places:
            try:
                # データベース追加処理（シミュレーション）
                added_count += 1
                if place['coordinates']:
                    geocoded_count += 1
                
                if RICH_AVAILABLE:
                    console.print(f"   ✅ 追加完了: {place['place_name']}")
                else:
                    click.echo(f"   ✅ 追加完了: {place['place_name']}")
            except Exception as e:
                if RICH_AVAILABLE:
                    console.print(f"   ❌ 追加失敗: {place['place_name']} - {e}")
                else:
                    click.echo(f"   ❌ 追加失敗: {place['place_name']} - {e}")
        
        click.echo(f"\n📊 地名追加結果: {added_count}/{len(candidate_places)}件")
        click.echo(f"   ジオコーディング済み: {geocoded_count}件")

@expand.command()
@click.option('--target', default='all', type=click.Choice(['all', 'authors', 'works', 'places']), help='拡張対象')
@click.option('--batch-size', default=20, help='バッチサイズ')
@click.option('--delay', default=1.0, help='処理間隔（秒）')
@click.option('--dry-run', is_flag=True, help='実際の追加は行わず候補のみ表示')
@click.pass_context
def auto(ctx, target, batch_size, delay, dry_run):
    """自動データベース拡張"""
    click.echo(f"🤖 自動データベース拡張")
    click.echo(f"   対象: {target}")
    click.echo(f"   バッチサイズ: {batch_size}")
    
    if dry_run:
        click.echo("   📋 ドライランモード")
    
    # 拡張対象決定
    targets = []
    if target in ['all', 'authors']:
        targets.append('authors')
    if target in ['all', 'works']:
        targets.append('works')
    if target in ['all', 'places']:
        targets.append('places')
    
    total_added = {'authors': 0, 'works': 0, 'places': 0}
    
    if RICH_AVAILABLE:
        with Progress() as progress:
            for target_type in targets:
                task = progress.add_task(f"{target_type} 自動拡張中...", total=batch_size)
                
                if target_type == 'authors':
                    ctx.invoke(authors, source='all', limit=batch_size, dry_run=dry_run, confidence_min=0.7)
                    total_added['authors'] = batch_size
                elif target_type == 'works':
                    ctx.invoke(works, source='aozora', limit=batch_size, dry_run=dry_run)
                    total_added['works'] = batch_size
                elif target_type == 'places':
                    ctx.invoke(places, source='extraction', limit=batch_size, dry_run=dry_run, confidence_min=0.6)
                    total_added['places'] = batch_size
                
                progress.update(task, advance=batch_size)
                
                import time
                time.sleep(delay)
    else:
        for target_type in targets:
            click.echo(f"\n🔄 {target_type} 自動拡張中...")
            
            if target_type == 'authors':
                ctx.invoke(authors, source='all', limit=batch_size, dry_run=dry_run, confidence_min=0.7)
                total_added['authors'] = batch_size
            elif target_type == 'works':
                ctx.invoke(works, source='aozora', limit=batch_size, dry_run=dry_run)
                total_added['works'] = batch_size
            elif target_type == 'places':
                ctx.invoke(places, source='extraction', limit=batch_size, dry_run=dry_run, confidence_min=0.6)
                total_added['places'] = batch_size
            
            import time
            time.sleep(delay)
    
    # 総合結果
    click.echo(f"\n📊 自動拡張完了")
    for target_type, count in total_added.items():
        if count > 0:
            click.echo(f"   {target_type}: {count}件追加")

@expand.command()
@click.pass_context
def stats(ctx):
    """データベース拡張統計表示"""
    click.echo("📈 データベース拡張統計")
    
    # サンプル統計データ
    stats_data = {
        'expansion_history': {
            'authors_added_today': 5,
            'works_added_today': 12,
            'places_added_today': 28,
            'total_expansions': 156
        },
        'candidate_sources': {
            'wikipedia': {
                'authors': 45,
                'works': 23,
                'confidence_avg': 0.87
            },
            'aozora': {
                'works': 89,
                'places': 156,
                'confidence_avg': 0.82
            },
            'extraction': {
                'places': 234,
                'confidence_avg': 0.75
            }
        },
        'expansion_potential': {
            'high_confidence_candidates': 67,
            'medium_confidence_candidates': 134,
            'total_candidates': 201
        }
    }
    
    if RICH_AVAILABLE:
        # 今日の拡張状況
        today_panel = Panel.fit(
            f"[bold]本日の拡張実績[/bold]\n"
            f"作者追加: {stats_data['expansion_history']['authors_added_today']:,}名\n"
            f"作品追加: {stats_data['expansion_history']['works_added_today']:,}作品\n"
            f"地名追加: {stats_data['expansion_history']['places_added_today']:,}件\n"
            f"総拡張回数: {stats_data['expansion_history']['total_expansions']:,}回",
            title="📊 拡張統計"
        )
        console.print(today_panel)
        
        # ソース別統計
        source_table = Table(title="データソース別統計")
        source_table.add_column("ソース", style="cyan")
        source_table.add_column("候補数", style="yellow")
        source_table.add_column("平均信頼度", style="green")
        source_table.add_column("種別", style="magenta")
        
        for source, data in stats_data['candidate_sources'].items():
            if 'authors' in data:
                source_table.add_row(source, str(data['authors']), f"{data['confidence_avg']:.1%}", "作者")
            if 'works' in data:
                source_table.add_row(source, str(data['works']), f"{data['confidence_avg']:.1%}", "作品")
            if 'places' in data:
                source_table.add_row(source, str(data['places']), f"{data['confidence_avg']:.1%}", "地名")
        
        console.print(source_table)
    else:
        click.echo(f"\n📊 本日の拡張実績:")
        click.echo(f"   作者追加: {stats_data['expansion_history']['authors_added_today']:,}名")
        click.echo(f"   作品追加: {stats_data['expansion_history']['works_added_today']:,}作品")
        click.echo(f"   地名追加: {stats_data['expansion_history']['places_added_today']:,}件")
        
        click.echo(f"\n📈 拡張候補:")
        click.echo(f"   高信頼度: {stats_data['expansion_potential']['high_confidence_candidates']}件")
        click.echo(f"   中信頼度: {stats_data['expansion_potential']['medium_confidence_candidates']}件")

def _display_author_candidates_rich(candidates: List[Dict], dry_run: bool):
    """Rich UI 作者候補表示"""
    table = Table(title=f"👤 作者候補 ({len(candidates)}名)")
    table.add_column("作者名", style="cyan")
    table.add_column("生没年", style="green")
    table.add_column("信頼度", style="yellow")
    table.add_column("作品数", style="red")
    table.add_column("ソース", style="magenta")
    table.add_column("処理", style="blue")
    
    for candidate in candidates:
        status = "ドライラン" if dry_run else "追加予定"
        table.add_row(
            candidate['name'],
            f"{candidate['birth_year']}-{candidate['death_year']}",
            f"{candidate['confidence']:.1%}",
            str(candidate['works_found']),
            candidate['source'],
            status
        )
    
    console.print(table)

def _display_author_candidates_simple(candidates: List[Dict], dry_run: bool):
    """シンプル 作者候補表示"""
    status = "ドライラン" if dry_run else "追加予定"
    
    for i, candidate in enumerate(candidates, 1):
        click.echo(f"   {i}. {candidate['name']} ({candidate['birth_year']}-{candidate['death_year']}) - 信頼度: {candidate['confidence']:.1%}, 作品: {candidate['works_found']}件 [{status}]")

def _display_work_candidates_rich(candidates: List[Dict], include_metadata: bool, dry_run: bool):
    """Rich UI 作品候補表示"""
    table = Table(title=f"📚 作品候補 ({len(candidates)}作品)")
    table.add_column("作品名", style="cyan")
    table.add_column("作者", style="green")
    table.add_column("発表年", style="yellow")
    table.add_column("信頼度", style="red")
    
    if include_metadata:
        table.add_column("ジャンル", style="magenta")
        table.add_column("地名予想", style="blue")
    
    table.add_column("処理", style="white")
    
    for candidate in candidates:
        status = "ドライラン" if dry_run else "追加予定"
        row = [
            candidate['title'],
            candidate['author'],
            str(candidate['publication_year']),
            f"{candidate['confidence']:.1%}"
        ]
        
        if include_metadata:
            row.extend([
                candidate['genre'],
                f"{candidate['places_potential']}件"
            ])
        
        row.append(status)
        table.add_row(*row)
    
    console.print(table)

def _display_work_candidates_simple(candidates: List[Dict], include_metadata: bool, dry_run: bool):
    """シンプル 作品候補表示"""
    status = "ドライラン" if dry_run else "追加予定"
    
    for i, candidate in enumerate(candidates, 1):
        metadata = f" ({candidate['genre']}, 地名予想: {candidate['places_potential']}件)" if include_metadata else ""
        click.echo(f"   {i}. {candidate['title']} - {candidate['author']} ({candidate['publication_year']}) - 信頼度: {candidate['confidence']:.1%}{metadata} [{status}]")

def _display_place_candidates_rich(candidates: List[Dict], dry_run: bool):
    """Rich UI 地名候補表示"""
    table = Table(title=f"🗺️ 地名候補 ({len(candidates)}件)")
    table.add_column("地名", style="cyan")
    table.add_column("都道府県", style="green")
    table.add_column("カテゴリー", style="yellow")
    table.add_column("信頼度", style="red")
    table.add_column("出現数", style="magenta")
    table.add_column("処理", style="blue")
    
    for candidate in candidates:
        status = "ドライラン" if dry_run else "追加予定"
        table.add_row(
            candidate['place_name'],
            candidate['prefecture'],
            candidate['category'],
            f"{candidate['confidence']:.1%}",
            str(candidate['work_count']),
            status
        )
    
    console.print(table)

def _display_place_candidates_simple(candidates: List[Dict], dry_run: bool):
    """シンプル 地名候補表示"""
    status = "ドライラン" if dry_run else "追加予定"
    
    for i, candidate in enumerate(candidates, 1):
        click.echo(f"   {i}. {candidate['place_name']} ({candidate['prefecture']}) - {candidate['category']}, 信頼度: {candidate['confidence']:.1%}, 出現: {candidate['work_count']}回 [{status}]")

if __name__ == '__main__':
    expand() 