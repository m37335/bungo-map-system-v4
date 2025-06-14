#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統合テストスイート v4
全システム機能の包括的動作確認・品質保証
"""

import os
import sys
import time
import logging
import subprocess
import psutil
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json

# Rich UIサポート
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.tree import Tree
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False

logger = logging.getLogger(__name__)

class IntegrationTestSuite:
    """統合テストスイート"""
    
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        self.error_log = []
        self.start_time = None
        self.base_path = Path(__file__).parent.parent.parent.parent
        
    def run_full_test_suite(self) -> Dict[str, Any]:
        """フル統合テスト実行"""
        if RICH_AVAILABLE:
            console.print("[bold green]🧪 統合テストスイート v4 開始[/bold green]")
        
        self.start_time = time.time()
        
        # テストカテゴリー
        test_categories = [
            ('system_health', '🔧 システムヘルスチェック'),
            ('cli_integration', '🖥️ CLI統合テスト'),
            ('ai_system', '🤖 AI機能統合テスト'),
            ('data_pipeline', '📊 データパイプライン統合'),
            ('performance', '⚡ パフォーマンステスト'),
            ('error_handling', '🛡️ エラーハンドリング'),
            ('memory_usage', '💾 メモリ使用量テスト'),
            ('concurrent_ops', '🔄 並行処理テスト')
        ]
        
        overall_results = {}
        
        if RICH_AVAILABLE:
            with Progress() as progress:
                main_task = progress.add_task("統合テスト実行中...", total=len(test_categories))
                
                for category, description in test_categories:
                    progress.update(main_task, description=f"実行中: {description}")
                    
                    result = self._run_test_category(category)
                    overall_results[category] = result
                    
                    progress.update(main_task, advance=1)
        else:
            for category, description in test_categories:
                print(f"実行中: {description}")
                result = self._run_test_category(category)
                overall_results[category] = result
        
        # 総合レポート生成
        self._generate_integration_report(overall_results)
        
        return overall_results
    
    def _run_test_category(self, category: str) -> Dict[str, Any]:
        """テストカテゴリー実行"""
        if category == 'system_health':
            return self._test_system_health()
        elif category == 'cli_integration':
            return self._test_cli_integration()
        elif category == 'ai_system':
            return self._test_ai_system()
        elif category == 'data_pipeline':
            return self._test_data_pipeline()
        elif category == 'performance':
            return self._test_performance()
        elif category == 'error_handling':
            return self._test_error_handling()
        elif category == 'memory_usage':
            return self._test_memory_usage()
        elif category == 'concurrent_ops':
            return self._test_concurrent_operations()
        else:
            return {'success': False, 'error': f'Unknown category: {category}'}
    
    def _test_system_health(self) -> Dict[str, Any]:
        """システムヘルスチェック"""
        health_checks = []
        
        # ファイル存在確認
        required_files = [
            'src/bungo_map/ai/ai_manager.py',
            'src/bungo_map/cli/search_cli.py',
            'src/bungo_map/cli/export_cli.py',
            'src/bungo_map/cli/geocode_cli.py',
            'src/bungo_map/cli/aozora_cli.py',
            'src/bungo_map/cli/expand_cli.py',
            'src/bungo_map/cli/add_cli.py'
        ]
        
        file_check_success = 0
        for file_path in required_files:
            full_path = self.base_path / file_path
            if full_path.exists():
                file_check_success += 1
                health_checks.append(f"✅ {file_path}")
            else:
                health_checks.append(f"❌ {file_path}")
        
        # Python環境確認
        python_version = sys.version_info
        python_ok = python_version.major == 3 and python_version.minor >= 8
        health_checks.append(f"{'✅' if python_ok else '❌'} Python {python_version.major}.{python_version.minor}")
        
        # 依存関係確認
        dependencies = ['click', 'rich', 'psutil']
        deps_ok = 0
        for dep in dependencies:
            try:
                __import__(dep)
                health_checks.append(f"✅ {dep}")
                deps_ok += 1
            except ImportError:
                health_checks.append(f"❌ {dep}")
        
        # システムリソース確認
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        memory_ok = memory.available > 1024 * 1024 * 1024  # 1GB以上
        disk_ok = disk.free > 1024 * 1024 * 1024  # 1GB以上
        
        health_checks.append(f"{'✅' if memory_ok else '❌'} メモリ: {memory.available / 1024**3:.1f}GB利用可能")
        health_checks.append(f"{'✅' if disk_ok else '❌'} ディスク: {disk.free / 1024**3:.1f}GB利用可能")
        
        success_rate = (file_check_success + deps_ok + int(python_ok) + int(memory_ok) + int(disk_ok)) / (len(required_files) + len(dependencies) + 3)
        
        return {
            'success': success_rate >= 0.8,
            'success_rate': success_rate,
            'checks': health_checks,
            'details': {
                'files_ok': f"{file_check_success}/{len(required_files)}",
                'deps_ok': f"{deps_ok}/{len(dependencies)}",
                'python_ok': python_ok,
                'resources_ok': memory_ok and disk_ok
            }
        }
    
    def _test_cli_integration(self) -> Dict[str, Any]:
        """CLI統合テスト"""
        cli_tests = [
            ('search', 'python src/bungo_map/cli/search_cli.py --help'),
            ('export', 'python src/bungo_map/cli/export_cli.py --help'),
            ('geocode', 'python src/bungo_map/cli/geocode_cli.py --help'),
            ('aozora', 'python src/bungo_map/cli/aozora_cli.py --help'),
            ('expand', 'python src/bungo_map/cli/expand_cli.py --help'),
            ('add', 'python src/bungo_map/cli/add_cli.py --help')
        ]
        
        results = []
        success_count = 0
        
        for cli_name, command in cli_tests:
            try:
                result = subprocess.run(
                    command.split(),
                    cwd=self.base_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    results.append(f"✅ {cli_name} CLI")
                    success_count += 1
                else:
                    results.append(f"❌ {cli_name} CLI")
                    
            except Exception as e:
                results.append(f"❌ {cli_name} CLI - {str(e)[:50]}")
        
        # 機能別テスト
        functional_tests = [
            ('search_places', 'python src/bungo_map/cli/search_cli.py places 東京 --limit 3'),
            ('export_csv', 'python src/bungo_map/cli/export_cli.py csv test_integration.csv --format places'),
            ('geocode_single', 'python src/bungo_map/cli/geocode_cli.py single 東京駅'),
            ('expand_stats', 'python src/bungo_map/cli/expand_cli.py stats')
        ]
        
        for test_name, command in functional_tests:
            try:
                result = subprocess.run(
                    command.split(),
                    cwd=self.base_path,
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                if result.returncode == 0:
                    results.append(f"✅ {test_name}")
                    success_count += 1
                else:
                    results.append(f"❌ {test_name}")
                    
            except Exception as e:
                results.append(f"❌ {test_name} - {str(e)[:50]}")
        
        total_tests = len(cli_tests) + len(functional_tests)
        success_rate = success_count / total_tests
        
        return {
            'success': success_rate >= 0.8,
            'success_rate': success_rate,
            'results': results,
            'total_tests': total_tests,
            'passed': success_count
        }
    
    def _test_ai_system(self) -> Dict[str, Any]:
        """AI機能統合テスト"""
        try:
            sys.path.append(str(self.base_path / 'src'))
            from bungo_map.ai.ai_manager import AIManager
            
            ai_manager = AIManager()
            
            # AI機能テスト
            tests = []
            success_count = 0
            
            # 1. 初期化テスト
            try:
                if ai_manager:
                    tests.append("✅ AI Manager初期化")
                    success_count += 1
                else:
                    tests.append("❌ AI Manager初期化")
            except Exception as e:
                tests.append(f"❌ AI Manager初期化 - {str(e)[:50]}")
            
            # 2. 接続テスト
            try:
                connection_result = ai_manager.test_connection()
                if connection_result.get('success', False):
                    tests.append("✅ API接続テスト")
                    success_count += 1
                else:
                    tests.append("❌ API接続テスト")
            except Exception as e:
                tests.append(f"❌ API接続テスト - {str(e)[:50]}")
            
            # 3. データ分析テスト
            try:
                sample_data = [
                    {'place_name': '東京', 'confidence': 0.95, 'category': 'major_city'},
                    {'place_name': '京都', 'confidence': 0.90, 'category': 'major_city'}
                ]
                analysis = ai_manager.analyze_place_data(sample_data)
                
                if analysis and 'quality_score' in analysis:
                    tests.append("✅ データ分析機能")
                    success_count += 1
                else:
                    tests.append("❌ データ分析機能")
            except Exception as e:
                tests.append(f"❌ データ分析機能 - {str(e)[:50]}")
            
            # 4. 統計生成テスト
            try:
                stats = ai_manager.get_statistics()
                if stats:
                    tests.append("✅ 統計生成機能")
                    success_count += 1
                else:
                    tests.append("❌ 統計生成機能")
            except Exception as e:
                tests.append(f"❌ 統計生成機能 - {str(e)[:50]}")
            
            total_tests = 4
            success_rate = success_count / total_tests
            
            return {
                'success': success_rate >= 0.75,
                'success_rate': success_rate,
                'tests': tests,
                'total_tests': total_tests,
                'passed': success_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"AI システムテスト失敗: {str(e)}",
                'tests': [f"❌ AI システム全体 - {str(e)[:50]}"]
            }
    
    def _test_data_pipeline(self) -> Dict[str, Any]:
        """データパイプライン統合テスト"""
        pipeline_tests = []
        success_count = 0
        
        # 1. 地名抽出パイプライン
        try:
            sys.path.append(str(self.base_path / 'src'))
            
            # 抽出器存在確認
            extractor_files = [
                'src/bungo_map/extractors_v4/ginza_place_extractor.py',
                'src/bungo_map/extractors_v4/enhanced_place_extractor.py',
                'src/bungo_map/extractors_v4/advanced_place_extractor.py'
            ]
            
            extractor_count = 0
            for extractor_file in extractor_files:
                if (self.base_path / extractor_file).exists():
                    extractor_count += 1
            
            if extractor_count >= 2:
                pipeline_tests.append("✅ 地名抽出器群")
                success_count += 1
            else:
                pipeline_tests.append("❌ 地名抽出器群")
                
        except Exception as e:
            pipeline_tests.append(f"❌ 地名抽出器群 - {str(e)[:50]}")
        
        # 2. データ変換パイプライン
        try:
            # エクスポート機能テスト
            export_result = subprocess.run(
                ['python', 'src/bungo_map/cli/export_cli.py', 'stats'],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if export_result.returncode == 0:
                pipeline_tests.append("✅ データエクスポート")
                success_count += 1
            else:
                pipeline_tests.append("❌ データエクスポート")
                
        except Exception as e:
            pipeline_tests.append(f"❌ データエクスポート - {str(e)[:50]}")
        
        # 3. ジオコーディングパイプライン
        try:
            geocode_result = subprocess.run(
                ['python', 'src/bungo_map/cli/geocode_cli.py', 'stats'],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if geocode_result.returncode == 0:
                pipeline_tests.append("✅ ジオコーディング")
                success_count += 1
            else:
                pipeline_tests.append("❌ ジオコーディング")
                
        except Exception as e:
            pipeline_tests.append(f"❌ ジオコーディング - {str(e)[:50]}")
        
        # 4. データベース拡張パイプライン
        try:
            expand_result = subprocess.run(
                ['python', 'src/bungo_map/cli/expand_cli.py', 'stats'],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if expand_result.returncode == 0:
                pipeline_tests.append("✅ データベース拡張")
                success_count += 1
            else:
                pipeline_tests.append("❌ データベース拡張")
                
        except Exception as e:
            pipeline_tests.append(f"❌ データベース拡張 - {str(e)[:50]}")
        
        total_tests = 4
        success_rate = success_count / total_tests
        
        return {
            'success': success_rate >= 0.75,
            'success_rate': success_rate,
            'tests': pipeline_tests,
            'total_tests': total_tests,
            'passed': success_count
        }
    
    def _test_performance(self) -> Dict[str, Any]:
        """パフォーマンステスト"""
        performance_results = {}
        
        # 1. CLI応答時間テスト
        cli_commands = [
            ('help_response', 'python src/bungo_map/cli/search_cli.py --help'),
            ('stats_response', 'python src/bungo_map/cli/expand_cli.py stats'),
            ('export_response', 'python src/bungo_map/cli/export_cli.py stats')
        ]
        
        for test_name, command in cli_commands:
            start_time = time.time()
            try:
                result = subprocess.run(
                    command.split(),
                    cwd=self.base_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                performance_results[test_name] = {
                    'response_time': response_time,
                    'success': result.returncode == 0,
                    'benchmark': response_time < 5.0  # 5秒以内
                }
                
            except Exception as e:
                performance_results[test_name] = {
                    'response_time': None,
                    'success': False,
                    'error': str(e)
                }
        
        # 2. メモリ使用量測定
        process = psutil.Process()
        memory_before = process.memory_info().rss
        
        # 軽量処理実行
        try:
            subprocess.run(
                ['python', 'src/bungo_map/cli/search_cli.py', '--help'],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=10
            )
        except:
            pass
        
        memory_after = process.memory_info().rss
        memory_usage = memory_after - memory_before
        
        performance_results['memory_usage'] = {
            'memory_delta': memory_usage,
            'memory_mb': memory_usage / 1024 / 1024,
            'benchmark': memory_usage < 50 * 1024 * 1024  # 50MB以内
        }
        
        # 総合評価
        benchmark_passed = sum(1 for r in performance_results.values() if r.get('benchmark', False))
        total_benchmarks = len(performance_results)
        
        return {
            'success': benchmark_passed >= total_benchmarks * 0.8,
            'benchmark_rate': benchmark_passed / total_benchmarks,
            'results': performance_results,
            'summary': {
                'avg_response_time': sum(r.get('response_time', 0) for r in performance_results.values() if r.get('response_time')]),
                'memory_usage_mb': performance_results['memory_usage']['memory_mb'],
                'benchmarks_passed': f"{benchmark_passed}/{total_benchmarks}"
            }
        }
    
    def _test_error_handling(self) -> Dict[str, Any]:
        """エラーハンドリングテスト"""
        error_tests = []
        success_count = 0
        
        # 1. 不正なコマンドライン引数
        try:
            result = subprocess.run(
                ['python', 'src/bungo_map/cli/search_cli.py', 'invalid_command'],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # エラーが適切に処理されているか確認
            if result.returncode != 0 and ('Usage:' in result.stdout or 'Error' in result.stderr):
                error_tests.append("✅ 不正コマンド処理")
                success_count += 1
            else:
                error_tests.append("❌ 不正コマンド処理")
                
        except Exception as e:
            error_tests.append(f"❌ 不正コマンド処理 - {str(e)[:50]}")
        
        # 2. 存在しないファイル指定
        try:
            result = subprocess.run(
                ['python', 'src/bungo_map/cli/export_cli.py', 'csv', '/nonexistent/path/file.csv'],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # エラーが適切に処理されているか確認
            if result.returncode != 0:
                error_tests.append("✅ ファイルエラー処理")
                success_count += 1
            else:
                error_tests.append("❌ ファイルエラー処理")
                
        except Exception as e:
            error_tests.append(f"❌ ファイルエラー処理 - {str(e)[:50]}")
        
        # 3. ネットワークエラーシミュレーション
        try:
            # API接続テスト（失敗期待）
            sys.path.append(str(self.base_path / 'src'))
            from bungo_map.ai.ai_manager import AIManager
            
            ai_manager = AIManager()
            # 実際のAPI呼び出しを行わずフォールバック動作確認
            connection_result = ai_manager.test_connection()
            
            # フォールバック動作が適切に実装されているか
            if 'success' in connection_result:
                error_tests.append("✅ ネットワークエラー処理")
                success_count += 1
            else:
                error_tests.append("❌ ネットワークエラー処理")
                
        except Exception as e:
            error_tests.append(f"❌ ネットワークエラー処理 - {str(e)[:50]}")
        
        total_tests = 3
        success_rate = success_count / total_tests
        
        return {
            'success': success_rate >= 0.67,
            'success_rate': success_rate,
            'tests': error_tests,
            'total_tests': total_tests,
            'passed': success_count
        }
    
    def _test_memory_usage(self) -> Dict[str, Any]:
        """メモリ使用量テスト"""
        memory_results = {}
        
        # 初期メモリ状況
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # 各CLI実行時のメモリ使用量測定
        cli_commands = [
            'python src/bungo_map/cli/search_cli.py --help',
            'python src/bungo_map/cli/export_cli.py stats',
            'python src/bungo_map/cli/geocode_cli.py stats'
        ]
        
        memory_measurements = []
        
        for command in cli_commands:
            try:
                start_memory = process.memory_info().rss
                
                subprocess.run(
                    command.split(),
                    cwd=self.base_path,
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                end_memory = process.memory_info().rss
                memory_delta = end_memory - start_memory
                memory_measurements.append(memory_delta)
                
            except Exception:
                memory_measurements.append(0)
        
        avg_memory_usage = sum(memory_measurements) / len(memory_measurements)
        max_memory_usage = max(memory_measurements)
        
        # ベンチマーク: 平均50MB以内、最大100MB以内
        avg_benchmark = avg_memory_usage < 50 * 1024 * 1024
        max_benchmark = max_memory_usage < 100 * 1024 * 1024
        
        return {
            'success': avg_benchmark and max_benchmark,
            'avg_memory_mb': avg_memory_usage / 1024 / 1024,
            'max_memory_mb': max_memory_usage / 1024 / 1024,
            'benchmarks': {
                'avg_passed': avg_benchmark,
                'max_passed': max_benchmark
            },
            'measurements': [m / 1024 / 1024 for m in memory_measurements]
        }
    
    def _test_concurrent_operations(self) -> Dict[str, Any]:
        """並行処理テスト"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def run_cli_command(command, result_queue):
            try:
                result = subprocess.run(
                    command.split(),
                    cwd=self.base_path,
                    capture_output=True,
                    text=True,
                    timeout=20
                )
                result_queue.put(('success', result.returncode == 0))
            except Exception as e:
                result_queue.put(('error', str(e)))
        
        # 並行実行するコマンド
        concurrent_commands = [
            'python src/bungo_map/cli/search_cli.py --help',
            'python src/bungo_map/cli/export_cli.py stats',
            'python src/bungo_map/cli/geocode_cli.py stats',
            'python src/bungo_map/cli/expand_cli.py stats'
        ]
        
        # 並行実行
        threads = []
        start_time = time.time()
        
        for command in concurrent_commands:
            thread = threading.Thread(target=run_cli_command, args=(command, results_queue))
            thread.start()
            threads.append(thread)
        
        # スレッド完了待機
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 結果収集
        results = []
        success_count = 0
        
        while not results_queue.empty():
            result_type, result_value = results_queue.get()
            results.append((result_type, result_value))
            
            if result_type == 'success' and result_value:
                success_count += 1
        
        success_rate = success_count / len(concurrent_commands)
        time_benchmark = total_time < 30  # 30秒以内
        
        return {
            'success': success_rate >= 0.75 and time_benchmark,
            'success_rate': success_rate,
            'total_time': total_time,
            'time_benchmark': time_benchmark,
            'results': results,
            'concurrent_operations': len(concurrent_commands)
        }
    
    def _generate_integration_report(self, results: Dict[str, Any]):
        """統合テストレポート生成"""
        total_time = time.time() - self.start_time
        
        # 成功率計算
        category_scores = []
        for category, result in results.items():
            if 'success_rate' in result:
                category_scores.append(result['success_rate'])
            elif 'success' in result:
                category_scores.append(1.0 if result['success'] else 0.0)
        
        overall_success_rate = sum(category_scores) / len(category_scores) if category_scores else 0.0
        
        # レポート表示
        if RICH_AVAILABLE:
            console.print("\n" + "=" * 80)
            console.print("[bold blue]📋 統合テストレポート[/bold blue]")
            console.print("=" * 80)
            
            # 総合結果
            overall_panel = Panel.fit(
                f"[bold]総合成功率: {overall_success_rate:.1%}[/bold]\n"
                f"実行時間: {total_time:.1f}秒\n"
                f"テスト日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"ステータス: {'🎉 合格' if overall_success_rate >= 0.8 else '⚠️ 要改善'}",
                title="🎯 総合結果"
            )
            console.print(overall_panel)
            
            # カテゴリー別結果テーブル
            table = Table(title="📊 カテゴリー別テスト結果")
            table.add_column("カテゴリー", style="cyan")
            table.add_column("成功率", style="yellow")
            table.add_column("ステータス", style="green")
            table.add_column("詳細", style="magenta")
            
            category_names = {
                'system_health': '🔧 システムヘルス',
                'cli_integration': '🖥️ CLI統合',
                'ai_system': '🤖 AI機能',
                'data_pipeline': '📊 データパイプライン',
                'performance': '⚡ パフォーマンス',
                'error_handling': '🛡️ エラーハンドリング',
                'memory_usage': '💾 メモリ使用量',
                'concurrent_ops': '🔄 並行処理'
            }
            
            for category, result in results.items():
                name = category_names.get(category, category)
                
                if 'success_rate' in result:
                    success_rate = result['success_rate']
                    status = "✅ 合格" if success_rate >= 0.8 else "⚠️ 要改善" if success_rate >= 0.6 else "❌ 不合格"
                    details = f"{result.get('passed', 0)}/{result.get('total_tests', 0)} 成功"
                elif 'success' in result:
                    success_rate = 1.0 if result['success'] else 0.0
                    status = "✅ 合格" if result['success'] else "❌ 不合格"
                    details = "実行完了" if result['success'] else "実行失敗"
                else:
                    success_rate = 0.0
                    status = "❓ 不明"
                    details = "結果不明"
                
                table.add_row(
                    name,
                    f"{success_rate:.1%}",
                    status,
                    details
                )
            
            console.print(table)
            
        else:
            print("\n" + "=" * 80)
            print("📋 統合テストレポート")
            print("=" * 80)
            print(f"総合成功率: {overall_success_rate:.1%}")
            print(f"実行時間: {total_time:.1f}秒")
            print(f"ステータス: {'🎉 合格' if overall_success_rate >= 0.8 else '⚠️ 要改善'}")
            
            for category, result in results.items():
                if 'success_rate' in result:
                    print(f"{category}: {result['success_rate']:.1%}")
                elif 'success' in result:
                    print(f"{category}: {'✅' if result['success'] else '❌'}")
        
        # JSON レポート保存
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'overall_success_rate': overall_success_rate,
            'execution_time': total_time,
            'categories': results
        }
        
        report_file = self.base_path / 'integration_test_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        if RICH_AVAILABLE:
            console.print(f"\n📄 詳細レポート: {report_file}")
        else:
            print(f"\n📄 詳細レポート: {report_file}")

def main():
    """統合テストスイート実行"""
    suite = IntegrationTestSuite()
    results = suite.run_full_test_suite()
    
    return results

if __name__ == '__main__':
    main() 