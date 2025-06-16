#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
インタラクティブ分析機能
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
from rich.progress import Progress
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

@dataclass
class AnalysisConfig:
    """分析設定"""
    min_mentions: int = 1
    max_places: int = 1000
    time_range: Optional[Tuple[datetime, datetime]] = None
    prefecture_filter: Optional[List[str]] = None
    place_type_filter: Optional[List[str]] = None
    author_filter: Optional[List[str]] = None
    work_filter: Optional[List[str]] = None

class InteractiveAnalyzer:
    """インタラクティブ分析クラス"""
    
    def __init__(self, db_path: str, config: Optional[AnalysisConfig] = None):
        self.db_path = db_path
        self.config = config or AnalysisConfig()
        self.console = Console()
        self._init_database()
    
    def _init_database(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_cache (
                    cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_type TEXT,
                    parameters TEXT,
                    results TEXT,
                    created_at TIMESTAMP
                )
            """)
    
    def start_interactive_session(self):
        """インタラクティブセッションの開始"""
        self.console.print(Panel.fit(
            "🎯 地名分析インタラクティブセッション",
            style="bold blue"
        ))
        
        while True:
            self.console.print("\n利用可能なコマンド:")
            self.console.print("1. 基本統計の表示")
            self.console.print("2. 時系列分析")
            self.console.print("3. 地域分析")
            self.console.print("4. 作家別分析")
            self.console.print("5. 作品別分析")
            self.console.print("6. カスタム分析")
            self.console.print("7. 設定の変更")
            self.console.print("8. 終了")
            
            choice = Prompt.ask("コマンドを選択", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
            
            if choice == "1":
                self._show_basic_statistics()
            elif choice == "2":
                self._analyze_temporal_patterns()
            elif choice == "3":
                self._analyze_regional_patterns()
            elif choice == "4":
                self._analyze_author_patterns()
            elif choice == "5":
                self._analyze_work_patterns()
            elif choice == "6":
                self._run_custom_analysis()
            elif choice == "7":
                self._update_config()
            elif choice == "8":
                if Confirm.ask("セッションを終了しますか？"):
                    break
    
    def _show_basic_statistics(self):
        """基本統計の表示"""
        with sqlite3.connect(self.db_path) as conn:
            # 基本統計の取得
            stats = self._get_basic_statistics(conn)
            
            # テーブルの作成
            table = Table(title="基本統計")
            table.add_column("指標", style="cyan")
            table.add_column("値", style="green")
            
            for key, value in stats.items():
                table.add_row(key, str(value))
            
            self.console.print(table)
    
    def _analyze_temporal_patterns(self):
        """時系列パターンの分析"""
        with sqlite3.connect(self.db_path) as conn:
            # 時系列データの取得
            temporal_data = self._get_temporal_data(conn)
            
            # 分析結果の表示
            self.console.print("\n📈 時系列分析結果")
            
            # トレンドの表示
            trend_table = Table(title="トレンド分析")
            trend_table.add_column("期間", style="cyan")
            trend_table.add_column("傾向", style="green")
            trend_table.add_column("変化率", style="yellow")
            
            for period, trend in temporal_data['trends'].items():
                trend_table.add_row(
                    period,
                    trend['direction'],
                    f"{trend['change_rate']:.1f}%"
                )
            
            self.console.print(trend_table)
            
            # 季節性の表示
            if temporal_data['seasonality']:
                self.console.print("\n📅 季節性パターン")
                season_table = Table()
                season_table.add_column("月", style="cyan")
                season_table.add_column("言及回数", style="green")
                
                for month, count in temporal_data['seasonality'].items():
                    season_table.add_row(month, str(count))
                
                self.console.print(season_table)
    
    def _analyze_regional_patterns(self):
        """地域パターンの分析"""
        with sqlite3.connect(self.db_path) as conn:
            # 地域データの取得
            regional_data = self._get_regional_data(conn)
            
            # 分析結果の表示
            self.console.print("\n🗾 地域分析結果")
            
            # 都道府県別統計
            prefecture_table = Table(title="都道府県別統計")
            prefecture_table.add_column("都道府県", style="cyan")
            prefecture_table.add_column("地名数", style="green")
            prefecture_table.add_column("言及回数", style="yellow")
            prefecture_table.add_column("主要地名", style="blue")
            
            for prefecture, data in regional_data['prefectures'].items():
                prefecture_table.add_row(
                    prefecture,
                    str(data['place_count']),
                    str(data['mention_count']),
                    ", ".join(data['top_places'][:3])
                )
            
            self.console.print(prefecture_table)
            
            # 地域クラスターの表示
            if regional_data['clusters']:
                self.console.print("\n🔍 地域クラスター")
                cluster_table = Table()
                cluster_table.add_column("クラスター", style="cyan")
                cluster_table.add_column("中心地", style="green")
                cluster_table.add_column("関連地名", style="blue")
                
                for cluster in regional_data['clusters']:
                    cluster_table.add_row(
                        cluster['name'],
                        cluster['center'],
                        ", ".join(cluster['related_places'][:3])
                    )
                
                self.console.print(cluster_table)
    
    def _analyze_author_patterns(self):
        """作家パターンの分析"""
        with sqlite3.connect(self.db_path) as conn:
            # 作家データの取得
            author_data = self._get_author_data(conn)
            
            # 分析結果の表示
            self.console.print("\n👤 作家分析結果")
            
            # 作家別統計
            author_table = Table(title="作家別統計")
            author_table.add_column("作家", style="cyan")
            author_table.add_column("作品数", style="green")
            author_table.add_column("地名数", style="yellow")
            author_table.add_column("主要地名", style="blue")
            
            for author, data in author_data.items():
                author_table.add_row(
                    author,
                    str(data['work_count']),
                    str(data['place_count']),
                    ", ".join(data['top_places'][:3])
                )
            
            self.console.print(author_table)
            
            # 作家間の類似性
            if author_data['similarities']:
                self.console.print("\n🔄 作家間の類似性")
                similarity_table = Table()
                similarity_table.add_column("作家1", style="cyan")
                similarity_table.add_column("作家2", style="green")
                similarity_table.add_column("類似度", style="yellow")
                
                for sim in author_data['similarities']:
                    similarity_table.add_row(
                        sim['author1'],
                        sim['author2'],
                        f"{sim['similarity']:.2f}"
                    )
                
                self.console.print(similarity_table)
    
    def _analyze_work_patterns(self):
        """作品パターンの分析"""
        with sqlite3.connect(self.db_path) as conn:
            # 作品データの取得
            work_data = self._get_work_data(conn)
            
            # 分析結果の表示
            self.console.print("\n📚 作品分析結果")
            
            # 作品別統計
            work_table = Table(title="作品別統計")
            work_table.add_column("作品", style="cyan")
            work_table.add_column("作家", style="green")
            work_table.add_column("地名数", style="yellow")
            work_table.add_column("主要地名", style="blue")
            
            for work, data in work_data.items():
                work_table.add_row(
                    work,
                    data['author'],
                    str(data['place_count']),
                    ", ".join(data['top_places'][:3])
                )
            
            self.console.print(work_table)
            
            # 作品間の関連性
            if work_data['relationships']:
                self.console.print("\n🔗 作品間の関連性")
                relationship_table = Table()
                relationship_table.add_column("作品1", style="cyan")
                relationship_table.add_column("作品2", style="green")
                relationship_table.add_column("関連度", style="yellow")
                relationship_table.add_column("共通地名", style="blue")
                
                for rel in work_data['relationships']:
                    relationship_table.add_row(
                        rel['work1'],
                        rel['work2'],
                        f"{rel['relationship']:.2f}",
                        ", ".join(rel['common_places'][:3])
                    )
                
                self.console.print(relationship_table)
    
    def _run_custom_analysis(self):
        """カスタム分析の実行"""
        self.console.print("\n🔍 カスタム分析")
        
        # 分析タイプの選択
        analysis_type = Prompt.ask(
            "分析タイプを選択",
            choices=["時系列", "地域", "作家", "作品", "地名"]
        )
        
        # パラメータの設定
        params = {}
        if analysis_type == "時系列":
            params['start_date'] = Prompt.ask("開始日 (YYYY-MM-DD)")
            params['end_date'] = Prompt.ask("終了日 (YYYY-MM-DD)")
        elif analysis_type == "地域":
            params['prefecture'] = Prompt.ask("都道府県")
        elif analysis_type == "作家":
            params['author'] = Prompt.ask("作家名")
        elif analysis_type == "作品":
            params['work'] = Prompt.ask("作品名")
        elif analysis_type == "地名":
            params['place'] = Prompt.ask("地名")
        
        # 分析の実行
        with sqlite3.connect(self.db_path) as conn:
            results = self._execute_custom_analysis(conn, analysis_type, params)
            
            # 結果の表示
            self.console.print("\n📊 分析結果")
            self._display_custom_results(results)
    
    def _update_config(self):
        """設定の更新"""
        self.console.print("\n⚙️ 設定の更新")
        
        # 最小言及回数
        self.config.min_mentions = int(Prompt.ask(
            "最小言及回数",
            default=str(self.config.min_mentions)
        ))
        
        # 最大地名数
        self.config.max_places = int(Prompt.ask(
            "最大地名数",
            default=str(self.config.max_places)
        ))
        
        # 都道府県フィルター
        if Confirm.ask("都道府県でフィルターしますか？"):
            prefectures = Prompt.ask("都道府県（カンマ区切り）").split(",")
            self.config.prefecture_filter = [p.strip() for p in prefectures]
        
        # 地名タイプフィルター
        if Confirm.ask("地名タイプでフィルターしますか？"):
            types = Prompt.ask("地名タイプ（カンマ区切り）").split(",")
            self.config.place_type_filter = [t.strip() for t in types]
        
        self.console.print("✅ 設定を更新しました")
    
    def _get_basic_statistics(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """基本統計の取得"""
        stats = {}
        
        # 地名数
        cursor = conn.execute("SELECT COUNT(*) FROM places_master")
        stats['総地名数'] = cursor.fetchone()[0]
        
        # 言及回数
        cursor = conn.execute("SELECT COUNT(*) FROM sentence_places")
        stats['総言及回数'] = cursor.fetchone()[0]
        
        # 作家数
        cursor = conn.execute("SELECT COUNT(*) FROM authors")
        stats['作家数'] = cursor.fetchone()[0]
        
        # 作品数
        cursor = conn.execute("SELECT COUNT(*) FROM works")
        stats['作品数'] = cursor.fetchone()[0]
        
        return stats
    
    def _get_temporal_data(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """時系列データの取得"""
        data = {
            'trends': {},
            'seasonality': {}
        }
        
        # トレンド分析
        cursor = conn.execute("""
            SELECT 
                strftime('%Y-%m', created_at) as month,
                COUNT(*) as count
            FROM sentence_places
            GROUP BY month
            ORDER BY month
        """)
        
        monthly_data = cursor.fetchall()
        if monthly_data:
            # トレンドの計算
            months = [row[0] for row in monthly_data]
            counts = [row[1] for row in monthly_data]
            
            # 全体トレンド
            data['trends']['全体'] = {
                'direction': '上昇' if counts[-1] > counts[0] else '下降',
                'change_rate': ((counts[-1] - counts[0]) / counts[0] * 100)
            }
            
            # 季節性の計算
            for month, count in monthly_data:
                data['seasonality'][month] = count
        
        return data
    
    def _get_regional_data(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """地域データの取得"""
        data = {
            'prefectures': {},
            'clusters': []
        }
        
        # 都道府県別統計
        cursor = conn.execute("""
            SELECT 
                prefecture,
                COUNT(DISTINCT place_id) as place_count,
                COUNT(*) as mention_count
            FROM places_master
            GROUP BY prefecture
        """)
        
        for row in cursor.fetchall():
            prefecture = row[0]
            data['prefectures'][prefecture] = {
                'place_count': row[1],
                'mention_count': row[2],
                'top_places': self._get_top_places(conn, prefecture)
            }
        
        return data
    
    def _get_author_data(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """作家データの取得"""
        data = {}
        
        # 作家別統計
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
        
        for row in cursor.fetchall():
            author = row[0]
            data[author] = {
                'work_count': row[1],
                'place_count': row[2],
                'top_places': self._get_author_top_places(conn, author)
            }
        
        return data
    
    def _get_work_data(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """作品データの取得"""
        data = {}
        
        # 作品別統計
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
        
        for row in cursor.fetchall():
            work = row[0]
            data[work] = {
                'author': row[1],
                'place_count': row[2],
                'top_places': self._get_work_top_places(conn, work)
            }
        
        return data
    
    def _get_top_places(self, conn: sqlite3.Connection, prefecture: str) -> List[str]:
        """都道府県の主要地名を取得"""
        cursor = conn.execute("""
            SELECT place_name
            FROM places_master
            WHERE prefecture = ?
            ORDER BY mention_count DESC
            LIMIT 5
        """, (prefecture,))
        
        return [row[0] for row in cursor.fetchall()]
    
    def _get_author_top_places(self, conn: sqlite3.Connection, author: str) -> List[str]:
        """作家の主要地名を取得"""
        cursor = conn.execute("""
            SELECT pm.place_name
            FROM places_master pm
            JOIN sentence_places sp ON pm.place_id = sp.place_id
            JOIN sentences s ON sp.sentence_id = s.sentence_id
            JOIN works w ON s.work_id = w.work_id
            JOIN authors a ON w.author_id = a.author_id
            WHERE a.author_name = ?
            GROUP BY pm.place_id
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """, (author,))
        
        return [row[0] for row in cursor.fetchall()]
    
    def _get_work_top_places(self, conn: sqlite3.Connection, work: str) -> List[str]:
        """作品の主要地名を取得"""
        cursor = conn.execute("""
            SELECT pm.place_name
            FROM places_master pm
            JOIN sentence_places sp ON pm.place_id = sp.place_id
            JOIN sentences s ON sp.sentence_id = s.sentence_id
            JOIN works w ON s.work_id = w.work_id
            WHERE w.work_title = ?
            GROUP BY pm.place_id
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """, (work,))
        
        return [row[0] for row in cursor.fetchall()]
    
    def _execute_custom_analysis(self, conn: sqlite3.Connection,
                               analysis_type: str,
                               params: Dict[str, Any]) -> Dict[str, Any]:
        """カスタム分析の実行"""
        results = {}
        
        if analysis_type == "時系列":
            cursor = conn.execute("""
                SELECT 
                    strftime('%Y-%m', created_at) as month,
                    COUNT(*) as count
                FROM sentence_places
                WHERE created_at BETWEEN ? AND ?
                GROUP BY month
                ORDER BY month
            """, (params['start_date'], params['end_date']))
            
            results['data'] = cursor.fetchall()
            
        elif analysis_type == "地域":
            cursor = conn.execute("""
                SELECT 
                    place_name,
                    COUNT(*) as mention_count
                FROM places_master
                WHERE prefecture = ?
                GROUP BY place_id
                ORDER BY mention_count DESC
            """, (params['prefecture'],))
            
            results['data'] = cursor.fetchall()
            
        elif analysis_type == "作家":
            cursor = conn.execute("""
                SELECT 
                    pm.place_name,
                    COUNT(*) as mention_count
                FROM places_master pm
                JOIN sentence_places sp ON pm.place_id = sp.place_id
                JOIN sentences s ON sp.sentence_id = s.sentence_id
                JOIN works w ON s.work_id = w.work_id
                JOIN authors a ON w.author_id = a.author_id
                WHERE a.author_name = ?
                GROUP BY pm.place_id
                ORDER BY mention_count DESC
            """, (params['author'],))
            
            results['data'] = cursor.fetchall()
            
        elif analysis_type == "作品":
            cursor = conn.execute("""
                SELECT 
                    pm.place_name,
                    COUNT(*) as mention_count
                FROM places_master pm
                JOIN sentence_places sp ON pm.place_id = sp.place_id
                JOIN sentences s ON sp.sentence_id = s.sentence_id
                JOIN works w ON s.work_id = w.work_id
                WHERE w.work_title = ?
                GROUP BY pm.place_id
                ORDER BY mention_count DESC
            """, (params['work'],))
            
            results['data'] = cursor.fetchall()
            
        elif analysis_type == "地名":
            cursor = conn.execute("""
                SELECT 
                    w.work_title,
                    a.author_name,
                    COUNT(*) as mention_count
                FROM places_master pm
                JOIN sentence_places sp ON pm.place_id = sp.place_id
                JOIN sentences s ON sp.sentence_id = s.sentence_id
                JOIN works w ON s.work_id = w.work_id
                JOIN authors a ON w.author_id = a.author_id
                WHERE pm.place_name = ?
                GROUP BY w.work_id
                ORDER BY mention_count DESC
            """, (params['place'],))
            
            results['data'] = cursor.fetchall()
        
        return results
    
    def _display_custom_results(self, results: Dict[str, Any]):
        """カスタム分析結果の表示"""
        if not results.get('data'):
            self.console.print("❌ データが見つかりませんでした")
            return
        
        # テーブルの作成
        table = Table()
        
        # カラムの追加
        for col in results['data'][0].keys():
            table.add_column(col, style="cyan")
        
        # データの追加
        for row in results['data']:
            table.add_row(*[str(val) for val in row])
        
        self.console.print(table) 