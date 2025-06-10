#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪ゆかり地図システム v3.0 - メインCLI
"""

import os
from pathlib import Path
import click

# .envファイルの読み込み
try:
    from dotenv import load_dotenv
    # プロジェクトルートの.envファイルを読み込み
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ 環境変数読み込み完了: {env_path}")
    else:
        print(f"⚠️ .envファイルが見つかりません: {env_path}")
except ImportError:
    print("⚠️ python-dotenvがインストールされていません")

from bungo_map.core.database import init_db


@click.group()
@click.version_option(version="3.0.0")
def main():
    """🌟 文豪ゆかり地図システム v3.0"""
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


# 機能モジュールをインポート
from .search import search
from .aozora import aozora
from .add import add
from .ai import ai
from .setup import setup

# 機能をメインCLIに追加
main.add_command(search)
main.add_command(aozora)
main.add_command(add)
main.add_command(ai)
main.add_command(setup)


@main.command()
@click.option('--reset', is_flag=True, help='placesテーブルをリセットしてからパイプラインを実行')
@click.option('--limit', type=int, help='処理する作品数の上限')
@click.option('--batch-size', type=int, default=10, help='バッチサイズ')
@click.option('--ai-geocoding', is_flag=True, default=True, help='AI文脈判断型Geocodingを使用')
@click.option('--enhanced-extraction', is_flag=True, default=True, help='強化版地名抽出を使用')
@click.option('--test-mode', is_flag=True, help='テストモード（3作品のみ処理）')
def pipeline(reset: bool, limit: int, batch_size: int, ai_geocoding: bool, enhanced_extraction: bool, test_mode: bool):
    """🚀 完全統合パイプライン（最新版）
    
    青空文庫処理改善 + AI文脈判断型Geocoding + 強化版地名抽出
    """
    from bungo_map.cli.full_pipeline import FullPipeline
    
    click.echo("🚀 完全統合パイプライン開始")
    click.echo("   ✨ 青空文庫データ処理改善済み")
    click.echo("   🤖 AI文脈判断型Geocoding (88.9%精度)")
    click.echo("   🗺️ 強化版地名抽出器")
    
    # パイプライン設定
    pipeline = FullPipeline()
    pipeline.batch_size = batch_size
    pipeline.use_geocoding = ai_geocoding
    
    if test_mode:
        limit = 3
        click.echo("⚠️ テストモード: 3作品のみ処理")
    
    try:
        # パイプライン実行
        result = pipeline.run_full_pipeline(
            reset_data=reset,
            limit=limit,
            use_ai=enhanced_extraction,
            enable_geocoding=ai_geocoding
        )
        
        # 結果表示
        click.echo("\n🎉 パイプライン完了!")
        
        stats = result.get('stats', {})
        click.echo(f"📊 統計:")
        click.echo(f"   📚 処理作品数: {stats.get('works_processed', 0)}")
        click.echo(f"   🗺️ 抽出地名数: {stats.get('places_extracted', 0)}")
        click.echo(f"   🌍 Geocoding成功: {stats.get('geocoding_success', 0)}")
        click.echo(f"   📈 Geocoding成功率: {stats.get('geocoding_success_rate', 0):.1f}%")
        click.echo(f"   ⏱️ 実行時間: {stats.get('total_time', 0):.1f}秒")
        
        # 抽出手法別統計
        extraction_methods = stats.get('extraction_methods', {})
        if extraction_methods:
            click.echo(f"\n🔍 抽出手法別統計:")
            for method, count in sorted(extraction_methods.items(), key=lambda x: x[1], reverse=True):
                click.echo(f"   {method}: {count}件")
        
    except Exception as e:
        click.echo(f"❌ パイプラインエラー: {e}")
        import traceback
        traceback.print_exc()


@main.command()
@click.option('--place-names', help='テストする地名（カンマ区切り）', default='東京,京都,ローマ,柏,清水')
@click.option('--with-context', is_flag=True, help='文脈付きでテスト')
def test_geocoding(place_names: str, with_context: bool):
    """🤖 AI文脈判断型Geocodingテスト"""
    from bungo_map.ai.context_aware_geocoding import ContextAwareGeocodingService
    
    click.echo("🤖 AI文脈判断型Geocodingテスト")
    
    service = ContextAwareGeocodingService()
    places = [name.strip() for name in place_names.split(',')]
    
    for place_name in places:
        click.echo(f"\n🗺️ テスト地名: {place_name}")
        
        if with_context:
            # 文脈付きテスト
            test_contexts = [
                f"彼は{place_name}という名前の人だった。",  # 人名文脈
                f"今日は{place_name}へ旅行に行った。",     # 地名文脈
                f"{place_name}から電車で帰宅した。",       # 地名文脈
            ]
            
            for context in test_contexts:
                result = service.analyze_and_geocode(place_name, context)
                
                if result.success:
                    click.echo(f"   ✅ {context[:30]}... → 🌍 ({result.latitude:.4f}, {result.longitude:.4f})")
                    click.echo(f"      信頼度: {result.confidence:.2f}, 判定: {result.context_analysis.get('classification', 'N/A')}")
                else:
                    click.echo(f"   ❌ {context[:30]}... → 失敗: {result.error}")
        else:
            # 基本テスト
            result = service.geocode_place_name(place_name)
            
            if result.success:
                click.echo(f"   ✅ 🌍 ({result.latitude:.4f}, {result.longitude:.4f})")
                click.echo(f"      信頼度: {result.confidence:.2f}, 方法: {result.method}")
            else:
                click.echo(f"   ❌ 失敗: {result.error}")


@main.command()
@click.option('--work-id', type=int, help='テストする作品ID')
@click.option('--work-title', help='テストする作品タイトル')
@click.option('--content-only', is_flag=True, help='青空文庫処理のみテスト')
def test_processing(work_id: int, work_title: str, content_only: bool):
    """📚 青空文庫処理＋強化版地名抽出テスト"""
    import sqlite3
    from bungo_map.processors.aozora_content_processor import AozoraContentProcessor
    from bungo_map.extractors.enhanced_place_extractor import EnhancedPlaceExtractor
    
    # 作品取得
    with sqlite3.connect('data/bungo_production.db') as conn:
        if work_id:
            cursor = conn.execute("SELECT work_id, title, content FROM works WHERE work_id = ?", (work_id,))
        elif work_title:
            cursor = conn.execute("SELECT work_id, title, content FROM works WHERE title LIKE ?", (f'%{work_title}%',))
        else:
            cursor = conn.execute("SELECT work_id, title, content FROM works WHERE length(content) > 10000 LIMIT 1")
        
        row = cursor.fetchone()
        if not row:
            click.echo("❌ 指定された作品が見つかりません")
            return
        
        work_id, title, content = row
        
    click.echo(f"📚 テスト作品: {title} (ID: {work_id})")
    click.echo(f"📊 元データ: {len(content):,}文字")
    
    # 青空文庫処理テスト
    processor = AozoraContentProcessor()
    result = processor.process_work_content(work_id, content)
    
    if result['success']:
        click.echo(f"✅ 青空文庫処理成功:")
        stats = result['stats']
        click.echo(f"   📖 {stats['original_length']:,} → {stats['processed_length']:,}文字")
        click.echo(f"   📝 {stats['sentence_count']}文に分割")
        click.echo(f"   📈 圧縮率: {(1 - stats['processed_length']/stats['original_length'])*100:.1f}%")
        
        # サンプル文表示
        sentences = result['sentences']
        click.echo(f"\n📝 サンプル文（最初の3文）:")
        for i, sentence in enumerate(sentences[:3]):
            click.echo(f"   {i+1}. {sentence[:80]}{'...' if len(sentence) > 80 else ''}")
        
        if not content_only:
            # 強化版地名抽出テスト
            click.echo(f"\n🗺️ 強化版地名抽出テスト...")
            extractor = EnhancedPlaceExtractor()
            places = extractor.extract_places_from_work(work_id, content)
            
            click.echo(f"✅ 地名抽出完了: {len(places)}件")
            
            # 地名サンプル表示
            for i, place in enumerate(places[:5]):
                click.echo(f"\n{i+1}. 🗺️ {place.place_name}")
                click.echo(f"   📝 文: {place.sentence[:60]}...")
                click.echo(f"   ⬅️ 前: {place.before_text[:30]}...")
                click.echo(f"   ➡️ 後: {place.after_text[:30]}...")
    else:
        click.echo(f"❌ 青空文庫処理失敗: {result['error']}")


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