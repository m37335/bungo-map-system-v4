#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名データ品質分析CLI
"""

import json
import logging
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.progress import Progress

from ..ai.analyzer import PlaceAnalyzer, AnalysisConfig

logger = logging.getLogger(__name__)
console = Console()

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='分析結果の出力ファイル')
@click.option('--min-confidence', type=float, default=0.7, help='最小信頼度閾値')
@click.option('--min-accuracy', type=float, default=0.8, help='最小座標精度閾値')
@click.option('--no-context', is_flag=True, help='文脈分析を無効化')
@click.option('--no-type', is_flag=True, help='タイプ分析を無効化')
def analyze(input_file: str, output: Optional[str], min_confidence: float,
           min_accuracy: float, no_context: bool, no_type: bool) -> None:
    """地名データの品質分析を実行"""
    try:
        # 入力ファイルの読み込み
        with open(input_file, 'r', encoding='utf-8') as f:
            places = json.load(f)
        
        # 分析設定
        config = AnalysisConfig(
            min_confidence=min_confidence,
            min_coordinate_accuracy=min_accuracy,
            enable_context_analysis=not no_context,
            enable_type_analysis=not no_type
        )
        
        # 分析実行
        analyzer = PlaceAnalyzer(config)
        with Progress() as progress:
            task = progress.add_task("[cyan]分析中...", total=len(places))
            
            report = analyzer.analyze_places(places)
            progress.update(task, completed=len(places))
        
        # 結果表示
        analyzer.display_report(report)
        
        # 結果保存
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            console.print(f"\n[green]分析結果を保存しました: {output_path}[/green]")
    
    except Exception as e:
        logger.error(f"分析中にエラーが発生しました: {str(e)}")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    analyze() 