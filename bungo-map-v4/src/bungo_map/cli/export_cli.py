#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
エクスポートシステム CLI v4
GeoJSON・CSV・KML・各種形式のデータエクスポート
"""

import click
import json
import csv
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import os

logger = logging.getLogger(__name__)

# Rich UIサポート
try:
    from rich.console import Console
    from rich.progress import Progress
    from rich.panel import Panel
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='詳細ログ出力')
@click.pass_context
def export(ctx, verbose):
    """📤 データエクスポートシステム v4"""
    ctx.ensure_object(dict)
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    if console:
        console.print("[bold blue]📤 データエクスポートシステム v4[/bold blue]")

@export.command()
@click.argument('output_file', type=click.Path())
@click.option('--work-id', type=int, help='特定作品のみエクスポート')
@click.option('--author', help='特定作者のみエクスポート')
@click.option('--confidence-min', default=0.0, help='信頼度の下限')
@click.option('--category', help='特定カテゴリーのみエクスポート')
@click.option('--include-metadata', is_flag=True, help='メタデータも含める')
@click.pass_context
def geojson(ctx, output_file, work_id, author, confidence_min, category, include_metadata):
    """GeoJSONファイルエクスポート"""
    click.echo(f"🗺️ GeoJSONエクスポート: {output_file}")
    
    # フィルタ条件表示
    filters = []
    if work_id:
        filters.append(f"作品ID: {work_id}")
    if author:
        filters.append(f"作者: {author}")
    if confidence_min > 0:
        filters.append(f"信頼度: {confidence_min}以上")
    if category:
        filters.append(f"カテゴリー: {category}")
    
    if filters:
        click.echo(f"   フィルタ条件: {', '.join(filters)}")
    
    # サンプルGeoJSONデータ生成
    geojson_data = {
        "type": "FeatureCollection",
        "metadata": {
            "generated_by": "文豪ゆかり地図システム v4",
            "export_date": "2024-12-19",
            "total_features": 0,
            "filters": filters if filters else None
        },
        "features": []
    }
    
    # サンプル地名データ
    sample_places = [
        {
            "place_name": "東京駅",
            "latitude": 35.6812,
            "longitude": 139.7671,
            "confidence": 0.95,
            "category": "landmark",
            "work_title": "坊っちゃん",
            "author": "夏目漱石",
            "sentence": "東京駅から汽車に乗って四国へ向かった。"
        },
        {
            "place_name": "京都",
            "latitude": 35.0116,
            "longitude": 135.7681,
            "confidence": 0.92,
            "category": "major_city",
            "work_title": "金閣寺",
            "author": "三島由紀夫",
            "sentence": "古都京都の美しさに心を奪われた。"
        },
        {
            "place_name": "隅田川",
            "latitude": 35.7100,
            "longitude": 139.8000,
            "confidence": 0.88,
            "category": "natural",
            "work_title": "浮雲",
            "author": "二葉亭四迷",
            "sentence": "隅田川の流れを眺めながら物思いにふけった。"
        }
    ]
    
    # フィルタリング適用
    filtered_places = []
    for place in sample_places:
        if confidence_min > 0 and place['confidence'] < confidence_min:
            continue
        if category and place['category'] != category:
            continue
        if author and place['author'] != author:
            continue
        filtered_places.append(place)
    
    # GeoJSON Features生成
    for place in filtered_places:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [place["longitude"], place["latitude"]]
            },
            "properties": {
                "name": place["place_name"],
                "confidence": place["confidence"],
                "category": place["category"]
            }
        }
        
        if include_metadata:
            feature["properties"].update({
                "work_title": place["work_title"],
                "author": place["author"],
                "sentence": place["sentence"]
            })
        
        geojson_data["features"].append(feature)
    
    geojson_data["metadata"]["total_features"] = len(geojson_data["features"])
    
    # ファイル書き込み
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(geojson_data, f, ensure_ascii=False, indent=2)
        
        click.echo(f"✅ GeoJSONエクスポート完了")
        click.echo(f"   出力ファイル: {output_path}")
        click.echo(f"   地名数: {len(geojson_data['features'])}件")
        click.echo(f"   ファイルサイズ: {output_path.stat().st_size:,}バイト")
        
    except Exception as e:
        click.echo(f"❌ エクスポートエラー: {e}")

@export.command()
@click.argument('output_file', type=click.Path())
@click.option('--format', 'csv_format', default='standard', type=click.Choice(['standard', 'places', 'works', 'authors']), help='CSVフォーマット')
@click.option('--encoding', default='utf-8', help='文字エンコーディング')
@click.option('--delimiter', default=',', help='区切り文字')
@click.option('--include-headers', default=True, help='ヘッダー行を含める')
@click.pass_context
def csv(ctx, output_file, csv_format, encoding, delimiter, include_headers):
    """CSVファイルエクスポート"""
    click.echo(f"📊 CSVエクスポート: {output_file}")
    click.echo(f"   フォーマット: {csv_format}")
    click.echo(f"   エンコーディング: {encoding}")
    
    # フォーマット別データ準備
    if csv_format == 'places':
        headers = ['place_name', 'latitude', 'longitude', 'confidence', 'category', 'work_count', 'sentence_count']
        data = [
            ['東京駅', 35.6812, 139.7671, 0.95, 'landmark', 5, 12],
            ['京都', 35.0116, 135.7681, 0.92, 'major_city', 8, 23],
            ['隅田川', 35.7100, 139.8000, 0.88, 'natural', 3, 7]
        ]
    elif csv_format == 'works':
        headers = ['work_id', 'title', 'author', 'publication_year', 'places_count', 'total_sentences']
        data = [
            [1, '坊っちゃん', '夏目漱石', 1906, 45, 1200],
            [2, '羅生門', '芥川龍之介', 1915, 12, 500],
            [3, '舞姫', '森鴎外', 1890, 23, 800]
        ]
    elif csv_format == 'authors':
        headers = ['author_id', 'name', 'birth_year', 'death_year', 'works_count', 'places_count']
        data = [
            [1, '夏目漱石', 1867, 1916, 23, 145],
            [2, '芥川龍之介', 1892, 1927, 15, 89],
            [3, '森鴎外', 1862, 1922, 18, 112]
        ]
    else:  # standard
        headers = ['sentence_id', 'place_name', 'work_title', 'author', 'confidence', 'sentence']
        data = [
            [1, '東京駅', '坊っちゃん', '夏目漱石', 0.95, '東京駅から汽車に乗って四国へ向かった。'],
            [2, '京都', '金閣寺', '三島由紀夫', 0.92, '古都京都の美しさに心を奪われた。'],
            [3, '隅田川', '浮雲', '二葉亭四迷', 0.88, '隅田川の流れを眺めながら物思いにふけった。']
        ]
    
    # CSV書き込み
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding=encoding, newline='') as f:
            writer = csv.writer(f, delimiter=delimiter)
            
            if include_headers:
                writer.writerow(headers)
            
            writer.writerows(data)
        
        click.echo(f"✅ CSVエクスポート完了")
        click.echo(f"   出力ファイル: {output_path}")
        click.echo(f"   レコード数: {len(data)}件")
        click.echo(f"   ファイルサイズ: {output_path.stat().st_size:,}バイト")
        
    except Exception as e:
        click.echo(f"❌ エクスポートエラー: {e}")

@export.command()
@click.argument('output_file', type=click.Path())
@click.option('--template', default='default', help='KMLテンプレート')
@click.option('--icon-style', default='default', help='アイコンスタイル')
@click.pass_context
def kml(ctx, output_file, template, icon_style):
    """KMLファイルエクスポート（Google Earth用）"""
    click.echo(f"🌍 KMLエクスポート: {output_file}")
    click.echo(f"   テンプレート: {template}")
    
    # KMLデータ生成
    kml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>文豪ゆかり地図データ</name>
    <description>文豪ゆかり地図システム v4 エクスポートデータ</description>
    
    <Style id="literaryPlace">
      <IconStyle>
        <scale>1.0</scale>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png</href>
        </Icon>
      </IconStyle>
    </Style>
    
    <Placemark>
      <name>東京駅</name>
      <description><![CDATA[
        <b>作品:</b> 坊っちゃん<br/>
        <b>作者:</b> 夏目漱石<br/>
        <b>信頼度:</b> 95%<br/>
        <b>文:</b> 東京駅から汽車に乗って四国へ向かった。
      ]]></description>
      <styleUrl>#literaryPlace</styleUrl>
      <Point>
        <coordinates>139.7671,35.6812,0</coordinates>
      </Point>
    </Placemark>
    
    <Placemark>
      <name>京都</name>
      <description><![CDATA[
        <b>作品:</b> 金閣寺<br/>
        <b>作者:</b> 三島由紀夫<br/>
        <b>信頼度:</b> 92%<br/>
        <b>文:</b> 古都京都の美しさに心を奪われた。
      ]]></description>
      <styleUrl>#literaryPlace</styleUrl>
      <Point>
        <coordinates>135.7681,35.0116,0</coordinates>
      </Point>
    </Placemark>
    
  </Document>
</kml>"""
    
    # ファイル書き込み
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(kml_data)
        
        click.echo(f"✅ KMLエクスポート完了")
        click.echo(f"   出力ファイル: {output_path}")
        click.echo(f"   ファイルサイズ: {output_path.stat().st_size:,}バイト")
        
    except Exception as e:
        click.echo(f"❌ エクスポートエラー: {e}")

