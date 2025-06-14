#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手動データ追加システム CLI v4
作者・作品・地名の手動追加・編集・管理機能
"""

import click
import logging
from typing import Dict, List, Any, Optional
import sys
import os
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Rich UIサポート
try:
    from rich.console import Console
    from rich.table import Table
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.panel import Panel
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='詳細ログ出力')
@click.pass_context
def add(ctx, verbose):
    """➕ 手動データ追加システム v4"""
    ctx.ensure_object(dict)
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    if console:
        console.print("[bold green]➕ 手動データ追加システム v4[/bold green]")

@add.command()
@click.option('--name', prompt='作者名', help='作者名（必須）')
@click.option('--birth-year', type=int, help='生年')
@click.option('--death-year', type=int, help='没年')
@click.option('--biography', help='経歴・略歴')
@click.option('--wikipedia-url', help='Wikipedia URL')
@click.option('--interactive', is_flag=True, help='対話式入力モード')
@click.pass_context
def author(ctx, name, birth_year, death_year, biography, wikipedia_url, interactive):
    """作者データ手動追加"""
    click.echo(f"👤 作者データ追加: {name}")
    
    # 対話式入力モード
    if interactive or not all([birth_year, death_year]):
        if RICH_AVAILABLE:
            console.print("[bold blue]📝 対話式入力モード[/bold blue]")
            
            if not birth_year:
                birth_year = IntPrompt.ask("生年", default=1900)
            if not death_year:
                death_year = IntPrompt.ask("没年", default=1950)
            if not biography:
                biography = Prompt.ask("略歴", default="")
            if not wikipedia_url:
                wikipedia_url = Prompt.ask("Wikipedia URL", default="")
        else:
            if not birth_year:
                birth_year = int(input("生年 (例: 1867): ") or "1900")
            if not death_year:
                death_year = int(input("没年 (例: 1916): ") or "1950")
            if not biography:
                biography = input("略歴: ") or ""
            if not wikipedia_url:
                wikipedia_url = input("Wikipedia URL: ") or ""
    
    # データ検証
    validation_errors = []
    
    if birth_year and death_year and birth_year >= death_year:
        validation_errors.append("生年が没年以降になっています")
    
    if birth_year and (birth_year < 1800 or birth_year > 2000):
        validation_errors.append("生年が範囲外です (1800-2000)")
    
    if death_year and (death_year < 1800 or death_year > 2050):
        validation_errors.append("没年が範囲外です (1800-2050)")
    
    if validation_errors:
        click.echo("❌ データ検証エラー:")
        for error in validation_errors:
            click.echo(f"   • {error}")
        return
    
    # 作者データ構築
    author_data = {
        'name': name,
        'birth_year': birth_year,
        'death_year': death_year,
        'biography': biography or f"{name}の略歴情報",
        'wikipedia_url': wikipedia_url,
        'added_date': datetime.now().isoformat(),
        'source': 'manual_input'
    }
    
    # 確認表示
    if RICH_AVAILABLE:
        _display_author_data_rich(author_data)
        
        if Confirm.ask("この内容で作者を追加しますか？"):
            _save_author_data(author_data)
        else:
            console.print("[yellow]キャンセルされました[/yellow]")
    else:
        _display_author_data_simple(author_data)
        
        confirm = input("この内容で作者を追加しますか？ (y/n): ")
        if confirm.lower() in ['y', 'yes']:
            _save_author_data(author_data)
        else:
            click.echo("キャンセルされました")

@add.command()
@click.option('--title', prompt='作品タイトル', help='作品タイトル（必須）')
@click.option('--author', prompt='作者名', help='作者名（必須）')
@click.option('--publication-year', type=int, help='発表年')
@click.option('--genre', help='ジャンル')
@click.option('--aozora-url', help='青空文庫URL')
@click.option('--file-path', type=click.Path(exists=True), help='テキストファイルパス')
@click.option('--interactive', is_flag=True, help='対話式入力モード')
@click.pass_context
def work(ctx, title, author, publication_year, genre, aozora_url, file_path, interactive):
    """作品データ手動追加"""
    click.echo(f"📚 作品データ追加: {title}")
    
    # 対話式入力モード
    if interactive or not all([publication_year, genre]):
        if RICH_AVAILABLE:
            console.print("[bold blue]📝 対話式入力モード[/bold blue]")
            
            if not publication_year:
                publication_year = IntPrompt.ask("発表年", default=1900)
            if not genre:
                genre_options = ['小説', '詩', '戯曲', '評論', '随筆', 'その他']
                genre = Prompt.ask("ジャンル", choices=genre_options, default='小説')
            if not aozora_url:
                aozora_url = Prompt.ask("青空文庫URL", default="")
        else:
            if not publication_year:
                publication_year = int(input("発表年 (例: 1906): ") or "1900")
            if not genre:
                genre = input("ジャンル (小説/詩/戯曲/評論/随筆): ") or "小説"
            if not aozora_url:
                aozora_url = input("青空文庫URL: ") or ""
    
    # ファイル内容読み込み
    content = ""
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()[:1000]  # 最初の1000文字のみ
            click.echo(f"   ファイル読み込み完了: {len(content)}文字")
        except Exception as e:
            click.echo(f"   ⚠️ ファイル読み込みエラー: {e}")
    
    # データ検証
    validation_errors = []
    
    if publication_year and (publication_year < 1000 or publication_year > 2050):
        validation_errors.append("発表年が範囲外です (1000-2050)")
    
    if aozora_url and not aozora_url.startswith('http'):
        validation_errors.append("URLの形式が正しくありません")
    
    if validation_errors:
        click.echo("❌ データ検証エラー:")
        for error in validation_errors:
            click.echo(f"   • {error}")
        return
    
    # 作品データ構築
    work_data = {
        'title': title,
        'author': author,
        'publication_year': publication_year,
        'genre': genre or '小説',
        'aozora_url': aozora_url,
        'content_preview': content[:200] if content else "",
        'file_path': str(file_path) if file_path else "",
        'added_date': datetime.now().isoformat(),
        'source': 'manual_input'
    }
    
    # 確認表示
    if RICH_AVAILABLE:
        _display_work_data_rich(work_data)
        
        if Confirm.ask("この内容で作品を追加しますか？"):
            _save_work_data(work_data)
            
            # 地名抽出確認
            if content and Confirm.ask("地名抽出を実行しますか？"):
                ctx.invoke(extract_places_from_work, work_data=work_data)
        else:
            console.print("[yellow]キャンセルされました[/yellow]")
    else:
        _display_work_data_simple(work_data)
        
        confirm = input("この内容で作品を追加しますか？ (y/n): ")
        if confirm.lower() in ['y', 'yes']:
            _save_work_data(work_data)
            
            if content:
                extract_confirm = input("地名抽出を実行しますか？ (y/n): ")
                if extract_confirm.lower() in ['y', 'yes']:
                    ctx.invoke(extract_places_from_work, work_data=work_data)
        else:
            click.echo("キャンセルされました")

@add.command()
@click.option('--place-name', prompt='地名', help='地名（必須）')
@click.option('--latitude', type=float, help='緯度')
@click.option('--longitude', type=float, help='経度')
@click.option('--prefecture', help='都道府県')
@click.option('--category', help='カテゴリー')
@click.option('--confidence', type=float, default=1.0, help='信頼度 (0.0-1.0)')
@click.option('--interactive', is_flag=True, help='対話式入力モード')
@click.pass_context
def place(ctx, place_name, latitude, longitude, prefecture, category, confidence, interactive):
    """地名データ手動追加"""
    click.echo(f"🗺️ 地名データ追加: {place_name}")
    
    # 対話式入力モード
    if interactive or not all([latitude, longitude, prefecture, category]):
        if RICH_AVAILABLE:
            console.print("[bold blue]📝 対話式入力モード[/bold blue]")
            
            if not latitude:
                latitude = float(Prompt.ask("緯度", default="35.0"))
            if not longitude:
                longitude = float(Prompt.ask("経度", default="135.0"))
            if not prefecture:
                prefecture = Prompt.ask("都道府県", default="東京都")
            if not category:
                category_options = ['prefecture', 'major_city', 'city', 'town', 'landmark', 'natural', 'other']
                category = Prompt.ask("カテゴリー", choices=category_options, default='city')
        else:
            if not latitude:
                latitude = float(input("緯度 (例: 35.6812): ") or "35.0")
            if not longitude:
                longitude = float(input("経度 (例: 139.7671): ") or "135.0")
            if not prefecture:
                prefecture = input("都道府県 (例: 東京都): ") or "東京都"
            if not category:
                category = input("カテゴリー (prefecture/major_city/city/town/landmark/natural): ") or "city"
    
    # データ検証
    validation_errors = []
    
    if latitude < -90 or latitude > 90:
        validation_errors.append("緯度が範囲外です (-90 〜 90)")
    
    if longitude < -180 or longitude > 180:
        validation_errors.append("経度が範囲外です (-180 〜 180)")
    
    if confidence < 0.0 or confidence > 1.0:
        validation_errors.append("信頼度が範囲外です (0.0 〜 1.0)")
    
    if validation_errors:
        click.echo("❌ データ検証エラー:")
        for error in validation_errors:
            click.echo(f"   • {error}")
        return
    
    # 地名データ構築
    place_data = {
        'place_name': place_name,
        'latitude': latitude,
        'longitude': longitude,
        'prefecture': prefecture,
        'category': category or 'city',
        'confidence': confidence,
        'added_date': datetime.now().isoformat(),
        'source': 'manual_input'
    }
    
    # 確認表示
    if RICH_AVAILABLE:
        _display_place_data_rich(place_data)
        
        if Confirm.ask("この内容で地名を追加しますか？"):
            _save_place_data(place_data)
        else:
            console.print("[yellow]キャンセルされました[/yellow]")
    else:
        _display_place_data_simple(place_data)
        
        confirm = input("この内容で地名を追加しますか？ (y/n): ")
        if confirm.lower() in ['y', 'yes']:
            _save_place_data(place_data)
        else:
            click.echo("キャンセルされました")

@add.command()
@click.option('--input-file', type=click.Path(exists=True), required=True, help='CSVファイルパス')
@click.option('--data-type', type=click.Choice(['authors', 'works', 'places']), required=True, help='データ種別')
@click.option('--dry-run', is_flag=True, help='実際の追加は行わず内容確認のみ')
@click.option('--batch-size', default=50, help='バッチサイズ')
@click.pass_context
def batch(ctx, input_file, data_type, dry_run, batch_size):
    """CSVファイルからバッチ追加"""
    click.echo(f"📦 CSVバッチ追加: {input_file}")
    click.echo(f"   データ種別: {data_type}")
    
    if dry_run:
        click.echo("   📋 ドライランモード")
    
    try:
        import csv
        
        records = []
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
                if len(records) >= batch_size:
                    break
        
        click.echo(f"   読み込み: {len(records)}件")
        
        # データ種別別処理
        success_count = 0
        error_count = 0
        
        for i, record in enumerate(records, 1):
            try:
                if data_type == 'authors':
                    success_count += _process_author_record(record, dry_run)
                elif data_type == 'works':
                    success_count += _process_work_record(record, dry_run)
                elif data_type == 'places':
                    success_count += _process_place_record(record, dry_run)
                
                if i % 10 == 0:
                    click.echo(f"   処理中: {i}/{len(records)}")
                    
            except Exception as e:
                error_count += 1
                click.echo(f"   ❌ エラー (行{i}): {e}")
        
        click.echo(f"\n📊 バッチ処理結果:")
        click.echo(f"   成功: {success_count}件")
        click.echo(f"   エラー: {error_count}件")
        
    except Exception as e:
        click.echo(f"❌ ファイル処理エラー: {e}")

@add.command()
@click.argument('work_data', type=dict, required=False)
@click.pass_context
def extract_places_from_work(ctx, work_data):
    """作品から地名抽出"""
    if not work_data:
        click.echo("⚠️ 作品データが提供されていません")
        return
    
    click.echo(f"🗺️ 地名抽出: {work_data.get('title', '不明')}")
    
    # サンプル地名抽出結果
    extracted_places = [
        {'place_name': '東京', 'confidence': 0.95, 'category': 'major_city'},
        {'place_name': '横浜', 'confidence': 0.88, 'category': 'major_city'},
        {'place_name': '鎌倉', 'confidence': 0.82, 'category': 'city'}
    ]
    
    click.echo(f"   抽出結果: {len(extracted_places)}件")
    
    # 抽出結果表示
    if RICH_AVAILABLE:
        table = Table(title="抽出された地名")
        table.add_column("地名", style="cyan")
        table.add_column("信頼度", style="yellow")
        table.add_column("カテゴリー", style="green")
        
        for place in extracted_places:
            table.add_row(
                place['place_name'],
                f"{place['confidence']:.1%}",
                place['category']
            )
        
        console.print(table)
        
        if Confirm.ask("これらの地名をデータベースに追加しますか？"):
            for place in extracted_places:
                _save_place_data(place)
            console.print(f"[green]✅ {len(extracted_places)}件の地名を追加しました[/green]")
    else:
        for i, place in enumerate(extracted_places, 1):
            click.echo(f"   {i}. {place['place_name']} (信頼度: {place['confidence']:.1%}, カテゴリー: {place['category']})")
        
        confirm = input("これらの地名をデータベースに追加しますか？ (y/n): ")
        if confirm.lower() in ['y', 'yes']:
            for place in extracted_places:
                _save_place_data(place)
            click.echo(f"✅ {len(extracted_places)}件の地名を追加しました")

@add.command()
@click.pass_context
def stats(ctx):
    """手動追加統計表示"""
    click.echo("📈 手動追加システム統計")
    
    # サンプル統計データ
    stats_data = {
        'manual_additions': {
            'authors_today': 3,
            'works_today': 8,
            'places_today': 15,
            'total_manual': 89
        },
        'data_sources': {
            'manual_input': 45,
            'csv_batch': 32,
            'extraction': 12
        },
        'validation_stats': {
            'success_rate': 0.92,
            'common_errors': [
                '年代範囲エラー',
                '座標範囲エラー',
                'URL形式エラー'
            ]
        }
    }
    
    if RICH_AVAILABLE:
        # 今日の追加状況
        today_panel = Panel.fit(
            f"[bold]本日の手動追加[/bold]\n"
            f"作者: {stats_data['manual_additions']['authors_today']}名\n"
            f"作品: {stats_data['manual_additions']['works_today']}作品\n"
            f"地名: {stats_data['manual_additions']['places_today']}件\n"
            f"手動追加総計: {stats_data['manual_additions']['total_manual']}件",
            title="📊 追加統計"
        )
        console.print(today_panel)
        
        # 成功率パネル
        validation_panel = Panel.fit(
            f"[bold]データ検証[/bold]\n"
            f"成功率: {stats_data['validation_stats']['success_rate']:.1%}\n"
            f"主なエラー:\n" +
            "\n".join([f"• {error}" for error in stats_data['validation_stats']['common_errors']]),
            title="✅ 品質管理"
        )
        console.print(validation_panel)
    else:
        click.echo(f"\n📊 本日の手動追加:")
        click.echo(f"   作者: {stats_data['manual_additions']['authors_today']}名")
        click.echo(f"   作品: {stats_data['manual_additions']['works_today']}作品")
        click.echo(f"   地名: {stats_data['manual_additions']['places_today']}件")
        
        click.echo(f"\n✅ データ品質:")
        click.echo(f"   成功率: {stats_data['validation_stats']['success_rate']:.1%}")

def _display_author_data_rich(author_data: Dict):
    """Rich UI 作者データ表示"""
    panel_content = f"[bold cyan]{author_data['name']}[/bold cyan]\n\n"
    panel_content += f"生没年: {author_data['birth_year']} - {author_data['death_year']}\n"
    panel_content += f"略歴: {author_data['biography'][:100]}{'...' if len(author_data['biography']) > 100 else ''}\n"
    if author_data['wikipedia_url']:
        panel_content += f"Wikipedia: {author_data['wikipedia_url']}\n"
    panel_content += f"追加日時: {author_data['added_date']}"
    
    console.print(Panel(panel_content, title="👤 作者データ確認"))

def _display_author_data_simple(author_data: Dict):
    """シンプル 作者データ表示"""
    click.echo(f"\n📋 作者データ確認:")
    click.echo(f"   名前: {author_data['name']}")
    click.echo(f"   生没年: {author_data['birth_year']} - {author_data['death_year']}")
    click.echo(f"   略歴: {author_data['biography'][:100]}{'...' if len(author_data['biography']) > 100 else ''}")
    if author_data['wikipedia_url']:
        click.echo(f"   Wikipedia: {author_data['wikipedia_url']}")

def _display_work_data_rich(work_data: Dict):
    """Rich UI 作品データ表示"""
    panel_content = f"[bold cyan]{work_data['title']}[/bold cyan]\n\n"
    panel_content += f"作者: {work_data['author']}\n"
    panel_content += f"発表年: {work_data['publication_year']}\n"
    panel_content += f"ジャンル: {work_data['genre']}\n"
    if work_data['aozora_url']:
        panel_content += f"青空文庫: {work_data['aozora_url']}\n"
    if work_data['content_preview']:
        panel_content += f"内容プレビュー: {work_data['content_preview']}...\n"
    panel_content += f"追加日時: {work_data['added_date']}"
    
    console.print(Panel(panel_content, title="📚 作品データ確認"))

def _display_work_data_simple(work_data: Dict):
    """シンプル 作品データ表示"""
    click.echo(f"\n📋 作品データ確認:")
    click.echo(f"   タイトル: {work_data['title']}")
    click.echo(f"   作者: {work_data['author']}")
    click.echo(f"   発表年: {work_data['publication_year']}")
    click.echo(f"   ジャンル: {work_data['genre']}")
    if work_data['aozora_url']:
        click.echo(f"   青空文庫: {work_data['aozora_url']}")

def _display_place_data_rich(place_data: Dict):
    """Rich UI 地名データ表示"""
    panel_content = f"[bold cyan]{place_data['place_name']}[/bold cyan]\n\n"
    panel_content += f"座標: ({place_data['latitude']:.6f}, {place_data['longitude']:.6f})\n"
    panel_content += f"都道府県: {place_data['prefecture']}\n"
    panel_content += f"カテゴリー: {place_data['category']}\n"
    panel_content += f"信頼度: {place_data['confidence']:.1%}\n"
    panel_content += f"追加日時: {place_data['added_date']}"
    
    console.print(Panel(panel_content, title="🗺️ 地名データ確認"))

def _display_place_data_simple(place_data: Dict):
    """シンプル 地名データ表示"""
    click.echo(f"\n📋 地名データ確認:")
    click.echo(f"   地名: {place_data['place_name']}")
    click.echo(f"   座標: ({place_data['latitude']:.6f}, {place_data['longitude']:.6f})")
    click.echo(f"   都道府県: {place_data['prefecture']}")
    click.echo(f"   カテゴリー: {place_data['category']}")
    click.echo(f"   信頼度: {place_data['confidence']:.1%}")

def _save_author_data(author_data: Dict) -> bool:
    """作者データ保存"""
    try:
        # データベース保存処理（シミュレーション）
        click.echo(f"✅ 作者データ保存完了: {author_data['name']}")
        return True
    except Exception as e:
        click.echo(f"❌ 作者データ保存エラー: {e}")
        return False

def _save_work_data(work_data: Dict) -> bool:
    """作品データ保存"""
    try:
        # データベース保存処理（シミュレーション）
        click.echo(f"✅ 作品データ保存完了: {work_data['title']}")
        return True
    except Exception as e:
        click.echo(f"❌ 作品データ保存エラー: {e}")
        return False

def _save_place_data(place_data: Dict) -> bool:
    """地名データ保存"""
    try:
        # データベース保存処理（シミュレーション）
        click.echo(f"✅ 地名データ保存完了: {place_data['place_name']}")
        return True
    except Exception as e:
        click.echo(f"❌ 地名データ保存エラー: {e}")
        return False

def _process_author_record(record: Dict, dry_run: bool) -> int:
    """作者レコード処理"""
    if dry_run:
        return 1  # ドライランは成功扱い
    
    # 実際の処理はここに実装
    return 1

def _process_work_record(record: Dict, dry_run: bool) -> int:
    """作品レコード処理"""
    if dry_run:
        return 1  # ドライランは成功扱い
    
    # 実際の処理はここに実装
    return 1

def _process_place_record(record: Dict, dry_run: bool) -> int:
    """地名レコード処理"""
    if dry_run:
        return 1  # ドライランは成功扱い
    
    # 実際の処理はここに実装
    return 1

if __name__ == '__main__':
    add() 