#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名クリーニングCLIコマンド

地名データの品質を向上させるためのクリーニングコマンドを提供します。
"""

import json
import logging
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.progress import Progress

from ..ai.cleaner import PlaceCleaner, CleanerConfig

logger = logging.getLogger(__name__)
console = Console()

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='出力ファイルパス')
@click.option('--min-confidence', type=float, default=0.7, help='最小信頼度')
@click.option('--min-accuracy', type=float, default=0.8, help='最小精度')
@click.option('--no-duplicates', is_flag=True, help='重複を除去しない')
@click.option('--no-context', is_flag=True, help='文脈検証を無効化')
@click.option('--no-coordinates', is_flag=True, help='座標検証を無効化')
def clean(
    input_file: str,
    output: Optional[str],
    min_confidence: float,
    min_accuracy: float,
    no_duplicates: bool,
    no_context: bool,
    no_coordinates: bool
) -> None:
    """地名データをクリーニングします。
    
    低信頼度データの除去、座標の検証、重複の削除などの機能を提供します。
    """
    try:
        # 入力ファイルの読み込み
        with open(input_file, 'r', encoding='utf-8') as f:
            places = json.load(f)
        
        # 設定の作成
        config = CleanerConfig(
            min_confidence=min_confidence,
            min_accuracy=min_accuracy,
            remove_duplicates=not no_duplicates,
            validate_context=not no_context,
            validate_coordinates=not no_coordinates
        )
        
        # クリーニングの実行
        cleaner = PlaceCleaner(config)
        with Progress() as progress:
            task = progress.add_task("クリーニング中...", total=len(places))
            cleaned_places = cleaner.clean_places(places)
            progress.update(task, completed=len(places))
        
        # 結果の表示
        cleaner.display_stats()
        
        # 結果の保存
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_places, f, ensure_ascii=False, indent=2)
            console.print(f"[green]結果を保存しました: {output_path}")
        
    except Exception as e:
        logger.error(f"クリーニング中にエラーが発生しました: {e}")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    clean() 