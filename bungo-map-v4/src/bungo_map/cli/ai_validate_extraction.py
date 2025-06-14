#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名抽出検証CLI
"""

import json
import logging
from typing import Optional
import click
from rich.console import Console
from rich.progress import Progress
from ..ai.validator import ExtractionValidator, ValidatorConfig

logger = logging.getLogger(__name__)
console = Console()

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='有効な地名の出力ファイルパス')
@click.option('--invalid-output', help='無効な地名の出力ファイルパス')
@click.option('--min-confidence', type=float, default=0.7, help='最小信頼度')
@click.option('--min-accuracy', type=float, default=0.8, help='最小精度')
@click.option('--no-coordinates', is_flag=True, help='座標検証を無効化')
@click.option('--no-context', is_flag=True, help='文脈検証を無効化')
@click.option('--no-duplicates', is_flag=True, help='重複検証を無効化')
def validate_extraction(
    input_file: str,
    output: Optional[str],
    invalid_output: Optional[str],
    min_confidence: float,
    min_accuracy: float,
    no_coordinates: bool,
    no_context: bool,
    no_duplicates: bool
) -> None:
    """地名抽出結果の検証を実行"""
    try:
        # 入力ファイルの読み込み
        with open(input_file, 'r', encoding='utf-8') as f:
            places = json.load(f)
        
        # 検証設定
        config = ValidatorConfig(
            min_confidence=min_confidence,
            min_accuracy=min_accuracy,
            validate_coordinates=not no_coordinates,
            validate_context=not no_context,
            validate_duplicates=not no_duplicates
        )
        
        # 検証実行
        validator = ExtractionValidator(config)
        valid_places, invalid_places = validator.validate_places(places)
        
        # 結果の表示
        validator.display_stats()
        
        # 結果の保存
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(valid_places, f, ensure_ascii=False, indent=2)
            console.print(f"\n[green]有効な地名を保存しました: {output}[/green]")
        
        if invalid_output:
            with open(invalid_output, 'w', encoding='utf-8') as f:
                json.dump(invalid_places, f, ensure_ascii=False, indent=2)
            console.print(f"\n[yellow]無効な地名を保存しました: {invalid_output}[/yellow]")
        
    except Exception as e:
        logger.error(f"検証エラー: {str(e)}")
        raise click.ClickException(str(e)) 