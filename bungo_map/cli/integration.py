#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 統合地名抽出システム CLI
複数抽出手法の優先順位調整と統合管理
"""

import click
import os
from dotenv import load_dotenv
from bungo_map.ai.integration.extraction_coordinator import ExtractionCoordinator

load_dotenv()

@click.group()
def integration():
    """統合地名抽出システム管理"""
    pass

@integration.command()
@click.option('--text', required=True, help='抽出対象テキスト')
@click.option('--with-ai', is_flag=True, help='AI文脈分析を有効化')
@click.option('--debug', is_flag=True, help='詳細ログ出力')
def extract(text: str, with_ai: bool, debug: bool):
    """統合地名抽出の実行"""
    if debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # APIキー取得
    api_key = os.getenv('OPENAI_API_KEY') if with_ai else None
    
    if with_ai and not api_key:
        click.echo("⚠️  OPENAI_API_KEYが設定されていません。AI機能無効で実行します。")
        api_key = None
    
    coordinator = ExtractionCoordinator(api_key)
    
    click.echo(f"📝 入力テキスト: {text[:100]}...")
    click.echo(f"🤖 AI機能: {'有効' if coordinator.ai_enabled else '無効'}")
    click.echo()
    
    try:
        places = coordinator.extract_and_coordinate(999, text)
        
        if not places:
            click.echo("🔍 地名は検出されませんでした")
            return
        
        click.echo(f"🎯 抽出結果: {len(places)}件\n")
        
        for i, place in enumerate(places, 1):
            click.echo(f"【{i}】 {place.place_name}")
            click.echo(f"    抽出方法: {place.extraction_method}")
            click.echo(f"    信頼度: {place.confidence:.2f}")
            click.echo(f"    文脈: {place.sentence[:60]}...")
            click.echo()
    
    except Exception as e:
        click.echo(f"❌ エラー: {e}")
        if debug:
            import traceback
            traceback.print_exc()

@integration.command()
def show_priority():
    """現在の優先順位設定を表示"""
    coordinator = ExtractionCoordinator()
    stats = coordinator.get_extraction_statistics()
    
    click.echo("🎯 地名抽出手法の優先順位\n")
    
    click.echo("📊 手法別設定:")
    for method, config in stats["method_configs"].items():
        click.echo(f"  {method.value}:")
        click.echo(f"    優先度: {config['priority']} (小さいほど高優先度)")
        click.echo(f"    基本信頼度: {config['base_reliability']}")
        click.echo(f"    信頼度閾値: {config['trust_threshold']}")
        click.echo()
    
    click.echo("🏆 優先順位:")
    for priority in stats["priority_order"]:
        click.echo(f"  {priority}")
    
    click.echo("\n🔧 統合戦略:")
    for key, value in stats["integration_strategy"].items():
        click.echo(f"  {key}: {value}")

@integration.command()
@click.option('--test-file', help='テストケースファイル（省略時はデフォルト）')
def benchmark(test_file: str):
    """抽出精度のベンチマークテスト"""
    # デフォルトテストケース
    test_cases = [
        {
            "text": "然るに、ことしの二月、私は千葉県船橋市に疎開している或る友人をたずねた",
            "expected": ["千葉県船橋市"],
            "should_exclude": ["葉県", "千葉", "船橋"]
        },
        {
            "text": "大きな萩が人の背より高く延びて、その奥に見える東京の空",
            "expected": ["東京"],
            "should_exclude": ["萩"]
        },
        {
            "text": "高柏寺の五重の塔から都のまん中を眺める",
            "expected": [],
            "should_exclude": ["柏", "都"]
        },
        {
            "text": "福岡県京都郡真崎村小川三四郎二十三年学生と正直に書いた",
            "expected": ["福岡県京都郡真崎村", "福岡"],
            "should_exclude": ["岡県", "京都"]
        }
    ]
    
    coordinator_without_ai = ExtractionCoordinator()
    
    click.echo("🧪 抽出精度ベンチマークテスト\n")
    
    total_tests = len(test_cases)
    passed_tests = 0
    
    for i, case in enumerate(test_cases, 1):
        click.echo(f"【テスト{i}】 {case['text'][:50]}...")
        
        places = coordinator_without_ai.extract_and_coordinate(999, case['text'])
        extracted_names = [place.place_name for place in places]
        
        # 期待される地名の確認
        expected_found = [name for name in case['expected'] if name in extracted_names]
        expected_missing = [name for name in case['expected'] if name not in extracted_names]
        
        # 除外すべき地名の確認
        should_exclude_found = [name for name in case['should_exclude'] if name in extracted_names]
        
        # テスト結果の判定
        is_passed = (len(expected_missing) == 0 and len(should_exclude_found) == 0)
        
        if is_passed:
            passed_tests += 1
            click.echo("  ✅ PASS")
        else:
            click.echo("  ❌ FAIL")
        
        click.echo(f"  抽出: {extracted_names}")
        if expected_missing:
            click.echo(f"  未検出: {expected_missing}")
        if should_exclude_found:
            click.echo(f"  誤抽出: {should_exclude_found}")
        
        click.echo()
    
    success_rate = (passed_tests / total_tests) * 100
    click.echo(f"📊 ベンチマーク結果: {passed_tests}/{total_tests} ({success_rate:.1f}%) 成功")

@integration.command()
@click.option('--method', type=click.Choice(['regex', 'ginza_nlp']), required=True, help='調整する手法')
@click.option('--priority', type=int, help='優先度 (0-10)')
@click.option('--threshold', type=float, help='信頼度閾値 (0.0-1.0)')
def tune_priority(method: str, priority: int, threshold: float):
    """優先順位の調整（設定ファイル更新）"""
    click.echo(f"🔧 {method} の設定調整")
    
    if priority is not None:
        click.echo(f"  優先度: {priority}")
    
    if threshold is not None:
        click.echo(f"  信頼度閾値: {threshold}")
    
    click.echo("\n⚠️  実際の設定変更はコード修正が必要です")
    click.echo("   bungo_map/ai/integration/extraction_coordinator.py の method_configs を編集してください")

if __name__ == '__main__':
    integration() 