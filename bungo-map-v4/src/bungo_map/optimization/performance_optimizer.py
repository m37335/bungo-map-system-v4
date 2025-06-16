#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
パフォーマンス最適化機能
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
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import queue
import gc

@dataclass
class OptimizationConfig:
    """最適化設定"""
    max_workers: int = 4
    batch_size: int = 1000
    cache_size: int = 10000
    page_size: int = 4096
    journal_mode: str = "WAL"
    synchronous: int = 1
    temp_store: int = 2
    mmap_size: int = 30000000000
    optimize_indexes: bool = True
    vacuum: bool = True
    analyze: bool = True

class PerformanceOptimizer:
    """パフォーマンス最適化クラス"""
    
    def __init__(self, db_path: str, config: Optional[OptimizationConfig] = None):
        self.db_path = db_path
        self.config = config or OptimizationConfig()
        self.console = Console()
        self._setup_logging()
        self._init_database()
    
    def _setup_logging(self):
        """ロギングの設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _init_database(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            # パフォーマンス設定の適用
            conn.execute(f"PRAGMA cache_size = {self.config.cache_size}")
            conn.execute(f"PRAGMA page_size = {self.config.page_size}")
            conn.execute(f"PRAGMA journal_mode = {self.config.journal_mode}")
            conn.execute(f"PRAGMA synchronous = {self.config.synchronous}")
            conn.execute(f"PRAGMA temp_store = {self.config.temp_store}")
            conn.execute(f"PRAGMA mmap_size = {self.config.mmap_size}")
    
    def optimize_database(self) -> Dict[str, Any]:
        """
        データベースの最適化
        
        Returns:
            最適化結果の辞書
        """
        results = {}
        
        with sqlite3.connect(self.db_path) as conn:
            # インデックスの最適化
            if self.config.optimize_indexes:
                start_time = time.time()
                self._optimize_indexes(conn)
                results['index_optimization_time'] = time.time() - start_time
            
            # VACUUMの実行
            if self.config.vacuum:
                start_time = time.time()
                conn.execute("VACUUM")
                results['vacuum_time'] = time.time() - start_time
            
            # ANALYZEの実行
            if self.config.analyze:
                start_time = time.time()
                conn.execute("ANALYZE")
                results['analyze_time'] = time.time() - start_time
            
            # 統計情報の取得
            results['database_size'] = self._get_database_size()
            results['table_stats'] = self._get_table_statistics(conn)
            results['index_stats'] = self._get_index_statistics(conn)
        
        return results
    
    def _optimize_indexes(self, conn: sqlite3.Connection):
        """インデックスの最適化"""
        # 既存のインデックスを取得
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        # インデックスの再構築
        for index in indexes:
            try:
                conn.execute(f"REINDEX {index}")
            except sqlite3.Error as e:
                self.logger.error(f"インデックス再構築エラー ({index}): {e}")
    
    def _get_database_size(self) -> int:
        """データベースサイズの取得"""
        return Path(self.db_path).stat().st_size
    
    def _get_table_statistics(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """テーブル統計情報の取得"""
        stats = {}
        
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            try:
                # レコード数
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                # テーブルサイズ
                cursor = conn.execute(f"SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size() WHERE name = '{table}'")
                table_size = cursor.fetchone()[0]
                
                stats[table] = {
                    'row_count': row_count,
                    'size_bytes': table_size
                }
            except sqlite3.Error as e:
                self.logger.error(f"テーブル統計取得エラー ({table}): {e}")
        
        return stats
    
    def _get_index_statistics(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """インデックス統計情報の取得"""
        stats = {}
        
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        for index in indexes:
            try:
                # インデックスサイズ
                cursor = conn.execute(f"SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size() WHERE name = '{index}'")
                index_size = cursor.fetchone()[0]
                
                stats[index] = {
                    'size_bytes': index_size
                }
            except sqlite3.Error as e:
                self.logger.error(f"インデックス統計取得エラー ({index}): {e}")
        
        return stats
    
    def optimize_query(self, query: str, params: Optional[Tuple] = None) -> Dict[str, Any]:
        """
        クエリの最適化
        
        Args:
            query: 最適化するクエリ
            params: クエリパラメータ
            
        Returns:
            最適化結果の辞書
        """
        results = {}
        
        with sqlite3.connect(self.db_path) as conn:
            # EXPLAIN QUERY PLANの実行
            if params:
                cursor = conn.execute(f"EXPLAIN QUERY PLAN {query}", params)
            else:
                cursor = conn.execute(f"EXPLAIN QUERY PLAN {query}")
            
            plan = cursor.fetchall()
            results['query_plan'] = plan
            
            # 実行時間の計測
            start_time = time.time()
            if params:
                cursor = conn.execute(query, params)
            else:
                cursor = conn.execute(query)
            results['execution_time'] = time.time() - start_time
            
            # メモリ使用量の計測
            process = psutil.Process()
            results['memory_usage'] = process.memory_info().rss
        
        return results
    
    def optimize_batch_processing(self, items: List[Any],
                                process_func: callable,
                                batch_size: Optional[int] = None) -> Dict[str, Any]:
        """
        バッチ処理の最適化
        
        Args:
            items: 処理対象のアイテムリスト
            process_func: 処理関数
            batch_size: バッチサイズ
            
        Returns:
            最適化結果の辞書
        """
        results = {
            'total_items': len(items),
            'batch_size': batch_size or self.config.batch_size,
            'start_time': time.time()
        }
        
        # バッチサイズの最適化
        if not batch_size:
            batch_size = self._optimize_batch_size(items, process_func)
            results['optimized_batch_size'] = batch_size
        
        # マルチスレッド処理
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = []
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                futures.append(executor.submit(process_func, batch))
            
            # 結果の収集
            results['processed_items'] = 0
            for future in futures:
                try:
                    result = future.result()
                    results['processed_items'] += len(result)
                except Exception as e:
                    self.logger.error(f"バッチ処理エラー: {e}")
        
        results['end_time'] = time.time()
        results['total_time'] = results['end_time'] - results['start_time']
        
        return results
    
    def _optimize_batch_size(self, items: List[Any],
                           process_func: callable) -> int:
        """
        バッチサイズの最適化
        
        Args:
            items: 処理対象のアイテムリスト
            process_func: 処理関数
            
        Returns:
            最適化されたバッチサイズ
        """
        # テスト用のバッチサイズ
        test_sizes = [100, 500, 1000, 2000, 5000]
        results = []
        
        for size in test_sizes:
            start_time = time.time()
            try:
                process_func(items[:size])
                execution_time = time.time() - start_time
                results.append((size, execution_time))
            except Exception as e:
                self.logger.error(f"バッチサイズテストエラー ({size}): {e}")
        
        # 最適なバッチサイズの選択
        if results:
            # 処理時間あたりのアイテム数で評価
            optimal_size = max(results, key=lambda x: x[0] / x[1])[0]
            return optimal_size
        
        return self.config.batch_size
    
    def monitor_performance(self, duration: int = 60) -> Dict[str, Any]:
        """
        パフォーマンスの監視
        
        Args:
            duration: 監視時間（秒）
            
        Returns:
            監視結果の辞書
        """
        results = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_io': [],
            'database_operations': []
        }
        
        process = psutil.Process()
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # CPU使用率
            results['cpu_usage'].append(process.cpu_percent())
            
            # メモリ使用量
            results['memory_usage'].append(process.memory_info().rss)
            
            # ディスクI/O
            io_counters = process.io_counters()
            results['disk_io'].append({
                'read_bytes': io_counters.read_bytes,
                'write_bytes': io_counters.write_bytes
            })
            
            # データベース操作の統計
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM sqlite_stat1")
                results['database_operations'].append(cursor.fetchall())
            
            time.sleep(1)
        
        # 統計情報の計算
        results['average_cpu_usage'] = np.mean(results['cpu_usage'])
        results['average_memory_usage'] = np.mean(results['memory_usage'])
        results['total_disk_read'] = sum(io['read_bytes'] for io in results['disk_io'])
        results['total_disk_write'] = sum(io['write_bytes'] for io in results['disk_io'])
        
        return results
    
    def cleanup_resources(self):
        """リソースのクリーンアップ"""
        # ガベージコレクションの実行
        gc.collect()
        
        # データベース接続のクリーンアップ
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA optimize")
            conn.execute("PRAGMA shrink_memory")
        
        # メモリ使用量の確認
        process = psutil.Process()
        self.logger.info(f"メモリ使用量: {process.memory_info().rss / 1024 / 1024:.2f} MB") 