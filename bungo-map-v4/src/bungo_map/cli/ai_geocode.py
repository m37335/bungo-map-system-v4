#!/usr/bin/env python3

"""地名ジオコーディングCLIコマンド

地名から座標を取得するジオコーディングコマンドを提供します。
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress

from ..ai.geocoder import PlaceGeocoder, GeocoderConfig

logger = logging.getLogger(__name__)
console = Console()

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='出力ファイルパス')
@click.option('--api-key', envvar='GOOGLE_MAPS_API_KEY', help='Google Maps APIキー')
@click.option('--batch-size', type=int, default=10, help='バッチサイズ')
@click.option('--retry-count', type=int, default=3, help='リトライ回数')
@click.option('--retry-delay', type=float, default=1.0, help='リトライ待機時間（秒）')
def geocode(
    input_file: str,
    output: Optional[str],
    api_key: Optional[str],
    batch_size: int,
    retry_count: int,
    retry_delay: float
) -> None:
    """地名データをジオコーディングします。
    
    Google Maps APIを使用して地名から座標を取得します。
    APIキーは環境変数GOOGLE_MAPS_API_KEYで設定することもできます。
    """
    try:
        # APIキーの確認
        if not api_key:
            raise click.ClickException(
                "Google Maps APIキーが必要です。"
                "環境変数GOOGLE_MAPS_API_KEYを設定するか、--api-keyオプションで指定してください。"
            )
        
        # 入力ファイルの読み込み
        with open(input_file, 'r', encoding='utf-8') as f:
            places = json.load(f)
        
        # 設定の作成
        config = GeocoderConfig(
            api_key=api_key,
            batch_size=batch_size,
            retry_count=retry_count,
            retry_delay=retry_delay
        )
        
        # ジオコーディングの実行
        geocoder = PlaceGeocoder(config)
        with Progress() as progress:
            task = progress.add_task("ジオコーディング中...", total=len(places))
            geocoded_places = geocoder.geocode_places(places)
            progress.update(task, completed=len(places))
        
        # 結果の表示
        geocoder.display_stats()
        
        # 結果の保存
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(geocoded_places, f, ensure_ascii=False, indent=2)
            console.print(f"[green]結果を保存しました: {output_path}")
        
    except Exception as e:
        logger.error(f"ジオコーディング中にエラーが発生しました: {e}")
        raise click.ClickException(str(e))
