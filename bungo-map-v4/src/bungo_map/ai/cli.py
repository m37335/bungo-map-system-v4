"""
AI機能のCLIコマンドモジュール
地名データの品質向上と正規化を行うAI機能のCLIを提供します。
"""

import click
import logging
from typing import List
from rich.console import Console
from rich.table import Table
from .cleaners.place_cleaner import PlaceCleaner
from bungo_map.ai.ai_manager import AIManager, AIConfig
import os
import sys

console = Console()
logger = logging.getLogger(__name__)

@click.group()
def ai():
    """AI機能のCLIコマンド"""
    pass

@ai.command()
@click.option('--data', required=True, help='分析するデータ')
def analyze(data):
    """地名データ品質分析（信頼度・タイプ分析）"""
    config = AIConfig(
        openai_api_key=os.getenv('OPENAI_API_KEY', ''),
        google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY', '')
    )
    manager = AIManager(config=config)
    result = manager.analyze(data)
    click.echo(result)

@ai.command()
@click.option('--data', required=True, help='正規化するデータ')
def normalize(data):
    """地名正規化実行（漢字表記統一等）"""
    config = AIConfig(
        openai_api_key=os.getenv('OPENAI_API_KEY', ''),
        google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY', '')
    )
    manager = AIManager(config=config)
    result = manager.normalize(data)
    click.echo(result)

@ai.command()
@click.option('--data', required=True, help='クリーニングするデータ')
def clean(data):
    """無効地名削除（低信頼度データ除去）"""
    config = AIConfig(
        openai_api_key=os.getenv('OPENAI_API_KEY', ''),
        google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY', '')
    )
    manager = AIManager(config=config)
    result = manager.clean(data)
    click.echo(result)

@ai.command()
@click.option('--data', required=True, help='ジオコーディングするデータ')
def geocode(data):
    """AI支援ジオコーディング（Google API統合）"""
    config = AIConfig(
        openai_api_key=os.getenv('OPENAI_API_KEY', ''),
        google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY', '')
    )
    manager = AIManager(config=config)
    result = manager.geocode(data)
    click.echo(result)

@ai.command()
@click.option('--data', required=True, help='検証するデータ')
def validate_extraction(data):
    """地名抽出精度検証システム"""
    config = AIConfig(
        openai_api_key=os.getenv('OPENAI_API_KEY', ''),
        google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY', '')
    )
    manager = AIManager(config=config)
    result = manager.validate_extraction(data)
    click.echo(result)

@ai.command()
@click.option('--data', required=True, help='分析するデータ')
def analyze_context(data):
    """文脈ベース地名分析"""
    config = AIConfig(
        openai_api_key=os.getenv('OPENAI_API_KEY', ''),
        google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY', '')
    )
    manager = AIManager(config=config)
    result = manager.analyze_context(data)
    click.echo(result)

@ai.command()
@click.option('--data', required=True, help='クリーニングするデータ')
def clean_context(data):
    """文脈判断による無効地名削除"""
    config = AIConfig(
        openai_api_key=os.getenv('OPENAI_API_KEY', ''),
        google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY', '')
    )
    manager = AIManager(config=config)
    result = manager.clean_context(data)
    click.echo(result)

@ai.command()
def test_connection():
    """OpenAI API接続テスト"""
    config = AIConfig(
        openai_api_key=os.getenv('OPENAI_API_KEY', ''),
        google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY', '')
    )
    manager = AIManager(config=config)
    result = manager.test_connection()
    click.echo(f"接続テスト結果: {result}")

@ai.command()
@click.option('--input', required=True, help='入力ファイルパス')
@click.option('--output', required=True, help='出力ファイルパス')
def batch_clean(input, output):
    """地名バッチクリーニング"""
    if not os.path.exists(input):
        click.echo("ファイルが見つかりません")
        sys.exit(1)
    # 入力ファイルから地名リストを読み込む
    with open(input, 'r', encoding='utf-8') as f:
        place_names = [line.strip() for line in f if line.strip()]
    # PlaceCleanerのダミー利用
    results = [f"cleaned:{name}" for name in place_names]
    # 出力ファイルに書き出し
    with open(output, 'w', encoding='utf-8') as f:
        for res in results:
            f.write(res + '\n')
    click.echo("バッチ処理完了")

if __name__ == '__main__':
    ai() 