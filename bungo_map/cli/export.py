#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
エクスポートコマンド
データをGeoJSON、CSVなどの形式でエクスポート
"""

import click
import json
import csv
from pathlib import Path
from bungo_map.core.database import init_db
from bungo_map.utils import GeoJSONExporter


class ExportManager:
    """エクスポート管理クラス"""
    
    def __init__(self, db_path: str = "data/bungo_production.db"):
        self.db = init_db(db_path)
        self.geojson_exporter = GeoJSONExporter(self.db)
    
    def export_geojson(self, output_path: str = "output/bungo_places.geojson", 
                      preview: bool = False) -> bool:
        """GeoJSONエクスポート"""
        
        if preview:
            # プレビューモード：統計情報のみ表示
            stats = self.geojson_exporter.get_export_stats()
            
            click.echo("📊 GeoJSONエクスポート対象データ:")
            click.echo(f"  - 総地名数: {stats['total_places']}")
            click.echo(f"  - 作者数: {stats['unique_authors']}")
            click.echo(f"  - 作品数: {stats['unique_works']}")
            
            click.echo("\n👥 作者別統計:")
            for author, data in stats['by_author'].items():
                click.echo(f"  - {author}: {data['places']}箇所 ({data['works']}作品)")
            
            click.echo("\n🏷️  カテゴリ別統計:")
            category_names = {
                "prefecture": "都道府県",
                "city": "市区町村", 
                "nature": "自然地名",
                "landmark": "名所",
                "district": "地区",
                "other": "その他"
            }
            for category, count in stats['by_category'].items():
                category_jp = category_names.get(category, category)
                click.echo(f"  - {category_jp}: {count}箇所")
            
            return True
        
        else:
            # 実際のエクスポート実行
            click.echo(f"📤 GeoJSONエクスポート開始: {output_path}")
            
            success = self.geojson_exporter.export_to_file(output_path)
            
            if success:
                # ファイルサイズを確認
                file_size = Path(output_path).stat().st_size
                click.echo(f"✅ エクスポート完了！")
                click.echo(f"  - ファイル: {output_path}")
                click.echo(f"  - サイズ: {file_size:,} bytes")
                
                # 統計情報も表示
                stats = self.geojson_exporter.get_export_stats()
                click.echo(f"  - 地名数: {stats['total_places']}")
                click.echo(f"  - 作者数: {stats['unique_authors']}")
                click.echo(f"  - 作品数: {stats['unique_works']}")
                
                return True
            else:
                click.echo("❌ エクスポートに失敗しました")
                return False
    
    def export_csv(self, output_path: str = "output/bungo_places.csv") -> bool:
        """CSVエクスポート"""
        
        click.echo(f"📤 CSVエクスポート開始: {output_path}")
        
        try:
            # データ取得
            places_data = self.geojson_exporter.get_places_with_metadata()
            
            if not places_data:
                click.echo("❌ エクスポート対象のデータがありません")
                return False
            
            # ディレクトリ作成
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # CSV出力
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                fieldnames = [
                    'place_id', 'place_name', 'lat', 'lng',
                    'author_name', 'birth_year', 'death_year',
                    'work_title', 'confidence', 'extraction_method',
                    'before_text', 'sentence', 'after_text',
                    'work_wiki_url', 'author_wiki_url'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for place in places_data:
                    writer.writerow({
                        'place_id': place['place_id'],
                        'place_name': place['place_name'],
                        'lat': place['lat'],
                        'lng': place['lng'],
                        'author_name': place['author_name'],
                        'birth_year': place['birth_year'],
                        'death_year': place['death_year'],
                        'work_title': place['work_title'],
                        'confidence': place['confidence'],
                        'extraction_method': place['extraction_method'],
                        'before_text': place['before_text'],
                        'sentence': place['sentence'],
                        'after_text': place['after_text'],
                        'work_wiki_url': place['work_wiki_url'],
                        'author_wiki_url': place['author_wiki_url']
                    })
            
            # 結果表示
            file_size = Path(output_path).stat().st_size
            click.echo(f"✅ CSVエクスポート完了！")
            click.echo(f"  - ファイル: {output_path}")
            click.echo(f"  - サイズ: {file_size:,} bytes")
            click.echo(f"  - レコード数: {len(places_data)}")
            
            return True
            
        except Exception as e:
            click.echo(f"❌ CSVエクスポートエラー: {e}")
            return False
    
    def show_sample_geojson(self, limit: int = 3) -> None:
        """GeoJSONサンプル表示"""
        places_data = self.geojson_exporter.get_places_with_metadata()[:limit]
        
        if not places_data:
            click.echo("❌ 表示対象のデータがありません")
            return
        
        click.echo(f"📄 GeoJSONサンプル (最初の{len(places_data)}件):")
        
        # サンプルGeoJSON作成
        features = []
        for place_data in places_data:
            feature = self.geojson_exporter.create_geojson_feature(place_data)
            features.append(feature)
        
        sample_geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        # 整形して表示
        json_str = json.dumps(sample_geojson, ensure_ascii=False, indent=2)
        click.echo(json_str)


@click.command()
@click.option('--format', 'export_format', type=click.Choice(['geojson', 'csv']), 
              default='geojson', help='エクスポート形式')
@click.option('--output', '-o', help='出力ファイルパス')
@click.option('--preview', is_flag=True, help='プレビューのみ（実際の出力は行わない）')
@click.option('--sample', is_flag=True, help='サンプルGeoJSONを表示')
def export(export_format: str, output: str, preview: bool, sample: bool):
    """📤 データエクスポートコマンド"""
    
    manager = ExportManager()
    
    if sample:
        # サンプル表示
        manager.show_sample_geojson()
        
    elif export_format == 'geojson':
        # GeoJSONエクスポート
        output_path = output or "output/bungo_places.geojson"
        manager.export_geojson(output_path, preview=preview)
        
    elif export_format == 'csv':
        # CSVエクスポート
        output_path = output or "output/bungo_places.csv"
        if preview:
            click.echo("⚠️ CSV形式ではプレビューモードは利用できません")
        else:
            manager.export_csv(output_path)
    
    else:
        click.echo("使用方法:")
        click.echo("  --format geojson         # GeoJSONエクスポート")
        click.echo("  --format csv             # CSVエクスポート")
        click.echo("  --preview               # プレビューのみ")
        click.echo("  --sample                # サンプル表示")
        click.echo("  -o output.geojson       # 出力ファイル指定")


if __name__ == "__main__":
    export() 