@export.command()
@click.argument('output_file', type=click.Path())
@click.option('--pretty', is_flag=True, help='整形されたJSON出力')
@click.option('--include-stats', is_flag=True, help='統計情報を含める')
@click.pass_context
def json_data(ctx, output_file, pretty, include_stats):
    """JSON形式でデータエクスポート"""
    click.echo(f"📄 JSONエクスポート: {output_file}")
    
    # JSONデータ構造
    json_data = {
        "metadata": {
            "export_format": "json",
            "generated_by": "文豪ゆかり地図システム v4",
            "export_date": "2024-12-19",
            "version": "4.0.0"
        },
        "places": [
            {
                "id": 1,
                "name": "東京駅",
                "coordinates": {"lat": 35.6812, "lng": 139.7671},
                "confidence": 0.95,
                "category": "landmark",
                "appearances": [
                    {
                        "work": "坊っちゃん",
                        "author": "夏目漱石",
                        "sentence": "東京駅から汽車に乗って四国へ向かった。"
                    }
                ]
            },
            {
                "id": 2,
                "name": "京都",
                "coordinates": {"lat": 35.0116, "lng": 135.7681},
                "confidence": 0.92,
                "category": "major_city",
                "appearances": [
                    {
                        "work": "金閣寺",
                        "author": "三島由紀夫", 
                        "sentence": "古都京都の美しさに心を奪われた。"
                    }
                ]
            }
        ]
    }
    
    if include_stats:
        json_data["statistics"] = {
            "total_places": len(json_data["places"]),
            "average_confidence": 0.935,
            "categories": {
                "landmark": 1,
                "major_city": 1
            },
            "authors": {
                "夏目漱石": 1,
                "三島由紀夫": 1
            }
        }
    
    # ファイル書き込み
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(json_data, f, ensure_ascii=False, indent=2, sort_keys=True)
            else:
                json.dump(json_data, f, ensure_ascii=False, separators=(',', ':'))
        
        click.echo(f"✅ JSONエクスポート完了")
        click.echo(f"   出力ファイル: {output_path}")
        click.echo(f"   地名数: {len(json_data['places'])}件")
        click.echo(f"   ファイルサイズ: {output_path.stat().st_size:,}バイト")
        
    except Exception as e:
        click.echo(f"❌ エクスポートエラー: {e}")

