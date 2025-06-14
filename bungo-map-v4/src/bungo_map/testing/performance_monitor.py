#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
パフォーマンス監視システム v4
ベンチマーク・最適化・リソース監視の統合システム
"""

import time
import psutil
import logging
import threading
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
import json
import gc
import tracemalloc
from functools import wraps

# Rich UIサポート
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress
    from rich.panel import Panel
    from rich.live import Live
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """パフォーマンス監視システム"""
    
    def __init__(self):
        self.metrics = {}
        self.benchmarks = {}
        self.monitoring_active = False
        self.baseline_metrics = None
        self.alert_thresholds = {
            'memory_mb': 500,
            'cpu_percent': 80,
            'response_time': 10.0,
            'disk_usage_percent': 90
        }
        
    def start_monitoring(self):
        """パフォーマンス監視開始"""
        self.monitoring_active = True
        self.baseline_metrics = self._collect_system_metrics()
        
        if RICH_AVAILABLE:
            console.print("[bold green]⚡ パフォーマンス監視開始[/bold green]")
        else:
            print("⚡ パフォーマンス監視開始")
    
    def stop_monitoring(self):
        """パフォーマンス監視停止"""
        self.monitoring_active = False
        
        if RICH_AVAILABLE:
            console.print("[bold red]⏹️ パフォーマンス監視停止[/bold red]")
        else:
            print("⏹️ パフォーマンス監視停止")
    
    def benchmark_function(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """関数のベンチマーク実行"""
        # メモリトレースの開始
        tracemalloc.start()
        gc.collect()  # ガベージコレクション
        
        # 初期メトリクス
        start_memory = psutil.Process().memory_info().rss
        start_cpu = psutil.cpu_percent()
        start_time = time.time()
        
        try:
            # 関数実行
            result = func(*args, **kwargs)
            execution_success = True
            error_message = None
            
        except Exception as e:
            result = None
            execution_success = False
            error_message = str(e)
        
        # 終了メトリクス
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        end_cpu = psutil.cpu_percent()
        
        # メモリトレース情報
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # パフォーマンス計算
        execution_time = end_time - start_time
        memory_delta = end_memory - start_memory
        cpu_delta = end_cpu - start_cpu
        
        benchmark_result = {
            'function_name': func.__name__ if hasattr(func, '__name__') else str(func),
            'execution_time': execution_time,
            'memory_delta_mb': memory_delta / 1024 / 1024,
            'peak_memory_mb': peak / 1024 / 1024,
            'cpu_delta': cpu_delta,
            'success': execution_success,
            'error': error_message,
            'timestamp': datetime.now().isoformat(),
            'result': str(result)[:100] if result else None
        }
        
        # ベンチマーク保存
        func_name = benchmark_result['function_name']
        if func_name not in self.benchmarks:
            self.benchmarks[func_name] = []
        
        self.benchmarks[func_name].append(benchmark_result)
        
        return benchmark_result
    
    def benchmark_cli_command(self, command: str, description: str = "") -> Dict[str, Any]:
        """CLIコマンドのベンチマーク"""
        import subprocess
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory
            
            benchmark_result = {
                'command': command,
                'description': description,
                'execution_time': execution_time,
                'memory_delta_mb': memory_delta / 1024 / 1024,
                'return_code': result.returncode,
                'success': result.returncode == 0,
                'stdout_length': len(result.stdout),
                'stderr_length': len(result.stderr),
                'timestamp': datetime.now().isoformat()
            }
            
            # ベンチマーク保存
            if 'cli_commands' not in self.benchmarks:
                self.benchmarks['cli_commands'] = []
            
            self.benchmarks['cli_commands'].append(benchmark_result)
            
            return benchmark_result
            
        except Exception as e:
            return {
                'command': command,
                'description': description,
                'execution_time': None,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def run_performance_suite(self) -> Dict[str, Any]:
        """包括的パフォーマンステスト実行"""
        if RICH_AVAILABLE:
            console.print("[bold blue]🚀 パフォーマンステスト開始[/bold blue]")
        
        self.start_monitoring()
        
        # テストスイート定義
        test_suite = [
            {
                'category': 'cli_performance',
                'name': 'CLI応答性能テスト',
                'tests': [
                    ('python src/bungo_map/cli/search_cli.py --help', 'Search CLI Help'),
                    ('python src/bungo_map/cli/export_cli.py stats', 'Export CLI Stats'),
                    ('python src/bungo_map/cli/geocode_cli.py stats', 'Geocode CLI Stats'),
                    ('python src/bungo_map/cli/expand_cli.py stats', 'Expand CLI Stats'),
                    ('python src/bungo_map/cli/add_cli.py stats', 'Add CLI Stats')
                ]
            },
            {
                'category': 'system_resources',
                'name': 'システムリソーステスト',
                'tests': [
                    ('memory_usage', 'メモリ使用量監視'),
                    ('cpu_usage', 'CPU使用率監視'),
                    ('disk_usage', 'ディスク使用量監視')
                ]
            },
            {
                'category': 'concurrency',
                'name': '並行処理性能テスト',
                'tests': [
                    ('concurrent_cli', '並行CLI実行'),
                    ('stress_test', 'ストレステスト')
                ]
            }
        ]
        
        results = {}
        
        if RICH_AVAILABLE:
            with Progress() as progress:
                main_task = progress.add_task("パフォーマンステスト実行中...", total=len(test_suite))
                
                for test_category in test_suite:
                    category_name = test_category['category']
                    progress.update(main_task, description=f"実行中: {test_category['name']}")
                    
                    category_results = self._run_performance_category(test_category)
                    results[category_name] = category_results
                    
                    progress.update(main_task, advance=1)
        else:
            for test_category in test_suite:
                category_name = test_category['category']
                print(f"実行中: {test_category['name']}")
                
                category_results = self._run_performance_category(test_category)
                results[category_name] = category_results
        
        self.stop_monitoring()
        
        # 結果分析・レポート生成
        self._generate_performance_report(results)
        
        return results
    
    def _run_performance_category(self, test_category: Dict) -> Dict[str, Any]:
        """パフォーマンステストカテゴリー実行"""
        category = test_category['category']
        tests = test_category['tests']
        
        if category == 'cli_performance':
            return self._test_cli_performance(tests)
        elif category == 'system_resources':
            return self._test_system_resources(tests)
        elif category == 'concurrency':
            return self._test_concurrency_performance(tests)
        else:
            return {'error': f'Unknown category: {category}'}
    
    def _test_cli_performance(self, tests: List[tuple]) -> Dict[str, Any]:
        """CLI性能テスト"""
        results = []
        total_time = 0
        
        for command, description in tests:
            benchmark = self.benchmark_cli_command(command, description)
            results.append(benchmark)
            
            if benchmark.get('execution_time'):
                total_time += benchmark['execution_time']
        
        # 性能分析
        successful_tests = [r for r in results if r.get('success', False)]
        avg_response_time = sum(r['execution_time'] for r in successful_tests) / len(successful_tests) if successful_tests else 0
        
        return {
            'results': results,
            'summary': {
                'total_tests': len(tests),
                'successful': len(successful_tests),
                'avg_response_time': avg_response_time,
                'total_time': total_time,
                'performance_grade': self._calculate_performance_grade(avg_response_time)
            }
        }
    
    def _test_system_resources(self, tests: List[tuple]) -> Dict[str, Any]:
        """システムリソーステスト"""
        resource_metrics = {}
        
        # メモリ使用量
        memory = psutil.virtual_memory()
        resource_metrics['memory'] = {
            'total_gb': memory.total / 1024**3,
            'available_gb': memory.available / 1024**3,
            'used_percent': memory.percent,
            'alert': memory.percent > self.alert_thresholds['memory_mb']
        }
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        resource_metrics['cpu'] = {
            'usage_percent': cpu_percent,
            'cores': psutil.cpu_count(),
            'alert': cpu_percent > self.alert_thresholds['cpu_percent']
        }
        
        # ディスク使用量
        disk = psutil.disk_usage('/')
        resource_metrics['disk'] = {
            'total_gb': disk.total / 1024**3,
            'free_gb': disk.free / 1024**3,
            'used_percent': (disk.used / disk.total) * 100,
            'alert': (disk.used / disk.total) * 100 > self.alert_thresholds['disk_usage_percent']
        }
        
        # プロセス情報
        process = psutil.Process()
        resource_metrics['process'] = {
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'cpu_percent': process.cpu_percent(),
            'threads': process.num_threads(),
            'open_files': len(process.open_files())
        }
        
        # アラート集計
        alerts = sum(1 for metric in resource_metrics.values() if metric.get('alert', False))
        
        return {
            'metrics': resource_metrics,
            'summary': {
                'alerts': alerts,
                'status': 'warning' if alerts > 0 else 'healthy',
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def _test_concurrency_performance(self, tests: List[tuple]) -> Dict[str, Any]:
        """並行処理性能テスト"""
        import threading
        import queue
        
        # 並行CLI実行テスト
        concurrent_commands = [
            'python src/bungo_map/cli/search_cli.py --help',
            'python src/bungo_map/cli/export_cli.py stats',
            'python src/bungo_map/cli/geocode_cli.py stats',
            'python src/bungo_map/cli/expand_cli.py stats'
        ]
        
        results_queue = queue.Queue()
        
        def run_concurrent_command(command):
            benchmark = self.benchmark_cli_command(command, f"Concurrent: {command.split()[-1]}")
            results_queue.put(benchmark)
        
        # 並行実行
        start_time = time.time()
        threads = []
        
        for command in concurrent_commands:
            thread = threading.Thread(target=run_concurrent_command, args=(command,))
            thread.start()
            threads.append(thread)
        
        # 完了待機
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_concurrent_time = end_time - start_time
        
        # 結果収集
        concurrent_results = []
        while not results_queue.empty():
            concurrent_results.append(results_queue.get())
        
        # シーケンシャル実行時間と比較
        sequential_time = sum(r.get('execution_time', 0) for r in concurrent_results)
        speedup = sequential_time / total_concurrent_time if total_concurrent_time > 0 else 0
        
        return {
            'concurrent_results': concurrent_results,
            'summary': {
                'concurrent_time': total_concurrent_time,
                'sequential_time': sequential_time,
                'speedup_ratio': speedup,
                'efficiency': speedup / len(concurrent_commands) if len(concurrent_commands) > 0 else 0,
                'threads_used': len(concurrent_commands)
            }
        }
    
    def _calculate_performance_grade(self, avg_response_time: float) -> str:
        """パフォーマンスグレード計算"""
        if avg_response_time < 1.0:
            return 'A'
        elif avg_response_time < 3.0:
            return 'B'
        elif avg_response_time < 5.0:
            return 'C'
        elif avg_response_time < 10.0:
            return 'D'
        else:
            return 'F'
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクス収集"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_performance_report(self, results: Dict[str, Any]):
        """パフォーマンスレポート生成"""
        if RICH_AVAILABLE:
            console.print("\n" + "=" * 80)
            console.print("[bold blue]⚡ パフォーマンステストレポート[/bold blue]")
            console.print("=" * 80)
            
            # CLI性能結果
            if 'cli_performance' in results:
                cli_results = results['cli_performance']
                cli_summary = cli_results.get('summary', {})
                
                cli_panel = Panel.fit(
                    f"[bold]CLI性能テスト[/bold]\n"
                    f"成功率: {cli_summary.get('successful', 0)}/{cli_summary.get('total_tests', 0)}\n"
                    f"平均応答時間: {cli_summary.get('avg_response_time', 0):.2f}秒\n"
                    f"性能グレード: {cli_summary.get('performance_grade', 'N/A')}\n"
                    f"総実行時間: {cli_summary.get('total_time', 0):.2f}秒",
                    title="🖥️ CLI性能"
                )
                console.print(cli_panel)
            
            # システムリソース結果
            if 'system_resources' in results:
                resource_results = results['system_resources']
                resource_summary = resource_results.get('summary', {})
                
                resource_panel = Panel.fit(
                    f"[bold]システムリソース[/bold]\n"
                    f"ステータス: {resource_summary.get('status', 'unknown')}\n"
                    f"アラート数: {resource_summary.get('alerts', 0)}\n"
                    f"チェック時刻: {resource_summary.get('timestamp', 'N/A')[:19]}",
                    title="💾 リソース"
                )
                console.print(resource_panel)
            
            # 並行処理結果
            if 'concurrency' in results:
                concurrency_results = results['concurrency']
                concurrency_summary = concurrency_results.get('summary', {})
                
                concurrency_panel = Panel.fit(
                    f"[bold]並行処理性能[/bold]\n"
                    f"並行実行時間: {concurrency_summary.get('concurrent_time', 0):.2f}秒\n"
                    f"速度向上比: {concurrency_summary.get('speedup_ratio', 0):.1f}x\n"
                    f"効率: {concurrency_summary.get('efficiency', 0):.1%}\n"
                    f"使用スレッド: {concurrency_summary.get('threads_used', 0)}",
                    title="🔄 並行処理"
                )
                console.print(concurrency_panel)
            
            # 詳細テーブル
            if 'cli_performance' in results:
                table = Table(title="📊 CLI詳細パフォーマンス")
                table.add_column("コマンド", style="cyan")
                table.add_column("実行時間", style="yellow")
                table.add_column("メモリ使用", style="green")
                table.add_column("ステータス", style="magenta")
                
                for result in results['cli_performance']['results']:
                    table.add_row(
                        result.get('description', 'N/A'),
                        f"{result.get('execution_time', 0):.2f}秒",
                        f"{result.get('memory_delta_mb', 0):.1f}MB",
                        "✅" if result.get('success', False) else "❌"
                    )
                
                console.print(table)
        
        else:
            print("\n" + "=" * 80)
            print("⚡ パフォーマンステストレポート")
            print("=" * 80)
            
            for category, result in results.items():
                print(f"\n{category}: {result.get('summary', {})}")
        
        # JSON レポート保存
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'benchmarks': self.benchmarks
        }
        
        report_file = Path('performance_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        if RICH_AVAILABLE:
            console.print(f"\n📄 詳細レポート: {report_file}")
        else:
            print(f"\n📄 詳細レポート: {report_file}")

def performance_timer(func):
    """パフォーマンス計測デコレータ"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        monitor = PerformanceMonitor()
        result = monitor.benchmark_function(func, *args, **kwargs)
        
        if RICH_AVAILABLE:
            console.print(f"⚡ {func.__name__}: {result['execution_time']:.3f}秒")
        else:
            print(f"⚡ {func.__name__}: {result['execution_time']:.3f}秒")
        
        return result
    return wrapper

def main():
    """パフォーマンス監視システム実行"""
    monitor = PerformanceMonitor()
    results = monitor.run_performance_suite()
    
    return results

if __name__ == '__main__':
    main() 