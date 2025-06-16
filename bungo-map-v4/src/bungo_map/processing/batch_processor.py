#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
バッチ処理機能
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
from rich.table import Table
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
from pathlib import Path
import time

@dataclass
class BatchConfig:
    """バッチ処理設定"""
    batch_size: int = 1000
    max_workers: int = multiprocessing.cpu_count()
    timeout: int = 300
    retry_count: int = 3
    retry_delay: int = 5
    output_dir: str = "output"
    log_level: str = "INFO"

class BatchProcessor:
    """バッチ処理クラス"""
    
    def __init__(self, db_path: str, config: Optional[BatchConfig] = None):
        self.db_path = db_path
        self.config = config or BatchConfig()
        self.console = Console()
        self._init_database()
        self._setup_logging()
    
    def _init_database(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS batch_jobs (
                    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_type TEXT,
                    status TEXT,
                    parameters TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    result TEXT
                )
            """)
    
    def _setup_logging(self):
        """ロギングの設定"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{self.config.output_dir}/batch_processing.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def process_places(self, places: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        地名データのバッチ処理
        
        Args:
            places: 処理対象の地名データリスト
            
        Returns:
            処理結果
        """
        results = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'processed_places': []
        }
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("地名処理中...", total=len(places))
            
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = []
                
                # バッチに分割
                for i in range(0, len(places), self.config.batch_size):
                    batch = places[i:i + self.config.batch_size]
                    futures.append(
                        executor.submit(self._process_place_batch, batch)
                    )
                
                # 結果の収集
                for future in as_completed(futures):
                    try:
                        batch_result = future.result(timeout=self.config.timeout)
                        results['success'] += batch_result['success']
                        results['failed'] += batch_result['failed']
                        results['errors'].extend(batch_result['errors'])
                        results['processed_places'].extend(batch_result['processed_places'])
                        progress.update(task, advance=len(batch_result['processed_places']))
                    except Exception as e:
                        self.logger.error(f"バッチ処理エラー: {e}")
                        results['failed'] += self.config.batch_size
        
        return results
    
    def _process_place_batch(self, places: List[Dict[str, Any]]) -> Dict[str, Any]:
        """地名バッチの処理"""
        results = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'processed_places': []
        }
        
        for place in places:
            try:
                # リトライ処理
                for attempt in range(self.config.retry_count):
                    try:
                        processed_place = self._process_single_place(place)
                        results['success'] += 1
                        results['processed_places'].append(processed_place)
                        break
                    except Exception as e:
                        if attempt == self.config.retry_count - 1:
                            raise
                        time.sleep(self.config.retry_delay)
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'place': place,
                    'error': str(e)
                })
        
        return results
    
    def _process_single_place(self, place: Dict[str, Any]) -> Dict[str, Any]:
        """単一地名の処理"""
        with sqlite3.connect(self.db_path) as conn:
            # 地名の正規化
            normalized_name = self._normalize_place_name(place['place_name'])
            
            # 地理情報の取得
            geo_info = self._get_geo_info(normalized_name)
            
            # 関連地名の取得
            related_places = self._get_related_places(place['place_id'])
            
            # 処理結果の保存
            processed_place = {
                'place_id': place['place_id'],
                'place_name': place['place_name'],
                'normalized_name': normalized_name,
                'geo_info': geo_info,
                'related_places': related_places,
                'processed_at': datetime.now().isoformat()
            }
            
            self._save_processed_place(conn, processed_place)
            
            return processed_place
    
    def process_works(self, works: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        作品データのバッチ処理
        
        Args:
            works: 処理対象の作品データリスト
            
        Returns:
            処理結果
        """
        results = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'processed_works': []
        }
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("作品処理中...", total=len(works))
            
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = []
                
                # バッチに分割
                for i in range(0, len(works), self.config.batch_size):
                    batch = works[i:i + self.config.batch_size]
                    futures.append(
                        executor.submit(self._process_work_batch, batch)
                    )
                
                # 結果の収集
                for future in as_completed(futures):
                    try:
                        batch_result = future.result(timeout=self.config.timeout)
                        results['success'] += batch_result['success']
                        results['failed'] += batch_result['failed']
                        results['errors'].extend(batch_result['errors'])
                        results['processed_works'].extend(batch_result['processed_works'])
                        progress.update(task, advance=len(batch_result['processed_works']))
                    except Exception as e:
                        self.logger.error(f"バッチ処理エラー: {e}")
                        results['failed'] += self.config.batch_size
        
        return results
    
    def _process_work_batch(self, works: List[Dict[str, Any]]) -> Dict[str, Any]:
        """作品バッチの処理"""
        results = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'processed_works': []
        }
        
        for work in works:
            try:
                # リトライ処理
                for attempt in range(self.config.retry_count):
                    try:
                        processed_work = self._process_single_work(work)
                        results['success'] += 1
                        results['processed_works'].append(processed_work)
                        break
                    except Exception as e:
                        if attempt == self.config.retry_count - 1:
                            raise
                        time.sleep(self.config.retry_delay)
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'work': work,
                    'error': str(e)
                })
        
        return results
    
    def _process_single_work(self, work: Dict[str, Any]) -> Dict[str, Any]:
        """単一作品の処理"""
        with sqlite3.connect(self.db_path) as conn:
            # 作品の統計情報取得
            stats = self._get_work_statistics(conn, work['work_id'])
            
            # 地名の抽出
            places = self._extract_places_from_work(conn, work['work_id'])
            
            # 処理結果の保存
            processed_work = {
                'work_id': work['work_id'],
                'work_title': work['work_title'],
                'author_id': work['author_id'],
                'statistics': stats,
                'places': places,
                'processed_at': datetime.now().isoformat()
            }
            
            self._save_processed_work(conn, processed_work)
            
            return processed_work
    
    def _normalize_place_name(self, place_name: str) -> str:
        """地名の正規化"""
        # TODO: 正規化ロジックの実装
        return place_name
    
    def _get_geo_info(self, place_name: str) -> Dict[str, Any]:
        """地理情報の取得"""
        # TODO: 地理情報取得ロジックの実装
        return {}
    
    def _get_related_places(self, place_id: int) -> List[Dict[str, Any]]:
        """関連地名の取得"""
        # TODO: 関連地名取得ロジックの実装
        return []
    
    def _save_processed_place(self, conn: sqlite3.Connection, place: Dict[str, Any]):
        """処理済み地名の保存"""
        conn.execute("""
            INSERT INTO processed_places (
                place_id, place_name, normalized_name,
                geo_info, related_places, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            place['place_id'],
            place['place_name'],
            place['normalized_name'],
            json.dumps(place['geo_info']),
            json.dumps(place['related_places']),
            place['processed_at']
        ))
    
    def _get_work_statistics(self, conn: sqlite3.Connection, work_id: int) -> Dict[str, Any]:
        """作品の統計情報取得"""
        cursor = conn.execute("""
            SELECT 
                COUNT(DISTINCT s.sentence_id) as sentence_count,
                COUNT(DISTINCT sp.place_id) as place_count,
                COUNT(sp.id) as mention_count
            FROM sentences s
            LEFT JOIN sentence_places sp ON s.sentence_id = sp.sentence_id
            WHERE s.work_id = ?
        """, (work_id,))
        
        row = cursor.fetchone()
        return {
            'sentence_count': row[0],
            'place_count': row[1],
            'mention_count': row[2]
        }
    
    def _extract_places_from_work(self, conn: sqlite3.Connection, work_id: int) -> List[Dict[str, Any]]:
        """作品からの地名抽出"""
        cursor = conn.execute("""
            SELECT 
                pm.place_id,
                pm.place_name,
                COUNT(sp.id) as mention_count
            FROM places_master pm
            JOIN sentence_places sp ON pm.place_id = sp.place_id
            JOIN sentences s ON sp.sentence_id = s.sentence_id
            WHERE s.work_id = ?
            GROUP BY pm.place_id
        """, (work_id,))
        
        return [
            {
                'place_id': row[0],
                'place_name': row[1],
                'mention_count': row[2]
            }
            for row in cursor.fetchall()
        ]
    
    def _save_processed_work(self, conn: sqlite3.Connection, work: Dict[str, Any]):
        """処理済み作品の保存"""
        conn.execute("""
            INSERT INTO processed_works (
                work_id, work_title, author_id,
                statistics, places, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            work['work_id'],
            work['work_title'],
            work['author_id'],
            json.dumps(work['statistics']),
            json.dumps(work['places']),
            work['processed_at']
        ))
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """
        処理結果レポートの生成
        
        Args:
            results: 処理結果
            
        Returns:
            レポート文字列
        """
        report = []
        report.append("📊 バッチ処理レポート")
        report.append("=" * 40)
        
        report.append(f"\n処理結果:")
        report.append(f"- 成功: {results['success']:,}")
        report.append(f"- 失敗: {results['failed']:,}")
        
        if results['errors']:
            report.append("\nエラー一覧:")
            for error in results['errors'][:10]:  # 最初の10件のみ表示
                report.append(f"- {error['error']}")
            if len(results['errors']) > 10:
                report.append(f"... 他 {len(results['errors']) - 10} 件のエラー")
        
        return "\n".join(report) 