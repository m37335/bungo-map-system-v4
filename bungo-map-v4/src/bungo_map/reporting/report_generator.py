#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
レポート生成機能
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
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import jinja2
import pdfkit
import plotly.graph_objects as go
import plotly.express as px

@dataclass
class ReportConfig:
    """レポート設定"""
    output_dir: str = "reports"
    template_dir: str = "templates"
    format: str = "html"  # html, pdf, markdown
    include_charts: bool = True
    include_tables: bool = True
    include_summary: bool = True
    language: str = "ja"

class ReportGenerator:
    """レポート生成クラス"""
    
    def __init__(self, db_path: str, config: Optional[ReportConfig] = None):
        self.db_path = db_path
        self.config = config or ReportConfig()
        self.console = Console()
        self._init_database()
        self._setup_logging()
        self._setup_templates()
    
    def _init_database(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS report_history (
                    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_type TEXT,
                    parameters TEXT,
                    generated_at TIMESTAMP,
                    output_path TEXT
                )
            """)
    
    def _setup_logging(self):
        """ロギングの設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{self.config.output_dir}/report_generation.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _setup_templates(self):
        """テンプレートの設定"""
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.config.template_dir),
            autoescape=True
        )
    
    def generate_analysis_report(self, analysis_type: str,
                               parameters: Dict[str, Any]) -> str:
        """
        分析レポートの生成
        
        Args:
            analysis_type: 分析タイプ
            parameters: 分析パラメータ
            
        Returns:
            生成されたレポートのパス
        """
        # データの取得
        data = self._get_analysis_data(analysis_type, parameters)
        
        # レポートの生成
        report_content = self._generate_report_content(analysis_type, data)
        
        # レポートの保存
        output_path = self._save_report(report_content, analysis_type)
        
        # 履歴の記録
        self._record_report_generation(analysis_type, parameters, output_path)
        
        return output_path
    
    def _get_analysis_data(self, analysis_type: str,
                          parameters: Dict[str, Any]) -> Dict[str, Any]:
        """分析データの取得"""
        with sqlite3.connect(self.db_path) as conn:
            if analysis_type == "temporal":
                return self._get_temporal_data(conn, parameters)
            elif analysis_type == "regional":
                return self._get_regional_data(conn, parameters)
            elif analysis_type == "author":
                return self._get_author_data(conn, parameters)
            elif analysis_type == "work":
                return self._get_work_data(conn, parameters)
            else:
                raise ValueError(f"未対応の分析タイプ: {analysis_type}")
    
    def _generate_report_content(self, analysis_type: str,
                               data: Dict[str, Any]) -> str:
        """レポート内容の生成"""
        template = self.template_env.get_template(f"{analysis_type}_report.html")
        
        # チャートの生成
        charts = {}
        if self.config.include_charts:
            charts = self._generate_charts(analysis_type, data)
        
        # テーブルの生成
        tables = {}
        if self.config.include_tables:
            tables = self._generate_tables(analysis_type, data)
        
        # サマリーの生成
        summary = {}
        if self.config.include_summary:
            summary = self._generate_summary(analysis_type, data)
        
        # テンプレートのレンダリング
        return template.render(
            data=data,
            charts=charts,
            tables=tables,
            summary=summary,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def _generate_charts(self, analysis_type: str,
                        data: Dict[str, Any]) -> Dict[str, Any]:
        """チャートの生成"""
        charts = {}
        
        if analysis_type == "temporal":
            # 時系列チャート
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=data['dates'],
                y=data['counts'],
                mode='lines+markers',
                name='言及回数'
            ))
            fig.update_layout(
                title='時系列トレンド',
                xaxis_title='日付',
                yaxis_title='言及回数'
            )
            charts['timeline'] = fig.to_html(full_html=False)
            
            # 季節性チャート
            fig = px.bar(
                x=data['months'],
                y=data['monthly_counts'],
                title='月別言及回数'
            )
            charts['seasonality'] = fig.to_html(full_html=False)
            
        elif analysis_type == "regional":
            # 地域分布チャート
            fig = px.choropleth(
                data['prefecture_data'],
                locations='prefecture',
                color='count',
                title='都道府県別地名分布'
            )
            charts['regional'] = fig.to_html(full_html=False)
            
            # 上位地名チャート
            fig = px.bar(
                data['top_places'],
                x='place_name',
                y='count',
                title='上位地名'
            )
            charts['top_places'] = fig.to_html(full_html=False)
            
        elif analysis_type == "author":
            # 作家別チャート
            fig = px.bar(
                data['author_data'],
                x='author_name',
                y='place_count',
                title='作家別地名数'
            )
            charts['author'] = fig.to_html(full_html=False)
            
            # 作家間の類似性チャート
            fig = px.imshow(
                data['similarity_matrix'],
                title='作家間の類似性'
            )
            charts['similarity'] = fig.to_html(full_html=False)
            
        elif analysis_type == "work":
            # 作品別チャート
            fig = px.bar(
                data['work_data'],
                x='work_title',
                y='place_count',
                title='作品別地名数'
            )
            charts['work'] = fig.to_html(full_html=False)
            
            # 作品間の関連性チャート
            fig = px.scatter(
                data['work_relationships'],
                x='work1',
                y='work2',
                size='relationship',
                title='作品間の関連性'
            )
            charts['relationships'] = fig.to_html(full_html=False)
        
        return charts
    
    def _generate_tables(self, analysis_type: str,
                        data: Dict[str, Any]) -> Dict[str, Any]:
        """テーブルの生成"""
        tables = {}
        
        if analysis_type == "temporal":
            # 時系列テーブル
            df = pd.DataFrame({
                '日付': data['dates'],
                '言及回数': data['counts']
            })
            tables['timeline'] = df.to_html(index=False)
            
            # 月別集計テーブル
            df = pd.DataFrame({
                '月': data['months'],
                '言及回数': data['monthly_counts']
            })
            tables['monthly'] = df.to_html(index=False)
            
        elif analysis_type == "regional":
            # 都道府県別テーブル
            tables['prefecture'] = pd.DataFrame(data['prefecture_data']).to_html(index=False)
            
            # 上位地名テーブル
            tables['top_places'] = pd.DataFrame(data['top_places']).to_html(index=False)
            
        elif analysis_type == "author":
            # 作家別テーブル
            tables['author'] = pd.DataFrame(data['author_data']).to_html(index=False)
            
            # 作家間の類似性テーブル
            tables['similarity'] = pd.DataFrame(
                data['similarity_matrix'],
                index=data['author_names'],
                columns=data['author_names']
            ).to_html()
            
        elif analysis_type == "work":
            # 作品別テーブル
            tables['work'] = pd.DataFrame(data['work_data']).to_html(index=False)
            
            # 作品間の関連性テーブル
            tables['relationships'] = pd.DataFrame(data['work_relationships']).to_html(index=False)
        
        return tables
    
    def _generate_summary(self, analysis_type: str,
                         data: Dict[str, Any]) -> Dict[str, Any]:
        """サマリーの生成"""
        summary = {}
        
        if analysis_type == "temporal":
            summary = {
                'total_mentions': sum(data['counts']),
                'average_mentions': np.mean(data['counts']),
                'max_mentions': max(data['counts']),
                'min_mentions': min(data['counts']),
                'trend': self._calculate_trend(data['counts'])
            }
            
        elif analysis_type == "regional":
            summary = {
                'total_places': len(data['prefecture_data']),
                'total_mentions': sum(d['count'] for d in data['prefecture_data']),
                'most_common_prefecture': max(
                    data['prefecture_data'],
                    key=lambda x: x['count']
                )['prefecture'],
                'top_place': data['top_places'][0]['place_name']
            }
            
        elif analysis_type == "author":
            summary = {
                'total_authors': len(data['author_data']),
                'total_places': sum(d['place_count'] for d in data['author_data']),
                'most_productive_author': max(
                    data['author_data'],
                    key=lambda x: x['place_count']
                )['author_name']
            }
            
        elif analysis_type == "work":
            summary = {
                'total_works': len(data['work_data']),
                'total_places': sum(d['place_count'] for d in data['work_data']),
                'most_mentioned_work': max(
                    data['work_data'],
                    key=lambda x: x['place_count']
                )['work_title']
            }
        
        return summary
    
    def _save_report(self, content: str, analysis_type: str) -> str:
        """レポートの保存"""
        # 出力ディレクトリの作成
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # ファイル名の生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{analysis_type}_report_{timestamp}"
        
        if self.config.format == "html":
            output_path = output_dir / f"{filename}.html"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
        elif self.config.format == "pdf":
            output_path = output_dir / f"{filename}.pdf"
            pdfkit.from_string(content, str(output_path))
        elif self.config.format == "markdown":
            output_path = output_dir / f"{filename}.md"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        return str(output_path)
    
    def _record_report_generation(self, analysis_type: str,
                                parameters: Dict[str, Any],
                                output_path: str):
        """レポート生成の記録"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO report_history (
                    report_type, parameters, generated_at, output_path
                ) VALUES (?, ?, ?, ?)
            """, (
                analysis_type,
                json.dumps(parameters),
                datetime.now().isoformat(),
                output_path
            ))
    
    def _calculate_trend(self, values: List[float]) -> str:
        """トレンドの計算"""
        if len(values) < 2:
            return "データ不足"
        
        slope = np.polyfit(range(len(values)), values, 1)[0]
        
        if slope > 0.1:
            return "上昇傾向"
        elif slope < -0.1:
            return "下降傾向"
        else:
            return "横ばい"
    
    def _get_temporal_data(self, conn: sqlite3.Connection,
                          parameters: Dict[str, Any]) -> Dict[str, Any]:
        """時系列データの取得"""
        cursor = conn.execute("""
            SELECT 
                date(created_at) as date,
                COUNT(*) as count
            FROM sentence_places
            WHERE created_at BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        """, (parameters['start_date'], parameters['end_date']))
        
        rows = cursor.fetchall()
        return {
            'dates': [row[0] for row in rows],
            'counts': [row[1] for row in rows],
            'months': [row[0][:7] for row in rows],
            'monthly_counts': [row[1] for row in rows]
        }
    
    def _get_regional_data(self, conn: sqlite3.Connection,
                          parameters: Dict[str, Any]) -> Dict[str, Any]:
        """地域データの取得"""
        cursor = conn.execute("""
            SELECT 
                prefecture,
                COUNT(DISTINCT place_id) as place_count,
                COUNT(*) as mention_count
            FROM places_master
            GROUP BY prefecture
        """)
        
        prefecture_data = [
            {
                'prefecture': row[0],
                'count': row[2]
            }
            for row in cursor.fetchall()
        ]
        
        cursor = conn.execute("""
            SELECT 
                place_name,
                COUNT(*) as count
            FROM places_master
            GROUP BY place_id
            ORDER BY count DESC
            LIMIT 10
        """)
        
        top_places = [
            {
                'place_name': row[0],
                'count': row[1]
            }
            for row in cursor.fetchall()
        ]
        
        return {
            'prefecture_data': prefecture_data,
            'top_places': top_places
        }
    
    def _get_author_data(self, conn: sqlite3.Connection,
                        parameters: Dict[str, Any]) -> Dict[str, Any]:
        """作家データの取得"""
        cursor = conn.execute("""
            SELECT 
                a.author_name,
                COUNT(DISTINCT w.work_id) as work_count,
                COUNT(DISTINCT pm.place_id) as place_count
            FROM authors a
            JOIN works w ON a.author_id = w.author_id
            JOIN sentences s ON w.work_id = s.work_id
            JOIN sentence_places sp ON s.sentence_id = sp.sentence_id
            JOIN places_master pm ON sp.place_id = pm.place_id
            GROUP BY a.author_id
        """)
        
        author_data = [
            {
                'author_name': row[0],
                'work_count': row[1],
                'place_count': row[2]
            }
            for row in cursor.fetchall()
        ]
        
        # 作家間の類似性計算
        author_names = [d['author_name'] for d in author_data]
        similarity_matrix = np.zeros((len(author_names), len(author_names)))
        
        for i, author1 in enumerate(author_names):
            for j, author2 in enumerate(author_names):
                if i != j:
                    similarity = self._calculate_author_similarity(
                        conn, author1, author2
                    )
                    similarity_matrix[i, j] = similarity
        
        return {
            'author_data': author_data,
            'author_names': author_names,
            'similarity_matrix': similarity_matrix.tolist()
        }
    
    def _get_work_data(self, conn: sqlite3.Connection,
                      parameters: Dict[str, Any]) -> Dict[str, Any]:
        """作品データの取得"""
        cursor = conn.execute("""
            SELECT 
                w.work_title,
                a.author_name,
                COUNT(DISTINCT pm.place_id) as place_count
            FROM works w
            JOIN authors a ON w.author_id = a.author_id
            JOIN sentences s ON w.work_id = s.work_id
            JOIN sentence_places sp ON s.sentence_id = sp.sentence_id
            JOIN places_master pm ON sp.place_id = pm.place_id
            GROUP BY w.work_id
        """)
        
        work_data = [
            {
                'work_title': row[0],
                'author_name': row[1],
                'place_count': row[2]
            }
            for row in cursor.fetchall()
        ]
        
        # 作品間の関連性計算
        work_relationships = []
        for i, work1 in enumerate(work_data):
            for j, work2 in enumerate(work_data):
                if i != j:
                    relationship = self._calculate_work_relationship(
                        conn, work1['work_title'], work2['work_title']
                    )
                    work_relationships.append({
                        'work1': work1['work_title'],
                        'work2': work2['work_title'],
                        'relationship': relationship
                    })
        
        return {
            'work_data': work_data,
            'work_relationships': work_relationships
        }
    
    def _calculate_author_similarity(self, conn: sqlite3.Connection,
                                   author1: str, author2: str) -> float:
        """作家間の類似性計算"""
        cursor = conn.execute("""
            WITH author1_places AS (
                SELECT DISTINCT pm.place_id
                FROM places_master pm
                JOIN sentence_places sp ON pm.place_id = sp.place_id
                JOIN sentences s ON sp.sentence_id = s.sentence_id
                JOIN works w ON s.work_id = w.work_id
                JOIN authors a ON w.author_id = a.author_id
                WHERE a.author_name = ?
            ),
            author2_places AS (
                SELECT DISTINCT pm.place_id
                FROM places_master pm
                JOIN sentence_places sp ON pm.place_id = sp.place_id
                JOIN sentences s ON sp.sentence_id = s.sentence_id
                JOIN works w ON s.work_id = w.work_id
                JOIN authors a ON w.author_id = a.author_id
                WHERE a.author_name = ?
            )
            SELECT 
                COUNT(DISTINCT a1.place_id) as common_places,
                COUNT(DISTINCT a1.place_id) + COUNT(DISTINCT a2.place_id) as total_places
            FROM author1_places a1
            FULL OUTER JOIN author2_places a2 ON a1.place_id = a2.place_id
        """, (author1, author2))
        
        row = cursor.fetchone()
        if row[1] == 0:
            return 0.0
        return row[0] / row[1]
    
    def _calculate_work_relationship(self, conn: sqlite3.Connection,
                                   work1: str, work2: str) -> float:
        """作品間の関連性計算"""
        cursor = conn.execute("""
            WITH work1_places AS (
                SELECT DISTINCT pm.place_id
                FROM places_master pm
                JOIN sentence_places sp ON pm.place_id = sp.place_id
                JOIN sentences s ON sp.sentence_id = s.sentence_id
                JOIN works w ON s.work_id = w.work_id
                WHERE w.work_title = ?
            ),
            work2_places AS (
                SELECT DISTINCT pm.place_id
                FROM places_master pm
                JOIN sentence_places sp ON pm.place_id = sp.place_id
                JOIN sentences s ON sp.sentence_id = s.sentence_id
                JOIN works w ON s.work_id = w.work_id
                WHERE w.work_title = ?
            )
            SELECT 
                COUNT(DISTINCT w1.place_id) as common_places,
                COUNT(DISTINCT w1.place_id) + COUNT(DISTINCT w2.place_id) as total_places
            FROM work1_places w1
            FULL OUTER JOIN work2_places w2 ON w1.place_id = w2.place_id
        """, (work1, work2))
        
        row = cursor.fetchone()
        if row[1] == 0:
            return 0.0
        return row[0] / row[1] 