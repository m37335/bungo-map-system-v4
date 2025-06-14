#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名正規化CLI
"""

import json
import logging
import os
from typing import Optional
import click
from rich.console import Console
from rich.progress import Progress
from ..ai.normalizer import PlaceNormalizer, NormalizerConfig

logger = logging.getLogger(__name__)
console = Console()

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='出力ファイルパス')
@click.option('--model', default='gpt-4', help='使用するAIモデル')
@click.option('--temperature', type=float, default=0.0, help='AIの創造性（0.0-1.0）')
@click.option('--max-tokens', type=int, default=100, help='最大トークン数')
@click.option('--batch-size', type=int, default=10, help='バッチサイズ')
@click.option('--retry-count', type=int, default=3, help='リトライ回数')
@click.option('--retry-delay', type=float, default=1.0, help='リトライ間隔（秒）')
def normalize(
    input_file: str,
    output: Optional[str],
    model: str,
    temperature: float,
    max_tokens: int,
    batch_size: int,
    retry_count: int,
    retry_delay: float
) -> None:
    """地名データの正規化を実行"""
    try:
        # APIキーの取得
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise click.ClickException(
                "OPENAI_API_KEY環境変数が設定されていません"
            )
        
        # 入力ファイルの読み込み
        with open(input_file, 'r', encoding='utf-8') as f:
            places = json.load(f)
        
        # 正規化設定
        config = NormalizerConfig(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            batch_size=batch_size,
            retry_count=retry_count,
            retry_delay=retry_delay
        )
        
        # 正規化実行
        normalizer = PlaceNormalizer(config)
        normalized_places = normalizer.normalize_places(places)
        
        # 結果の表示
        normalizer.display_stats()
        
        # 結果の保存
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(normalized_places, f, ensure_ascii=False, indent=2)
            console.print(f"\n[green]結果を保存しました: {output}[/green]")
        
    except Exception as e:
        logger.error(f"正規化エラー: {str(e)}")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    normalize() 