@export.command()
@click.argument('output_dir', type=click.Path())
@click.option('--formats', default='geojson,csv,json', help='エクスポート形式（カンマ区切り）')
@click.option('--prefix', default='bungo_map_v4', help='ファイル名プレフィックス')
@click.pass_context
def batch(ctx, output_dir, formats, prefix):
    """バッチエクスポート（複数形式一括）"""
    click.echo(f"📦 バッチエクスポート: {output_dir}")
    
    format_list = [f.strip() for f in formats.split(',')]
    click.echo(f"   対象形式: {', '.join(format_list)}")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 各形式でエクスポート実行
    for fmt in format_list:
        output_file = output_path / f"{prefix}.{fmt}"
        
        try:
            if fmt == 'geojson':
                ctx.invoke(geojson, output_file=str(output_file), include_metadata=True)
            elif fmt == 'csv':
                ctx.invoke(csv, output_file=str(output_file), csv_format='standard')
            elif fmt == 'json':
                ctx.invoke(json_data, output_file=str(output_file), pretty=True, include_stats=True)
            elif fmt == 'kml':
                ctx.invoke(kml, output_file=str(output_file))
            else:
                click.echo(f"⚠️ 未対応形式: {fmt}")
                
        except Exception as e:
            click.echo(f"❌ {fmt}エクスポートエラー: {e}")
    
    click.echo(f"\n🎉 バッチエクスポート完了")
    click.echo(f"   出力ディレクトリ: {output_path}")

@export.command()
@click.pass_context
def stats(ctx):
    """エクスポート機能統計表示"""
    click.echo("📈 エクスポートシステム統計")
    
    if RICH_AVAILABLE:
        from rich.table import Table
        
        table = Table(title="サポート形式")
        table.add_column("形式", style="cyan")
        table.add_column("説明", style="green")
        table.add_column("用途", style="yellow")
        
        table.add_row("GeoJSON", "地理空間データ", "Web地図・GIS")
        table.add_row("CSV", "表形式データ", "Excel・データ分析")
        table.add_row("KML", "Google Earth形式", "3D地図表示")
        table.add_row("JSON", "構造化データ", "API・アプリ連携")
        
        console.print(table)
    else:
        click.echo("\n📊 サポート形式:")
        click.echo("   • GeoJSON: 地理空間データ（Web地図・GIS用）")
        click.echo("   • CSV: 表形式データ（Excel・データ分析用）")
        click.echo("   • KML: Google Earth形式（3D地図表示用）")
        click.echo("   • JSON: 構造化データ（API・アプリ連携用）")

if __name__ == '__main__':
    export() 