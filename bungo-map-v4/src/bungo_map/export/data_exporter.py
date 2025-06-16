#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データエクスポート機能
"""

import sqlite3
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime
import json
from collections import defaultdict
import logging
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from pathlib import Path
import csv
import yaml
import xml.etree.ElementTree as ET
import geojson
from shapely.geometry import Point
import folium
import plotly.graph_objects as go
import plotly.express as px

@dataclass
class ExportConfig:
    """エクスポート設定"""
    output_dir: str = "exports"
    format: str = "csv"  # csv, json, yaml, xml, geojson, html
    encoding: str = "utf-8"
    include_metadata: bool = True
    compress: bool = False
    batch_size: int = 1000

class DataExporter:
    """データエクスポートクラス"""
    
    def __init__(self, db_path: str, config: Optional[ExportConfig] = None):
        self.db_path = db_path
        self.config = config or ExportConfig()
        self.console = Console()
        self._init_database()
        self._setup_logging()
    
    def _init_database(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS export_history (
                    export_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    export_type TEXT,
                    parameters TEXT,
                    exported_at TIMESTAMP,
                    output_path TEXT
                )
            """)
    
    def _setup_logging(self):
        """ロギングの設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{self.config.output_dir}/export.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def export_places(self, places: List[Dict[str, Any]]) -> str:
        """
        地名データのエクスポート
        
        Args:
            places: エクスポートする地名データのリスト
            
        Returns:
            エクスポートされたファイルのパス
        """
        # 出力ディレクトリの作成
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # ファイル名の生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"places_{timestamp}"
        
        # エクスポート処理
        if self.config.format == "csv":
            output_path = self._export_to_csv(places, output_dir / f"{filename}.csv")
        elif self.config.format == "json":
            output_path = self._export_to_json(places, output_dir / f"{filename}.json")
        elif self.config.format == "yaml":
            output_path = self._export_to_yaml(places, output_dir / f"{filename}.yaml")
        elif self.config.format == "xml":
            output_path = self._export_to_xml(places, output_dir / f"{filename}.xml")
        elif self.config.format == "geojson":
            output_path = self._export_to_geojson(places, output_dir / f"{filename}.geojson")
        elif self.config.format == "html":
            output_path = self._export_to_html(places, output_dir / f"{filename}.html")
        else:
            raise ValueError(f"未対応のフォーマット: {self.config.format}")
        
        # 履歴の記録
        self._record_export("places", {}, str(output_path))
        
        return str(output_path)
    
    def export_works(self, works: List[Dict[str, Any]]) -> str:
        """
        作品データのエクスポート
        
        Args:
            works: エクスポートする作品データのリスト
            
        Returns:
            エクスポートされたファイルのパス
        """
        # 出力ディレクトリの作成
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # ファイル名の生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"works_{timestamp}"
        
        # エクスポート処理
        if self.config.format == "csv":
            output_path = self._export_to_csv(works, output_dir / f"{filename}.csv")
        elif self.config.format == "json":
            output_path = self._export_to_json(works, output_dir / f"{filename}.json")
        elif self.config.format == "yaml":
            output_path = self._export_to_yaml(works, output_dir / f"{filename}.yaml")
        elif self.config.format == "xml":
            output_path = self._export_to_xml(works, output_dir / f"{filename}.xml")
        elif self.config.format == "html":
            output_path = self._export_to_html(works, output_dir / f"{filename}.html")
        else:
            raise ValueError(f"未対応のフォーマット: {self.config.format}")
        
        # 履歴の記録
        self._record_export("works", {}, str(output_path))
        
        return str(output_path)
    
    def export_authors(self, authors: List[Dict[str, Any]]) -> str:
        """
        作家データのエクスポート
        
        Args:
            authors: エクスポートする作家データのリスト
            
        Returns:
            エクスポートされたファイルのパス
        """
        # 出力ディレクトリの作成
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # ファイル名の生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"authors_{timestamp}"
        
        # エクスポート処理
        if self.config.format == "csv":
            output_path = self._export_to_csv(authors, output_dir / f"{filename}.csv")
        elif self.config.format == "json":
            output_path = self._export_to_json(authors, output_dir / f"{filename}.json")
        elif self.config.format == "yaml":
            output_path = self._export_to_yaml(authors, output_dir / f"{filename}.yaml")
        elif self.config.format == "xml":
            output_path = self._export_to_xml(authors, output_dir / f"{filename}.xml")
        elif self.config.format == "html":
            output_path = self._export_to_html(authors, output_dir / f"{filename}.html")
        else:
            raise ValueError(f"未対応のフォーマット: {self.config.format}")
        
        # 履歴の記録
        self._record_export("authors", {}, str(output_path))
        
        return str(output_path)
    
    def _export_to_csv(self, data: List[Dict[str, Any]], output_path: Path) -> Path:
        """CSV形式でのエクスポート"""
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False, encoding=self.config.encoding)
        return output_path
    
    def _export_to_json(self, data: List[Dict[str, Any]], output_path: Path) -> Path:
        """JSON形式でのエクスポート"""
        with open(output_path, "w", encoding=self.config.encoding) as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return output_path
    
    def _export_to_yaml(self, data: List[Dict[str, Any]], output_path: Path) -> Path:
        """YAML形式でのエクスポート"""
        with open(output_path, "w", encoding=self.config.encoding) as f:
            yaml.dump(data, f, allow_unicode=True)
        return output_path
    
    def _export_to_xml(self, data: List[Dict[str, Any]], output_path: Path) -> Path:
        """XML形式でのエクスポート"""
        root = ET.Element("data")
        
        for item in data:
            record = ET.SubElement(root, "record")
            for key, value in item.items():
                field = ET.SubElement(record, key)
                field.text = str(value)
        
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding=self.config.encoding, xml_declaration=True)
        return output_path
    
    def _export_to_geojson(self, data: List[Dict[str, Any]], output_path: Path) -> Path:
        """GeoJSON形式でのエクスポート"""
        features = []
        
        for item in data:
            if 'latitude' in item and 'longitude' in item:
                point = Point(item['longitude'], item['latitude'])
                feature = geojson.Feature(
                    geometry=point,
                    properties={
                        k: v for k, v in item.items()
                        if k not in ['latitude', 'longitude']
                    }
                )
                features.append(feature)
        
        feature_collection = geojson.FeatureCollection(features)
        
        with open(output_path, "w", encoding=self.config.encoding) as f:
            geojson.dump(feature_collection, f)
        
        return output_path
    
    def _export_to_html(self, data: List[Dict[str, Any]], output_path: Path) -> Path:
        """HTML形式でのエクスポート"""
        # データフレームの作成
        df = pd.DataFrame(data)
        
        # HTMLテーブルの生成
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="{self.config.encoding}">
            <title>データエクスポート</title>
            <style>
                table {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
            </style>
        </head>
        <body>
            <h1>データエクスポート</h1>
            <p>生成日時: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            {df.to_html(index=False)}
        </body>
        </html>
        """
        
        with open(output_path, "w", encoding=self.config.encoding) as f:
            f.write(html_content)
        
        return output_path
    
    def _record_export(self, export_type: str,
                      parameters: Dict[str, Any],
                      output_path: str):
        """エクスポート履歴の記録"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO export_history (
                    export_type, parameters, exported_at, output_path
                ) VALUES (?, ?, ?, ?)
            """, (
                export_type,
                json.dumps(parameters),
                datetime.now().isoformat(),
                output_path
            ))
    
    def get_export_history(self) -> List[Dict[str, Any]]:
        """エクスポート履歴の取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    export_id,
                    export_type,
                    parameters,
                    exported_at,
                    output_path
                FROM export_history
                ORDER BY exported_at DESC
            """)
            
            return [
                {
                    'export_id': row[0],
                    'export_type': row[1],
                    'parameters': json.loads(row[2]),
                    'exported_at': row[3],
                    'output_path': row[4]
                }
                for row in cursor.fetchall()
            ]
    
    def export_all_data(self) -> Dict[str, str]:
        """
        全データのエクスポート
        
        Returns:
            エクスポートされたファイルのパスの辞書
        """
        results = {}
        
        with sqlite3.connect(self.db_path) as conn:
            # 地名データの取得とエクスポート
            cursor = conn.execute("SELECT * FROM places_master")
            places = [dict(row) for row in cursor.fetchall()]
            results['places'] = self.export_places(places)
            
            # 作品データの取得とエクスポート
            cursor = conn.execute("SELECT * FROM works")
            works = [dict(row) for row in cursor.fetchall()]
            results['works'] = self.export_works(works)
            
            # 作家データの取得とエクスポート
            cursor = conn.execute("SELECT * FROM authors")
            authors = [dict(row) for row in cursor.fetchall()]
            results['authors'] = self.export_authors(authors)
        
        return results 