#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪ゆかり地図システム v2.0 - メインCLI
"""

import click
from bungo_map.core.database import init_db


@click.group()
@click.version_option(version="2.0.0")
def main():
    """🌟 文豪ゆかり地図システム v2.0"""
    pass


@main.command()
@click.option('--author', help='収集する作者名')
@click.option('--limit', default=5, help='作品数制限')
@click.option('--demo', is_flag=True, help='デモ用サンプルデータ収集')
@click.option('--ginza', is_flag=True, help='GiNZA NLP地名抽出を使用')
def collect(author: str, limit: int, demo: bool, ginza: bool):
    """📚 データ収集"""
    from bungo_map.cli.collect import DataCollector
    
    collector = DataCollector()
    
    if demo:
        # デモ用: 3人の有名作家のデータを収集
        extraction_method = "GiNZA NLP" if ginza else "サンプルデータ"
        click.echo(f"🎭 デモデータ収集開始... (抽出方法: {extraction_method})")
        demo_authors = ["夏目漱石", "芥川龍之介", "太宰治"]
        result = collector.collect_multiple_authors(demo_authors, limit=3, use_ginza=ginza)
        
        click.echo("🎉 デモデータ収集完了！")
        click.echo(f"📊 統計: 作者{result['stats']['authors']}人, "
                  f"作品{result['stats']['works']}作品, "
                  f"地名{result['stats']['places']}箇所")
        
    elif author:
        # 個別作家のデータ収集
        result = collector.collect_author_data(author, limit, use_ginza=ginza)
        
        if result["author"]:
            click.echo("🎉 データ収集完了！")
            click.echo(f"📊 統計: 作者{result['stats']['authors']}人, "
                      f"作品{result['stats']['works']}作品, "
                      f"地名{result['stats']['places']}箇所")
        else:
            click.echo("❌ 作者情報の取得に失敗しました")
    else:
        click.echo("使用方法:")
        click.echo("  --author '夏目漱石'          # 個別作家")
        click.echo("  --demo                      # デモデータ")
        click.echo("  --ginza                     # GiNZA NLP抽出")
        click.echo("  --demo --ginza              # デモ + GiNZA")


# 検索機能は search.py から import
from .search import search

# 検索機能をメインCLIに追加
main.add_command(search)


@main.command()
@click.option('--db-path', default='data/bungo_production.db', help='データベースファイルのパス')
@click.option('--output-dir', default='output', help='出力ディレクトリ')
@click.option('--include-stats', is_flag=True, help='統計情報も出力する')
def export_csv(db_path, output_dir, include_stats):
    """📊 CSV出力"""
    from bungo_map.cli.export_csv import export_csv as csv_export
    csv_export(db_path, output_dir, include_stats)


@main.command()
@click.option('--format', 'export_format', type=click.Choice(['geojson', 'csv']), 
              default='geojson', help='エクスポート形式')
@click.option('--output', '-o', help='出力ファイルパス')
@click.option('--preview', is_flag=True, help='プレビューのみ（実際の出力は行わない）')
@click.option('--sample', is_flag=True, help='サンプルGeoJSONを表示')
def export(export_format: str, output: str, preview: bool, sample: bool):
    """📤 データエクスポート"""
    from bungo_map.cli.export import ExportManager
    
    manager = ExportManager()
    
    if sample:
        # サンプル表示
        manager.show_sample_geojson()
        
    elif export_format == 'geojson':
        # GeoJSONエクスポート
        output_path = output or "output/bungo_places.geojson"
        manager.export_geojson(output_path, preview=preview)
        
    elif export_format == 'csv':
        # CSVエクスポート
        output_path = output or "output/bungo_places.csv"
        if preview:
            click.echo("⚠️ CSV形式ではプレビューモードは利用できません")
        else:
            manager.export_csv(output_path)
    
    else:
        click.echo("使用方法:")
        click.echo("  --format geojson         # GeoJSONエクスポート")
        click.echo("  --format csv             # CSVエクスポート")
        click.echo("  --preview               # プレビューのみ")
        click.echo("  --sample                # サンプル表示")
        click.echo("  -o output.geojson       # 出力ファイル指定")


@main.command()
@click.option('--all', is_flag=True, help='全ての未設定地名をジオコーディング')
@click.option('--limit', type=int, help='処理する地名数の上限')
@click.option('--test', help='テスト用地名（カンマ区切り）')
@click.option('--status', is_flag=True, help='座標設定状況を表示')
def geocode(all: bool, limit: int, test: str, status: bool):
    """🌍 ジオコーディング"""
    from bungo_map.cli.geocode import GeocodeManager
    
    manager = GeocodeManager()
    
    if status:
        # 座標設定状況を表示
        manager.show_coordinates_status()
        
    elif test:
        # テストモード
        test_places = [name.strip() for name in test.split(',')]
        manager.test_geocoder(test_places)
        
    elif all or limit:
        # ジオコーディング実行
        manager.geocode_missing_places(limit)
        
    else:
        click.echo("使用方法:")
        click.echo("  --status                    # 座標設定状況表示")
        click.echo("  --all                       # 全地名をジオコーディング")
        click.echo("  --limit 10                  # 最大10件をジオコーディング")
        click.echo("  --test '東京,京都,松山市'     # テスト実行")


@main.command()
@click.option('--target', type=int, default=30, help='目標作者数')
@click.option('--test-mode', is_flag=True, help='テストモード（少量データで実行）')
@click.option('--test-wikipedia', is_flag=True, help='Wikipedia抽出テスト')
@click.option('--test-aozora', is_flag=True, help='青空文庫抽出テスト')
def expand(target: int, test_mode: bool, test_wikipedia: bool, test_aozora: bool):
    """🚀 データ拡充（Wikipedia・青空文庫）"""
    from bungo_map.cli.expand import DataExpansionEngine
    
    engine = DataExpansionEngine()
    
    if test_wikipedia:
        # Wikipedia抽出テスト
        engine.test_wikipedia_extraction()
    elif test_aozora:
        # 青空文庫抽出テスト
        engine.test_aozora_extraction()
    else:
        # 作者データ拡充
        click.echo(f"🚀 データ拡充開始（目標: {target}名）")
        
        if test_mode:
            click.echo("⚠️ テストモード: 3名まで追加")
        
        result = engine.expand_authors(target, test_mode)
        
        if result.get('status') == 'already_sufficient':
            click.echo("✅ 既に目標数に達しています")
        else:
            click.echo(f"✅ 拡充完了: {result['success_count']}名追加, "
                      f"{result['execution_time']}秒")


@main.command()
def status():
    """📊 システム状況"""
    try:
        db = init_db()
        stats = db.get_stats()
        
        click.echo("📊 システム状況:")
        click.echo(f"  - 作者数: {stats['authors']}")
        click.echo(f"  - 作品数: {stats['works']}")  
        click.echo(f"  - 地名数: {stats['places']}")
        click.echo("✅ データベース接続OK")
        
    except Exception as e:
        click.echo(f"❌ エラー: {e}")


if __name__ == "__main__":
    main() 