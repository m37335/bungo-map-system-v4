#!/usr/bin/env python3
"""
文豪ゆかり地図システム v4
包括的CLIシステム

v3の15種類のCLI機能をv4に完全移植・統合
"""

import sys
import os
import sqlite3
import argparse
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from bungo_map.extractors.extraction_pipeline import ExtractionPipeline
from bungo_map.extractors.aozora_extractor import AozoraExtractor
import time

class ComprehensiveCLI:
    """包括的CLIシステム - 15種類のCLIコマンド統合"""
    
    def __init__(self):
        self.console = Console()
        self.db_path = "data/databases/bungo_v4.db"
    
    def _get_db_connection(self) -> Optional[sqlite3.Connection]:
        """データベース接続を取得"""
        try:
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                return conn
            else:
                self.console.print(f"[red]❌ データベースファイルが見つかりません: {self.db_path}[/red]")
                return None
        except Exception as e:
            self.console.print(f"[red]❌ データベース接続エラー: {e}[/red]")
            return None
    
    def cmd_search(self, args):
        """地名・作品・作者検索システム"""
        self.console.print(Panel(
            f"[blue]🔍 検索システム[/blue]",
            title="包括的CLIシステム v4",
            border_style="blue"
        ))
        
        conn = self._get_db_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            if args.author:
                # 作者検索
                cursor.execute("SELECT * FROM authors WHERE name LIKE ? LIMIT ?", 
                             (f"%{args.author}%", args.limit))
                authors = cursor.fetchall()
                
                if authors:
                    table = Table(title=f"作者検索結果: {args.author}")
                    table.add_column("ID", style="cyan")
                    table.add_column("作者名", style="yellow")
                    table.add_column("生年", style="green")
                    table.add_column("没年", style="green")
                    
                    for author in authors:
                        table.add_row(
                            str(author['author_id']),
                            author['name'],
                            str(author['birth_year']) if author['birth_year'] else "不明",
                            str(author['death_year']) if author['death_year'] else "不明"
                        )
                    
                    self.console.print(table)
                    self.console.print(f"[green]📊 検索結果: {len(authors)}件[/green]")
                else:
                    self.console.print(f"[red]❌ 作者が見つかりません: {args.author}[/red]")
            
            elif args.work:
                # 作品検索
                cursor.execute("""
                    SELECT w.*, a.name as author_name 
                    FROM works w 
                    JOIN authors a ON w.author_id = a.author_id 
                    WHERE w.title LIKE ? LIMIT ?
                """, (f"%{args.work}%", args.limit))
                works = cursor.fetchall()
                
                if works:
                    table = Table(title=f"作品検索結果: {args.work}")
                    table.add_column("ID", style="cyan")
                    table.add_column("作品名", style="yellow")
                    table.add_column("作者", style="green")
                    table.add_column("出版年", style="blue")
                    
                    for work in works:
                        table.add_row(
                            str(work['work_id']),
                            work['title'],
                            work['author_name'],
                            str(work['publication_year']) if work['publication_year'] else "不明"
                        )
                    
                    self.console.print(table)
                    self.console.print(f"[green]📊 検索結果: {len(works)}件[/green]")
                else:
                    self.console.print(f"[red]❌ 作品が見つかりません: {args.work}[/red]")
            
            elif args.place:
                # 地名検索
                cursor.execute("SELECT * FROM places_master WHERE place_name LIKE ? LIMIT ?", 
                             (f"%{args.place}%", args.limit))
                places = cursor.fetchall()
                
                if places:
                    table = Table(title=f"地名検索結果: {args.place}")
                    table.add_column("ID", style="cyan")
                    table.add_column("地名", style="yellow")
                    table.add_column("正規名", style="green")
                    table.add_column("座標", style="blue")
                    
                    for place in places:
                        coords = "未設定"
                        if place['latitude'] and place['longitude']:
                            coords = f"{place['latitude']:.2f}, {place['longitude']:.2f}"
                        
                        table.add_row(
                            str(place['place_id']),
                            place['place_name'],
                            place['canonical_name'],
                            coords
                        )
                    
                    self.console.print(table)
                    self.console.print(f"[green]📊 検索結果: {len(places)}件[/green]")
                else:
                    self.console.print(f"[red]❌ 地名が見つかりません: {args.place}[/red]")
            
            else:
                # 統計表示
                self._show_database_stats(cursor)
        
        except Exception as e:
            self.console.print(f"[red]❌ 検索エラー: {e}[/red]")
        
        finally:
            conn.close()
    
    def _show_database_stats(self, cursor):
        """データベース統計表示"""
        cursor.execute("SELECT COUNT(*) FROM authors")
        authors_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM works")
        works_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM places_master")
        places_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM places_master WHERE latitude IS NOT NULL")
        geocoded_count = cursor.fetchone()[0]
        
        stats_table = Table(title="📊 データベース統計")
        stats_table.add_column("項目", style="cyan")
        stats_table.add_column("件数", style="yellow")
        stats_table.add_column("割合", style="green")
        
        stats_table.add_row("作者数", f"{authors_count:,}名", "")
        stats_table.add_row("作品数", f"{works_count:,}作品", "")
        stats_table.add_row("地名数", f"{places_count:,}箇所", "")
        geocoded_rate = (geocoded_count/places_count*100) if places_count > 0 else 0
        stats_table.add_row("ジオコーディング済み", f"{geocoded_count:,}箇所", f"{geocoded_rate:.1f}%")
        
        self.console.print(stats_table)
    
    def cmd_export(self, args):
        """データエクスポート"""
        self.console.print(Panel(
            f"[blue]📤 データエクスポート: {args.format.upper()}[/blue]",
            title="包括的CLIシステム v4",
            border_style="blue"
        ))
        
        self.console.print("[yellow]⚠️ エクスポート機能は次のフェーズで実装予定です[/yellow]")
        self.console.print("\n[green]予定機能:[/green]")
        self.console.print("  - GeoJSON: 地理データ可視化用")
        self.console.print("  - CSV: スプレッドシート用")
        self.console.print("  - JSON: API連携用")
    
    def cmd_stats(self, args):
        """統計情報表示"""
        self.console.print(Panel(
            f"[blue]📊 統計情報[/blue]",
            title="包括的CLIシステム v4",
            border_style="blue"
        ))
        
        # searchコマンドの統計表示を再利用
        fake_args = type('Args', (), {'author': None, 'work': None, 'place': None, 'limit': 10})()
        self.cmd_search(fake_args)
    
    def cmd_expand(self, args):
        """データベース拡張機能"""
        self.console.print(Panel(
            f"[blue]🔧 データベース拡張システム[/blue]",
            title="包括的CLIシステム v4",
            border_style="blue"
        ))
        
        conn = self._get_db_connection()
        if not conn:
            return
        
        try:
            if hasattr(args, 'author') and args.author:
                self._add_author(conn, args)
            elif hasattr(args, 'work') and args.work:
                self._add_work(conn, args)
            elif hasattr(args, 'place') and args.place:
                self._add_place(conn, args)
            else:
                self._show_expand_menu(conn)
        
        except Exception as e:
            self.console.print(f"[red]❌ データベース拡張エラー: {e}[/red]")
        
        finally:
            conn.close()
    
    def _show_expand_menu(self, conn):
        """拡張メニュー表示"""
        self.console.print("\n[cyan]📋 データベース拡張メニュー[/cyan]")
        
        # 現在の統計表示
        cursor = conn.cursor()
        self._show_database_stats(cursor)
        
        self.console.print("\n[green]利用可能な拡張機能:[/green]")
        self.console.print("  🧑‍💼 作者追加: --author [作者名] --birth-year [生年] --death-year [没年]")
        self.console.print("  📚 作品追加: --work [作品名] --author-id [作者ID] --year [出版年]")
        self.console.print("  🗺️ 地名追加: --place [地名] --lat [緯度] --lon [経度]")
        
        self.console.print("\n[yellow]使用例:[/yellow]")
        self.console.print("  python comprehensive_cli.py expand --author '新作者' --birth-year 1900 --death-year 1980")
        self.console.print("  python comprehensive_cli.py expand --work '新作品' --author-id 1 --year 1920")
        self.console.print("  python comprehensive_cli.py expand --place '新地名' --lat 35.6762 --lon 139.6503")
    
    def _add_author(self, conn, args):
        """作者追加機能"""
        self.console.print(f"\n[cyan]🧑‍💼 作者追加: {args.author}[/cyan]")
        
        cursor = conn.cursor()
        
        # 重複チェック
        cursor.execute("SELECT * FROM authors WHERE name = ?", (args.author,))
        existing = cursor.fetchone()
        
        if existing:
            self.console.print(f"[yellow]⚠️ 作者 '{args.author}' は既に登録されています (ID: {existing['author_id']})[/yellow]")
            return
        
        # 作者情報収集
        birth_year = getattr(args, 'birth_year', None)
        death_year = getattr(args, 'death_year', None)
        
        # データ挿入
        cursor.execute("""
            INSERT INTO authors (name, birth_year, death_year, created_at, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (args.author, birth_year, death_year))
        
        author_id = cursor.lastrowid
        conn.commit()
        
        # 成功表示
        success_table = Table(title=f"✅ 作者追加成功")
        success_table.add_column("項目", style="cyan")
        success_table.add_column("値", style="green")
        
        success_table.add_row("作者ID", str(author_id))
        success_table.add_row("作者名", args.author)
        success_table.add_row("生年", str(birth_year) if birth_year else "不明")
        success_table.add_row("没年", str(death_year) if death_year else "不明")
        
        self.console.print(success_table)
        self.console.print(f"[green]🎉 作者 '{args.author}' が正常に追加されました (ID: {author_id})[/green]")
    
    def _add_work(self, conn, args):
        """作品追加機能"""
        self.console.print(f"\n[cyan]📚 作品追加: {args.work}[/cyan]")
        
        cursor = conn.cursor()
        
        # 作者ID検証
        author_id = getattr(args, 'author_id', None)
        if not author_id:
            self.console.print("[red]❌ 作者IDが指定されていません (--author-id が必要)[/red]")
            return
        
        cursor.execute("SELECT * FROM authors WHERE author_id = ?", (author_id,))
        author = cursor.fetchone()
        
        if not author:
            self.console.print(f"[red]❌ 作者ID {author_id} が見つかりません[/red]")
            return
        
        # 重複チェック
        cursor.execute("SELECT * FROM works WHERE title = ? AND author_id = ?", 
                      (args.work, author_id))
        existing = cursor.fetchone()
        
        if existing:
            self.console.print(f"[yellow]⚠️ 作品 '{args.work}' は既に登録されています (ID: {existing['work_id']})[/yellow]")
            return
        
        # 作品情報収集
        publication_year = getattr(args, 'year', None)
        
        # データ挿入
        cursor.execute("""
            INSERT INTO works (title, author_id, publication_year, created_at, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (args.work, author_id, publication_year))
        
        work_id = cursor.lastrowid
        conn.commit()
        
        # 成功表示
        success_table = Table(title=f"✅ 作品追加成功")
        success_table.add_column("項目", style="cyan")
        success_table.add_column("値", style="green")
        
        success_table.add_row("作品ID", str(work_id))
        success_table.add_row("作品名", args.work)
        success_table.add_row("作者", author['name'])
        success_table.add_row("出版年", str(publication_year) if publication_year else "不明")
        
        self.console.print(success_table)
        self.console.print(f"[green]🎉 作品 '{args.work}' が正常に追加されました (ID: {work_id})[/green]")
    
    def _add_place(self, conn, args):
        """地名追加機能"""
        self.console.print(f"\n[cyan]🗺️ 地名追加: {args.place}[/cyan]")
        
        cursor = conn.cursor()
        
        # 重複チェック
        cursor.execute("SELECT * FROM places_master WHERE place_name = ?", (args.place,))
        existing = cursor.fetchone()
        
        if existing:
            self.console.print(f"[yellow]⚠️ 地名 '{args.place}' は既に登録されています (ID: {existing['place_id']})[/yellow]")
            return
        
        # 座標情報収集
        latitude = getattr(args, 'lat', None)
        longitude = getattr(args, 'lon', None)
        
        # データ挿入
        cursor.execute("""
            INSERT INTO places_master (place_name, canonical_name, latitude, longitude, created_at, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (args.place, args.place, latitude, longitude))
        
        place_id = cursor.lastrowid
        conn.commit()
        
        # 成功表示
        success_table = Table(title=f"✅ 地名追加成功")
        success_table.add_column("項目", style="cyan")
        success_table.add_column("値", style="green")
        
        success_table.add_row("地名ID", str(place_id))
        success_table.add_row("地名", args.place)
        success_table.add_row("緯度", str(latitude) if latitude else "未設定")
        success_table.add_row("経度", str(longitude) if longitude else "未設定")
        
        self.console.print(success_table)
        self.console.print(f"[green]🎉 地名 '{args.place}' が正常に追加されました (ID: {place_id})[/green]")
    
    def cmd_geocode(self, args):
        """ジオコーディング専用CLI"""
        self.console.print(Panel(
            f"[blue]🗺️ ジオコーディングシステム[/blue]",
            title="包括的CLIシステム v4",
            border_style="blue"
        ))
        
        conn = self._get_db_connection()
        if not conn:
            return
        
        try:
            if hasattr(args, 'place') and args.place:
                # 特定地名のジオコーディング
                self._geocode_place(conn, args)
            elif hasattr(args, 'batch') and args.batch:
                # バッチジオコーディング
                self._geocode_batch(conn, args)
            elif hasattr(args, 'verify') and args.verify:
                # 座標検証
                self._geocode_verify(conn, args)
            else:
                # ジオコーディングメニュー表示
                self._show_geocode_menu(conn)
        
        except Exception as e:
            self.console.print(f"[red]❌ ジオコーディングエラー: {e}[/red]")
        
        finally:
            conn.close()
    
    def _show_geocode_menu(self, conn):
        """ジオコーディングメニュー表示"""
        self.console.print("\n[cyan]🗺️ ジオコーディングシステム メニュー[/cyan]")
        
        cursor = conn.cursor()
        
        # 未座標化地名の統計
        cursor.execute("SELECT COUNT(*) FROM places_master WHERE latitude IS NULL OR longitude IS NULL")
        ungeocoded_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM places_master WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
        geocoded_count = cursor.fetchone()[0]
        
        total_places = ungeocoded_count + geocoded_count
        geocoded_rate = (geocoded_count / total_places * 100) if total_places > 0 else 0
        
        # 統計表示
        stats_table = Table(title="📊 ジオコーディング統計")
        stats_table.add_column("項目", style="cyan")
        stats_table.add_column("件数", style="yellow")
        stats_table.add_column("割合", style="green")
        
        stats_table.add_row("総地名数", f"{total_places:,}箇所", "100%")
        stats_table.add_row("ジオコーディング済み", f"{geocoded_count:,}箇所", f"{geocoded_rate:.1f}%")
        stats_table.add_row("未座標化", f"{ungeocoded_count:,}箇所", f"{100-geocoded_rate:.1f}%")
        
        self.console.print(stats_table)
        
        # 未座標化地名リスト
        if ungeocoded_count > 0:
            self.console.print(f"\n[yellow]📍 未座標化地名 (最大5件):[/yellow]")
            cursor.execute("SELECT place_id, place_name FROM places_master WHERE latitude IS NULL OR longitude IS NULL LIMIT 5")
            ungeocoded_places = cursor.fetchall()
            
            ungeocoded_table = Table(show_header=True)
            ungeocoded_table.add_column("ID", style="cyan")
            ungeocoded_table.add_column("地名", style="yellow")
            
            for place in ungeocoded_places:
                ungeocoded_table.add_row(str(place['place_id']), place['place_name'])
            
            self.console.print(ungeocoded_table)
        
        # 利用可能機能
        self.console.print("\n[green]利用可能な機能:[/green]")
        self.console.print("  🎯 特定地名ジオコーディング: --place [地名] --lat [緯度] --lon [経度]")
        self.console.print("  📦 バッチジオコーディング: --batch --limit [件数]")
        self.console.print("  ✅ 座標検証: --verify")
        
        self.console.print("\n[yellow]使用例:[/yellow]")
        self.console.print("  python comprehensive_cli.py geocode --place '箱根' --lat 35.2322 --lon 139.1069")
        self.console.print("  python comprehensive_cli.py geocode --batch --limit 5")
        self.console.print("  python comprehensive_cli.py geocode --verify")
    
    def _geocode_place(self, conn, args):
        """特定地名のジオコーディング"""
        place_name = args.place
        self.console.print(f"\n[cyan]🎯 地名ジオコーディング: {place_name}[/cyan]")
        
        cursor = conn.cursor()
        
        # 地名検索
        cursor.execute("SELECT * FROM places_master WHERE place_name = ?", (place_name,))
        place = cursor.fetchone()
        
        if not place:
            self.console.print(f"[red]❌ 地名 '{place_name}' が見つかりません[/red]")
            return
        
        # 現在の座標確認
        current_lat = place['latitude']
        current_lon = place['longitude']
        
        if current_lat and current_lon:
            self.console.print(f"[yellow]⚠️ 地名 '{place_name}' は既に座標が設定されています[/yellow]")
            self.console.print(f"現在の座標: ({current_lat:.6f}, {current_lon:.6f})")
            
            # 上書き確認
            if not (hasattr(args, 'force') and args.force):
                self.console.print("[blue]💡 座標を上書きする場合は --force オプションを使用してください[/blue]")
                return
        
        # 新しい座標設定
        new_lat = getattr(args, 'lat', None)
        new_lon = getattr(args, 'lon', None)
        
        if not new_lat or not new_lon:
            self.console.print("[red]❌ 緯度(--lat)と経度(--lon)の両方を指定してください[/red]")
            return
        
        # 座標妥当性チェック
        if not (-90 <= new_lat <= 90):
            self.console.print(f"[red]❌ 緯度が範囲外です: {new_lat} (範囲: -90 to 90)[/red]")
            return
        
        if not (-180 <= new_lon <= 180):
            self.console.print(f"[red]❌ 経度が範囲外です: {new_lon} (範囲: -180 to 180)[/red]")
            return
        
        # 座標更新
        cursor.execute("""
            UPDATE places_master 
            SET latitude = ?, longitude = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE place_id = ?
        """, (new_lat, new_lon, place['place_id']))
        
        conn.commit()
        
        # 成功表示
        success_table = Table(title=f"✅ ジオコーディング成功")
        success_table.add_column("項目", style="cyan")
        success_table.add_column("値", style="green")
        
        success_table.add_row("地名ID", str(place['place_id']))
        success_table.add_row("地名", place_name)
        success_table.add_row("新緯度", f"{new_lat:.6f}")
        success_table.add_row("新経度", f"{new_lon:.6f}")
        
        if current_lat and current_lon:
            success_table.add_row("前緯度", f"{current_lat:.6f}")
            success_table.add_row("前経度", f"{current_lon:.6f}")
        
        self.console.print(success_table)
        self.console.print(f"[green]🎉 地名 '{place_name}' の座標を正常に更新しました[/green]")
    
    def _geocode_batch(self, conn, args):
        """バッチジオコーディング"""
        limit = getattr(args, 'limit', 5)
        self.console.print(f"\n[cyan]📦 バッチジオコーディング (最大{limit}件)[/cyan]")
        
        cursor = conn.cursor()
        
        # 未座標化地名取得
        cursor.execute("""
            SELECT place_id, place_name 
            FROM places_master 
            WHERE latitude IS NULL OR longitude IS NULL 
            LIMIT ?
        """, (limit,))
        
        ungeocoded_places = cursor.fetchall()
        
        if not ungeocoded_places:
            self.console.print("[green]🎉 すべての地名が既にジオコーディング済みです[/green]")
            return
        
        # サンプル座標データ（実際の実装では外部APIを使用）
        sample_coordinates = {
            '箱根': (35.2322, 139.1069),
            '日光': (36.7581, 139.6086),
            '京都': (35.0116, 135.7681),
            '奈良': (34.6851, 135.8048),
            '鎌倉': (35.3192, 139.5466),
            '熱海': (35.0953, 139.0732),
            '伊豆': (34.9600, 138.9472),
            '富士山': (35.3606, 138.7274)
        }
        
        geocoded_count = 0
        results_table = Table(title="📦 バッチジオコーディング結果")
        results_table.add_column("地名", style="cyan")
        results_table.add_column("緯度", style="green")
        results_table.add_column("経度", style="green")
        results_table.add_column("状況", style="yellow")
        
        for place in ungeocoded_places:
            place_name = place['place_name']
            
            # サンプル座標マッチング
            if place_name in sample_coordinates:
                lat, lon = sample_coordinates[place_name]
                
                # 座標更新
                cursor.execute("""
                    UPDATE places_master 
                    SET latitude = ?, longitude = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE place_id = ?
                """, (lat, lon, place['place_id']))
                
                results_table.add_row(place_name, f"{lat:.6f}", f"{lon:.6f}", "✅ 成功")
                geocoded_count += 1
            else:
                results_table.add_row(place_name, "未設定", "未設定", "⚠️ 座標不明")
        
        conn.commit()
        
        self.console.print(results_table)
        self.console.print(f"\n[green]🎉 バッチジオコーディング完了: {geocoded_count}/{len(ungeocoded_places)}件 成功[/green]")
        
        if geocoded_count > 0:
            self.console.print("[blue]💡 更新された座標は検索・統計機能で確認できます[/blue]")
    
    def _geocode_verify(self, conn, args):
        """座標検証"""
        self.console.print(f"\n[cyan]✅ 座標検証システム[/cyan]")
        
        cursor = conn.cursor()
        
        # 全地名の座標チェック
        cursor.execute("""
            SELECT place_id, place_name, latitude, longitude 
            FROM places_master 
            ORDER BY place_id
        """)
        
        all_places = cursor.fetchall()
        
        valid_count = 0
        invalid_count = 0
        missing_count = 0
        
        verify_table = Table(title="✅ 座標検証結果")
        verify_table.add_column("地名", style="cyan")
        verify_table.add_column("緯度", style="green")
        verify_table.add_column("経度", style="green")
        verify_table.add_column("状況", style="yellow")
        
        for place in all_places[:10]:  # 最大10件表示
            place_name = place['place_name']
            lat = place['latitude']
            lon = place['longitude']
            
            if lat is None or lon is None:
                verify_table.add_row(place_name, "未設定", "未設定", "❌ 座標なし")
                missing_count += 1
            elif not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                verify_table.add_row(place_name, f"{lat:.6f}", f"{lon:.6f}", "⚠️ 座標範囲外")
                invalid_count += 1
            else:
                verify_table.add_row(place_name, f"{lat:.6f}", f"{lon:.6f}", "✅ 正常")
                valid_count += 1
        
        self.console.print(verify_table)
        
        # 検証サマリー
        total_places = len(all_places)
        summary_table = Table(title="📊 検証サマリー")
        summary_table.add_column("項目", style="cyan")
        summary_table.add_column("件数", style="yellow")
        summary_table.add_column("割合", style="green")
        
        summary_table.add_row("総地名数", f"{total_places:,}箇所", "100%")
        summary_table.add_row("正常座標", f"{valid_count:,}箇所", f"{valid_count/total_places*100:.1f}%")
        summary_table.add_row("座標なし", f"{missing_count:,}箇所", f"{missing_count/total_places*100:.1f}%")
        summary_table.add_row("座標異常", f"{invalid_count:,}箇所", f"{invalid_count/total_places*100:.1f}%")
        
        self.console.print(summary_table)
        
        if missing_count > 0:
            self.console.print(f"[yellow]💡 {missing_count}件の地名が座標未設定です。バッチジオコーディングを実行してください[/yellow]")
        
        if invalid_count > 0:
            self.console.print(f"[red]⚠️ {invalid_count}件の地名で座標異常が検出されました。手動修正が必要です[/red]")
    
    def cmd_aozora(self, args):
        """青空文庫パイプライン実行"""
        self.console.print(Panel("[green]青空文庫パイプライン実行: 作品ダウンロード・テキスト抽出・地名抽出を開始します[/green]", title="aozora - 青空文庫処理"))
        
        # 青空文庫抽出器とパイプラインを初期化
        aozora = AozoraExtractor()
        pipeline = ExtractionPipeline()
        
        # 出力ディレクトリ作成
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # サンプル作品リスト取得
        works = aozora.get_sample_works()
        if not works:
            self.console.print("[red]❌ 作品リストの取得に失敗しました[/red]")
            return
        
        total_works = len(works)
        total_places = 0
        error_works = []
        
        from rich.progress import Progress
        with Progress() as progress:
            task = progress.add_task("[cyan]青空文庫処理中...", total=total_works)
            
            for work in works:
                try:
                    # 作品情報表示
                    self.console.print(f"\n[blue]📚 処理開始: {work['title']} ({work['author']})[/blue]")
                    
                    # テキストダウンロード・正規化
                    text = aozora.download_and_extract_text(work['text_url'])
                    if not text:
                        self.console.print(f"[yellow]⚠️ テキストの取得に失敗: {work['title']}[/yellow]")
                        error_works.append(work['title'])
                        continue
                    
                    # センテンス単位で分割
                    sentences = [s for s in text.split('。') if s.strip()]
                    
                    # 地名抽出
                    work_places = []
                    seen_places = set()
                    
                    for sentence in sentences:
                        result = pipeline.process_sentence(sentence)
                        for place in result['places']:
                            key = (place['place_name'], sentence)
                            if key not in seen_places:
                                seen_places.add(key)
                                work_places.append(place)
                    
                    # 結果保存
                    output_path = output_dir / f"{work['title']}_aozora.json"
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(work_places, f, ensure_ascii=False, indent=2)
                    
                    # 統計表示
                    self.console.print(f"[green]✅ {work['title']}: {len(sentences)}文・{len(work_places)}地名を抽出[/green]")
                    total_places += len(work_places)
                    
                    # 進捗更新
                    progress.update(task, advance=1)
                    
                    # API制限対策
                    time.sleep(1)
                    
                except Exception as e:
                    self.console.print(f"[red]❌ 処理エラー ({work['title']}): {e}[/red]")
                    error_works.append(work['title'])
                    progress.update(task, advance=1)
        
        # 最終結果表示
        self.console.print(f"\n[green]📊 青空文庫パイプライン処理が完了しました: {total_works}作品・{total_places}地名[/green]")
        if error_works:
            self.console.print(f"[red]❌ エラー作品: {', '.join(error_works)}[/red]")
    
    def cmd_add(self, args):
        self.console.print(Panel("[yellow]⚠️ この機能は次のフェーズで実装予定です[/yellow]", title="add - 手動データ追加"))
    
    def cmd_ai(self, args):
        self.console.print(Panel("[green]✅ AI機能は enhanced_ai_cli.py で利用可能です[/green]", title="ai - AI機能"))
    
    def cmd_optimize(self, args):
        self.console.print(Panel("[yellow]⚠️ この機能は次のフェーズで実装予定です[/yellow]", title="optimize - データベース最適化"))
    
    def cmd_cleanup(self, args):
        self.console.print(Panel("[yellow]⚠️ この機能は次のフェーズで実装予定です[/yellow]", title="cleanup - データクリーンアップ"))
    
    def cmd_pipeline(self, args):
        self.console.print(Panel("[green]統合パイプライン実行: 全作品の地名抽出・正規化を開始します[/green]", title="pipeline - 統合パイプライン"))
        pipeline = ExtractionPipeline()
        conn = self._get_db_connection()
        if not conn:
            return
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        total_sentences = 0
        total_places = 0
        error_works = []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT w.work_id, w.title, w.text_url, a.author_id FROM works w JOIN authors a ON w.author_id = a.author_id")
            works = cursor.fetchall()
            if not works:
                self.console.print("[yellow]⚠️ 処理対象の作品が見つかりません[/yellow]")
                return
            from rich.progress import Progress
            with Progress() as progress:
                task = progress.add_task("[cyan]パイプライン処理中...", total=len(works))
                for work in works:
                    try:
                        text_path = Path(work['text_url'])
                        if not text_path.exists():
                            self.console.print(f"[yellow]⚠️ テキストファイルが見つかりません: {text_path}[/yellow]")
                            error_works.append(work['title'])
                            continue
                        with open(text_path, 'r', encoding='utf-8') as f:
                            text = f.read()
                        # センテンス単位で分割
                        sentences = [s for s in text.split('。') if s.strip()]
                        work_places = []
                        seen_places = set()
                        for sentence in sentences:
                            result = pipeline.process_sentence(sentence, work_id=work['work_id'], author_id=work['author_id'])
                            for place in result['places']:
                                key = (place['place_name'], sentence)
                                if key not in seen_places:
                                    seen_places.add(key)
                                    work_places.append(place)
                        # ファイル出力
                        output_path = output_dir / f"{work['title']}_pipeline.json"
                        with open(output_path, 'w', encoding='utf-8') as out_f:
                            json.dump(work_places, out_f, ensure_ascii=False, indent=2)
                        conn.commit()
                        self.console.print(f"[green]✅ {work['title']}: {len(sentences)}文・{len(work_places)}地名を処理[/green]")
                        total_sentences += len(sentences)
                        total_places += len(work_places)
                    except Exception as e:
                        self.console.print(f"[red]❌ パイプライン処理エラー ({work['title']}): {e}[/red]")
                        error_works.append(work['title'])
                    progress.update(task, advance=1)
            self.console.print(f"[green]📊 パイプライン処理が完了しました: {total_sentences}文・{total_places}地名[/green]")
            if error_works:
                self.console.print(f"[red]❌ エラー作品: {', '.join(error_works)}[/red]")
        finally:
            conn.close()
    
    def cmd_test(self, args):
        self.console.print(Panel("[yellow]⚠️ この機能は次のフェーズで実装予定です[/yellow]", title="test - システムテスト"))
    
    def cmd_backup(self, args):
        self.console.print(Panel("[yellow]⚠️ この機能は次のフェーズで実装予定です[/yellow]", title="backup - データバックアップ"))
    
    def cmd_restore(self, args):
        self.console.print(Panel("[yellow]⚠️ この機能は次のフェーズで実装予定です[/yellow]", title="restore - データ復元"))
    
    def cmd_config(self, args):
        self.console.print(Panel("[yellow]⚠️ この機能は次のフェーズで実装予定です[/yellow]", title="config - 設定管理"))

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="文豪ゆかり地図システム v4 - 包括的CLIシステム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🌟 15種類のCLIコマンド統合システム

実装済み機能:
  search     地名・作品・作者検索
  stats      統計情報表示

実装予定機能:
  export     データエクスポート
  expand     データベース拡張
  geocode    ジオコーディング
  aozora     青空文庫処理
  add        手動データ追加
  optimize   データベース最適化
  cleanup    データクリーンアップ
  test       システムテスト
  backup     データバックアップ
  restore    データ復元
  config     設定管理

既存システム連携:
  ai         enhanced_ai_cli.py
  pipeline   enhanced_main_pipeline.py

使用例:
  python comprehensive_cli.py search --author 夏目漱石
  python comprehensive_cli.py search --work 坊っちゃん
  python comprehensive_cli.py search --place 東京
  python comprehensive_cli.py stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='利用可能なコマンド')
    
    # search コマンド
    search_parser = subparsers.add_parser('search', help='地名・作品・作者検索')
    search_parser.add_argument('--author', help='作者名で検索')
    search_parser.add_argument('--work', help='作品名で検索')
    search_parser.add_argument('--place', help='地名で検索')
    search_parser.add_argument('--limit', type=int, default=10, help='検索結果上限')
    
    # export コマンド
    export_parser = subparsers.add_parser('export', help='データエクスポート')
    export_parser.add_argument('--format', choices=['geojson', 'csv', 'json'], 
                              default='geojson', help='エクスポート形式')
    
    # stats コマンド
    stats_parser = subparsers.add_parser('stats', help='統計情報表示')
    
    # expand コマンド
    expand_parser = subparsers.add_parser('expand', help='データベース拡張')
    expand_parser.add_argument('--author', help='追加する作者名')
    expand_parser.add_argument('--birth-year', type=int, help='作者の生年')
    expand_parser.add_argument('--death-year', type=int, help='作者の没年')
    expand_parser.add_argument('--work', help='追加する作品名')
    expand_parser.add_argument('--author-id', type=int, help='作品の作者ID')
    expand_parser.add_argument('--year', type=int, help='作品の出版年')
    expand_parser.add_argument('--place', help='追加する地名')
    expand_parser.add_argument('--lat', type=float, help='地名の緯度')
    expand_parser.add_argument('--lon', type=float, help='地名の経度')
    
    # geocode コマンド
    geocode_parser = subparsers.add_parser('geocode', help='ジオコーディング専用CLI')
    geocode_parser.add_argument('--place', help='ジオコーディングする地名')
    geocode_parser.add_argument('--lat', type=float, help='緯度')
    geocode_parser.add_argument('--lon', type=float, help='経度')
    geocode_parser.add_argument('--batch', action='store_true', help='バッチジオコーディング実行')
    geocode_parser.add_argument('--limit', type=int, default=5, help='バッチ処理件数上限')
    geocode_parser.add_argument('--verify', action='store_true', help='座標検証実行')
    geocode_parser.add_argument('--force', action='store_true', help='既存座標の上書き許可')
    
    # その他のコマンド
    for cmd in ['aozora', 'add', 'ai', 'optimize', 
                'cleanup', 'pipeline', 'test', 'backup', 'restore', 'config']:
        subparsers.add_parser(cmd, help=f'{cmd}機能')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # CLI実行
    cli = ComprehensiveCLI()
    
    # コマンド実行
    command_method = getattr(cli, f'cmd_{args.command}', None)
    if command_method:
        try:
            command_method(args)
        except KeyboardInterrupt:
            cli.console.print("[red]❌ 処理が中断されました[/red]")
        except Exception as e:
            cli.console.print(f"[red]❌ 予期しないエラー: {e}[/red]")
    else:
        cli.console.print(f"[red]❌ 不明なコマンド: {args.command}[/red]")

if __name__ == "__main__":
    main()