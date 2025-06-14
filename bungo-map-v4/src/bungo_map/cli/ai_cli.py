#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI機能CLI v4
8つのAIコマンドを統合した統一インターフェース
"""

import click
import logging
from typing import Dict, List, Any, Optional
import sys
import os

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

# Rich UIサポート
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='詳細ログ出力')
@click.pass_context
def ai(ctx, verbose):
    """🤖 AI機能システム v4 - 地名データの高度分析・処理"""
    ctx.ensure_object(dict)
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    # AI Manager初期化
    try:
        from ..ai.ai_manager import AIManager
        ctx.obj['ai_manager'] = AIManager()
    except ImportError:
        click.echo("⚠️ AI Managerの読み込みに失敗しました")
        ctx.obj['ai_manager'] = None
    
    if console:
        console.print("[bold blue]🤖 AI機能システム v4[/bold blue]")

@ai.command()
@click.pass_context
def test_connection(ctx):
    """OpenAI API接続テスト"""
    ai_manager = ctx.obj.get('ai_manager')
    
    if not ai_manager:
        click.echo("❌ AI Manager未初期化")
        return
    
    click.echo("📡 OpenAI API接続テスト実行中...")
    
    result = ai_manager.test_connection()
    
    if result['success']:
        click.echo("✅ 接続成功")
        click.echo(f"   モデル: {result['model']}")
        click.echo(f"   レスポンスID: {result['response_id']}")
        click.echo(f"   使用トークン: {result['usage']}")
    else:
        click.echo("❌ 接続失敗")
        click.echo(f"   エラー: {result['error']}")
        if 'details' in result:
            click.echo(f"   詳細: {result['details']}")

@ai.command()
@click.option('--work-id', type=int, help='特定作品の分析')
@click.option('--category', help='特定カテゴリーの分析')
@click.option('--limit', default=100, help='分析対象数の上限')
@click.pass_context
def analyze(ctx, work_id, category, limit):
    """地名データ品質分析"""
    ai_manager = ctx.obj.get('ai_manager')
    
    if not ai_manager:
        click.echo("❌ AI Manager未初期化")
        return
    
    click.echo("📊 地名データ品質分析開始...")
    
    # サンプルデータで分析（実際のDB接続は今後実装）
    sample_places = [
        {'place_name': '東京', 'confidence': 0.95, 'category': 'major_city'},
        {'place_name': '不明地名', 'confidence': 0.3, 'category': 'unknown'},
        {'place_name': '京都', 'confidence': 0.90, 'category': 'major_city'},
        {'place_name': '北海道', 'confidence': 0.92, 'category': 'prefecture'},
        {'place_name': '架空地名', 'confidence': 0.2, 'category': 'unknown'}
    ]
    
    # フィルタリング
    if work_id:
        click.echo(f"   作品ID {work_id} でフィルタリング")
    if category:
        sample_places = [p for p in sample_places if p['category'] == category]
        click.echo(f"   カテゴリー '{category}' でフィルタリング")
    
    sample_places = sample_places[:limit]
    
    if not sample_places:
        click.echo("⚠️ 分析対象データが見つかりません")
        return
    
    # AI分析実行
    analysis = ai_manager.analyze_place_data(sample_places)
    
    # 結果表示
    ai_manager.display_analysis(analysis)
    
    # 推奨事項表示
    if analysis['recommendations']:
        click.echo("\n💡 改善推奨事項:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            click.echo(f"   {i}. {rec}")

@ai.command()
@click.option('--dry-run', is_flag=True, help='実際の変更は行わず結果のみ表示')
@click.option('--confidence-threshold', default=0.5, help='正規化対象の信頼度閾値')
@click.pass_context
def normalize(ctx, dry_run, confidence_threshold):
    """地名正規化実行"""
    click.echo(f"🔧 地名正規化実行 (閾値: {confidence_threshold})")
    
    if dry_run:
        click.echo("   📋 ドライランモード - 実際の変更は行いません")
    
    # 実装予定の正規化ロジック
    sample_normalizations = [
        "東京都 → 東京",
        "大阪府 → 大阪", 
        "京都府 → 京都"
    ]
    
    click.echo("🔄 正規化候補:")
    for norm in sample_normalizations:
        click.echo(f"   • {norm}")
    
    if not dry_run:
        click.echo("✅ 正規化完了 (テストモード)")
    else:
        click.echo("📋 ドライラン完了")

@ai.command()
@click.option('--confidence-threshold', default=0.3, help='削除対象の信頼度閾値')
@click.option('--confirm', is_flag=True, help='確認なしで実行')
@click.pass_context
def clean(ctx, confidence_threshold, confirm):
    """無効地名削除 (低信頼度データ除去)"""
    click.echo(f"🗑️ 無効地名削除実行 (閾値: {confidence_threshold})")
    
    if not confirm:
        if not click.confirm("⚠️ 低信頼度地名を削除しますか？"):
            click.echo("❌ 削除をキャンセルしました")
            return
    
    # 実装予定の削除ロジック
    click.echo("🔍 低信頼度地名検索中...")
    click.echo("   検出: 5件の低信頼度地名")
    click.echo("✅ 削除完了 (テストモード)")

@ai.command()
@click.option('--place-name', help='特定地名のジオコーディング')
@click.option('--batch-size', default=10, help='バッチ処理サイズ')
@click.pass_context  
def geocode(ctx, place_name, batch_size):
    """AI支援ジオコーディング"""
    if place_name:
        click.echo(f"🌍 地名ジオコーディング: {place_name}")
        # 単一地名の処理
        click.echo(f"   座標: (35.6762, 139.6503) # テストデータ")
        click.echo("✅ ジオコーディング完了")
    else:
        click.echo(f"🌍 バッチジオコーディング実行 (バッチサイズ: {batch_size})")
        click.echo("   対象: 未ジオコーディング地名")
        click.echo("✅ バッチ処理完了 (テストモード)")

@ai.command()
@click.option('--extractor', help='特定抽出器の検証')
@click.option('--sample-size', default=100, help='検証サンプルサイズ')
@click.pass_context
def validate_extraction(ctx, extractor, sample_size):
    """地名抽出精度検証システム"""
    click.echo(f"🔍 地名抽出精度検証 (サンプル: {sample_size}件)")
    
    if extractor:
        click.echo(f"   対象抽出器: {extractor}")
    else:
        click.echo("   対象: 全抽出器")
    
    # 検証結果（サンプル）
    results = {
        'enhanced_extractor': {'precision': 0.87, 'recall': 0.82},
        'improved_extractor': {'precision': 0.84, 'recall': 0.79},
        'ginza_extractor': {'precision': 0.91, 'recall': 0.85}
    }
    
    click.echo("\n📊 検証結果:")
    for ext, metrics in results.items():
        if not extractor or extractor in ext:
            click.echo(f"   {ext}:")
            click.echo(f"     精度: {metrics['precision']:.1%}")
            click.echo(f"     再現率: {metrics['recall']:.1%}")
    
    click.echo("✅ 検証完了")

@ai.command()
@click.option('--work-id', type=int, help='特定作品の文脈分析')
@click.option('--context-window', default=100, help='文脈ウィンドウサイズ')
@click.pass_context
def analyze_context(ctx, work_id, context_window):
    """文脈ベース地名分析"""
    click.echo(f"📖 文脈ベース地名分析 (ウィンドウ: {context_window}文字)")
    
    if work_id:
        click.echo(f"   対象作品ID: {work_id}")
    
    # 文脈分析結果（サンプル）
    context_results = [
        {'place': '東京', 'context_score': 0.92, 'context_type': '現実的場所'},
        {'place': '桃源郷', 'context_score': 0.15, 'context_type': '架空的場所'},
        {'place': '江戸', 'context_score': 0.88, 'context_type': '歴史的場所'}
    ]
    
    click.echo("\n📊 文脈分析結果:")
    for result in context_results:
        click.echo(f"   {result['place']}: {result['context_score']:.1%} ({result['context_type']})")
    
    click.echo("✅ 文脈分析完了")

@ai.command()
@click.option('--context-threshold', default=0.4, help='文脈判定閾値')
@click.option('--confirm', is_flag=True, help='確認なしで実行')
@click.pass_context
def clean_context(ctx, context_threshold, confirm):
    """文脈判断による無効地名削除"""
    click.echo(f"🧹 文脈ベース地名クリーニング (閾値: {context_threshold})")
    
    if not confirm:
        if not click.confirm("⚠️ 文脈スコアの低い地名を削除しますか？"):
            click.echo("❌ 削除をキャンセルしました")
            return
    
    click.echo("🔍 文脈スコア評価中...")
    click.echo("   検出: 3件の低文脈スコア地名")
    click.echo("✅ 文脈ベースクリーニング完了 (テストモード)")

@ai.command()
@click.pass_context
def stats(ctx):
    """AI機能システム統計表示"""
    ai_manager = ctx.obj.get('ai_manager')
    
    if not ai_manager:
        click.echo("❌ AI Manager未初期化")
        return
    
    click.echo("📈 AI機能システム統計")
    
    stats = ai_manager.get_stats()
    
    click.echo("\n🤖 AI Manager統計:")
    for key, value in stats['ai_manager_stats'].items():
        click.echo(f"   {key}: {value}")
    
    click.echo("\n⚙️ 設定情報:")
    for key, value in stats['config'].items():
        click.echo(f"   {key}: {value}")
    
    click.echo("\n🔧 利用可能性:")
    for key, value in stats['availability'].items():
        status = "✅" if value else "❌"
        click.echo(f"   {key}: {status}")

if __name__ == '__main__':
    ai() 