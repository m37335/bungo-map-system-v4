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
from bungo_map.ai.ai_manager import AIManager
import os

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
    manager = AIManager(openai_api_key=os.getenv('OPENAI_API_KEY'), google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY'))
    result = manager.analyze(data)
    click.echo(result)

@ai.command()
@click.option('--data', required=True, help='正規化するデータ')
def normalize(data):
    """地名正規化実行（漢字表記統一等）"""
    manager = AIManager(openai_api_key=os.getenv('OPENAI_API_KEY'), google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY'))
    result = manager.normalize(data)
    click.echo(result)

@ai.command()
@click.option('--data', required=True, help='クリーニングするデータ')
def clean(data):
    """無効地名削除（低信頼度データ除去）"""
    manager = AIManager(openai_api_key=os.getenv('OPENAI_API_KEY'), google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY'))
    result = manager.clean(data)
    click.echo(result)

@ai.command()
@click.option('--data', required=True, help='ジオコーディングするデータ')
def geocode(data):
    """AI支援ジオコーディング（Google API統合）"""
    manager = AIManager(openai_api_key=os.getenv('OPENAI_API_KEY'), google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY'))
    result = manager.geocode(data)
    click.echo(result)

@ai.command()
@click.option('--data', required=True, help='検証するデータ')
def validate_extraction(data):
    """地名抽出精度検証システム"""
    manager = AIManager(openai_api_key=os.getenv('OPENAI_API_KEY'), google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY'))
    result = manager.validate_extraction(data)
    click.echo(result)

@ai.command()
@click.option('--data', required=True, help='分析するデータ')
def analyze_context(data):
    """文脈ベース地名分析"""
    manager = AIManager(openai_api_key=os.getenv('OPENAI_API_KEY'), google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY'))
    result = manager.analyze_context(data)
    click.echo(result)

@ai.command()
@click.option('--data', required=True, help='クリーニングするデータ')
def clean_context(data):
    """文脈判断による無効地名削除"""
    manager = AIManager(openai_api_key=os.getenv('OPENAI_API_KEY'), google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY'))
    result = manager.clean_context(data)
    click.echo(result)

@ai.command()
def test_connection():
    """OpenAI API接続テスト"""
    manager = AIManager(openai_api_key=os.getenv('OPENAI_API_KEY'), google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY'))
    manager.test_connection()
    click.echo("接続テスト完了")

if __name__ == '__main__':
    ai() 