"""
AI機能CLI
地名データクリーニング・検証コマンド
"""

import os
import json
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# .envファイルの読み込み
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from ..ai.cleaners.place_cleaner import PlaceCleaner
from ..utils.database_utils import get_database_path

console = Console()

@click.group()
def ai():
    """🤖 AI機能: 地名データクリーニング・検証"""
    pass

@ai.command()
@click.option('--limit', '-l', type=int, help='分析する地名数の上限')
@click.option('--confidence', '-c', type=float, default=0.7, help='信頼度の閾値 (0.0-1.0)')
@click.option('--verbose', '-v', is_flag=True, help='個別の地名分析結果を詳細表示')
@click.option('--save-to-db', is_flag=True, help='AI分析結果をデータベースに保存')
@click.option('--output', '-o', help='分析結果の出力ファイルパス')
@click.option('--api-key', envvar='OPENAI_API_KEY', help='OpenAI APIキー')
def analyze(limit, confidence, verbose, save_to_db, output, api_key):
    """🔍 地名データの品質分析"""
    
    # APIキーのデバッグ出力
    if verbose:
        if api_key:
            console.print(f"🔑 APIキー確認: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else api_key}", style="green")
        else:
            console.print("❌ APIキーが見つかりません", style="red")
            console.print(f"環境変数 OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'Not Set')[:20]}...", style="yellow")
    
    if not api_key:
        console.print("❌ OpenAI APIキーが設定されていません。", style="red")
        console.print("環境変数 OPENAI_API_KEY を設定するか、--api-key オプションを使用してください。")
        return
    
    database_path = get_database_path()
    if not Path(database_path).exists():
        console.print(f"❌ データベースが見つかりません: {database_path}", style="red")
        return
    
    # PlaceCleanerを初期化
    cleaner = PlaceCleaner(database_path, api_key)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("地名データを分析中...", total=None)
        
        try:
            # 地名分析を実行
            analyses = cleaner.analyze_all_places(limit=limit, confidence_threshold=confidence, save_to_db=save_to_db)
            progress.update(task, description=f"分析完了: {len(analyses)}件")
            
        except Exception as e:
            console.print(f"❌ 分析エラー: {str(e)}", style="red")
            return
    
    if not analyses:
        console.print("⚠️ 分析対象の地名が見つかりませんでした。", style="yellow")
        return
    
    # レポート生成
    report = cleaner.generate_cleaning_report(analyses)
    
    # 結果表示
    _display_analysis_summary(report)
    _display_confidence_distribution(report)
    _display_type_distribution(report)
    _display_improvement_suggestions(report)
    
    # 詳細表示（verboseオプション）
    if verbose:
        _display_detailed_results(analyses)
    
    # ファイル出力
    if output:
        cleaner.export_analysis_results(analyses, output)
        console.print(f"✅ 分析結果を保存しました: {output}", style="green")

@ai.command()
@click.option('--confidence', '-c', type=float, default=0.7, help='分析時の信頼度閾値')
@click.option('--dry-run', is_flag=True, default=True, help='実際の更新は行わず、変更内容のみ表示')
@click.option('--apply', is_flag=True, help='実際にデータベースを更新')
@click.option('--api-key', envvar='OPENAI_API_KEY', help='OpenAI APIキー')
def normalize(confidence, dry_run, apply, api_key):
    """📝 地名の正規化を実行"""
    
    if not api_key:
        console.print("❌ OpenAI APIキーが設定されていません。", style="red")
        return
    
    database_path = get_database_path()
    cleaner = PlaceCleaner(database_path, api_key)
    
    # applyフラグが指定された場合はdry_runを無効化
    if apply:
        dry_run = False
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("地名データを分析中...", total=None)
        analyses = cleaner.analyze_all_places(confidence_threshold=confidence)
        progress.update(task, description="正規化を適用中...")
        
        result = cleaner.apply_normalizations(analyses, dry_run=dry_run)
    
    # 結果表示
    if result['applied']:
        console.print(f"✅ {result['updated_count']}件の地名を正規化しました。", style="green")
    else:
        console.print(f"📋 {result['would_update']}件の地名が正規化対象です。", style="blue")
        
        if result['normalizations']:
            table = Table(title="正規化予定の地名")
            table.add_column("元の地名", style="cyan")
            table.add_column("正規化後", style="green")
            table.add_column("信頼度", style="yellow")
            
            for norm in result['normalizations'][:10]:  # 最初の10件のみ表示
                table.add_row(
                    norm['original'],
                    norm['normalized'],
                    f"{norm['confidence']:.2f}"
                )
            
            console.print(table)
            
            if not apply:
                console.print("\n💡 実際に更新するには --apply オプションを使用してください。", style="blue")

@ai.command()
@click.option('--confidence-threshold', '-t', type=float, default=0.3, help='削除する信頼度の閾値')
@click.option('--dry-run', is_flag=True, default=True, help='実際の削除は行わず、対象のみ表示')
@click.option('--apply', is_flag=True, help='実際にデータベースから削除')
@click.option('--api-key', envvar='OPENAI_API_KEY', help='OpenAI APIキー')
def clean(confidence_threshold, dry_run, apply, api_key):
    """🗑️ 無効な地名を削除"""
    
    if not api_key:
        console.print("❌ OpenAI APIキーが設定されていません。", style="red")
        return
    
    database_path = get_database_path()
    cleaner = PlaceCleaner(database_path, api_key)
    
    # applyフラグが指定された場合はdry_runを無効化
    if apply:
        dry_run = False
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("地名データを分析中...", total=None)
        analyses = cleaner.analyze_all_places()
        progress.update(task, description="無効地名を削除中...")
        
        result = cleaner.remove_invalid_places(analyses, confidence_threshold, dry_run=dry_run)
    
    # 結果表示
    if result['applied']:
        console.print(f"✅ {result['deleted_count']}件の無効地名を削除しました。", style="green")
    else:
        console.print(f"📋 {result['would_delete']}件の地名が削除対象です。", style="blue")
        
        if result['candidates']:
            table = Table(title="削除対象の地名")
            table.add_column("地名", style="cyan")
            table.add_column("信頼度", style="yellow")
            table.add_column("理由", style="red")
            
            for candidate in result['candidates'][:10]:  # 最初の10件のみ表示
                table.add_row(
                    candidate['name'],
                    f"{candidate['confidence']:.2f}",
                    candidate['reasoning'][:50] + "..." if len(candidate['reasoning']) > 50 else candidate['reasoning']
                )
            
            console.print(table)
            
            if not apply:
                console.print("\n💡 実際に削除するには --apply オプションを使用してください。", style="blue")
                console.print("⚠️ 削除は元に戻せません。慎重に実行してください。", style="yellow")

@ai.command()
@click.option('--confidence', '-c', type=float, default=0.7, help='ジオコーディング対象の最低信頼度')
@click.option('--limit', '-l', type=int, help='処理する地名数の上限')
@click.option('--dry-run', is_flag=True, default=True, help='実際の更新は行わず、結果のみ表示')
@click.option('--apply', is_flag=True, help='実際にデータベースを更新')
@click.option('--use-google', is_flag=True, help='Google Geocoding APIを使用')
@click.option('--google-api-key', envvar='GOOGLE_MAPS_API_KEY', help='Google Maps APIキー')
def geocode(confidence, limit, dry_run, apply, use_google, google_api_key):
    """🌍 AI検証済み地名のジオコーディング"""
    
    database_path = get_database_path()
    if not Path(database_path).exists():
        console.print(f"❌ データベースが見つかりません: {database_path}", style="red")
        return
    
    if use_google and not google_api_key:
        console.print("❌ Google Maps APIキーが設定されていません。", style="red")
        return
    
    # applyフラグが指定された場合はdry_runを無効化
    if apply:
        dry_run = False
    
    try:
        from ..ai.geocoding.geocoder import PlaceGeocoder
        geocoder = PlaceGeocoder(database_path, use_google=use_google, google_api_key=google_api_key)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("ジオコーディング実行中...", total=None)
            
            # ジオコーディング実行
            result = geocoder.batch_geocode(
                min_ai_confidence=confidence,
                limit=limit,
                dry_run=dry_run
            )
            
            progress.update(task, description="ジオコーディング完了")
        
        # 結果表示
        _display_geocoding_results(result, dry_run, apply)
        
    except Exception as e:
        console.print(f"❌ ジオコーディングエラー: {str(e)}", style="red")

@ai.command()
@click.option('--limit', '-l', type=int, help='検証する地名数の上限')
@click.option('--severity', '-s', type=click.Choice(['high', 'medium', 'low', 'all']), default='all', help='表示する問題の重要度')
@click.option('--issue-type', '-t', type=click.Choice(['false_positive', 'context_mismatch', 'suspicious', 'all']), default='all', help='表示する問題のタイプ')
@click.option('--output', '-o', help='検証結果の出力ファイルパス')
def validate_extraction(limit, severity, issue_type, output):
    """🔍 地名抽出精度検証システム"""
    
    database_path = get_database_path()
    if not Path(database_path).exists():
        console.print(f"❌ データベースが見つかりません: {database_path}", style="red")
        return
    
    try:
        from ..ai.validation.extraction_validator import ExtractionValidator
        validator = ExtractionValidator(database_path)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("地名抽出精度を検証中...", total=None)
            
            # 検証実行
            issues, stats = validator.validate_extraction(limit=limit)
            
            progress.update(task, description="検証完了")
        
        # 結果表示
        _display_extraction_statistics(stats)
        _display_validation_issues(issues, severity, issue_type)
        
        # ファイル出力
        if output:
            _export_validation_results(issues, stats, output)
            console.print(f"✅ 検証結果を保存しました: {output}", style="green")
        
    except Exception as e:
        console.print(f"❌ 検証エラー: {str(e)}", style="red")

@ai.command()
@click.option('--api-key', envvar='OPENAI_API_KEY', help='OpenAI APIキー')
def test_connection(api_key):
    """🔌 OpenAI API接続テスト"""
    
    if not api_key:
        console.print("❌ OpenAI APIキーが設定されていません。", style="red")
        return
    
    try:
        from ..ai.connection.openai_connector import OpenAIConnector
        connector = OpenAIConnector(api_key)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("OpenAI API接続をテスト中...", total=None)
            
            # 接続テスト実行
            result = connector.test_connection()
            
            progress.update(task, description="接続テスト完了")
        
        if result['success']:
            console.print(f"✅ OpenAI API接続成功: {result['message']}", style="green")
        else:
            console.print(f"❌ OpenAI API接続失敗: {result['message']}", style="red")
        
    except Exception as e:
        console.print(f"❌ 接続テストエラー: {str(e)}", style="red")

@ai.command()
@click.option('--place-name', '-p', help='特定の地名を文脈分析（指定しない場合は疑わしい地名を自動選択）')
@click.option('--single-char', is_flag=True, help='一文字地名のみを対象にする')
@click.option('--limit', '-l', type=int, default=20, help='分析する地名数の上限')
@click.option('--output', '-o', help='分析結果の出力ファイルパス')
@click.option('--api-key', envvar='OPENAI_API_KEY', help='OpenAI APIキー')
def analyze_context(place_name, single_char, limit, output, api_key):
    """🔍 文脈ベース地名分析"""
    
    if not api_key:
        console.print("❌ OpenAI APIキーが設定されていません。", style="red")
        return
    
    database_path = get_database_path()
    if not Path(database_path).exists():
        console.print(f"❌ データベースが見つかりません: {database_path}", style="red")
        return
    
    try:
        from ..ai.context.context_analyzer import ContextAnalyzer
        analyzer = ContextAnalyzer(database_path, api_key)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("文脈ベース地名分析を実行中...", total=None)
            
            # 文脈分析実行
            analysis_results = analyzer.analyze_context(
                place_name=place_name,
                single_char=single_char,
                limit=limit
            )
            
            progress.update(task, description="文脈分析完了")
        
        # 結果表示
        _display_context_analysis_summary(analysis_results)
        _display_context_analysis_details(analysis_results)
        
        # ファイル出力
        if output:
            _export_context_analysis_results(analysis_results, output)
            console.print(f"✅ 分析結果を保存しました: {output}", style="green")
        
    except Exception as e:
        console.print(f"❌ 文脈分析エラー: {str(e)}", style="red")

@ai.command()
@click.option('--confidence-threshold', '-t', type=float, default=0.8, help='無効判定する信頼度の閾値')
@click.option('--dry-run', is_flag=True, default=True, help='実際の削除は行わず、対象のみ表示')
@click.option('--apply', is_flag=True, help='実際にデータベースから削除')
@click.option('--api-key', envvar='OPENAI_API_KEY', help='OpenAI APIキー')
def clean_context(confidence_threshold, dry_run, apply, api_key):
    """🗑️ 文脈判断による無効地名削除"""
    
    if not api_key:
        console.print("❌ OpenAI APIキーが設定されていません。", style="red")
        return
    
    database_path = get_database_path()
    if not Path(database_path).exists():
        console.print(f"❌ データベースが見つかりません: {database_path}", style="red")
        return
    
    # applyフラグが指定された場合はdry_runを無効化
    if apply:
        dry_run = False
    
    try:
        from ..ai.context.context_cleaner import ContextCleaner
        cleaner = ContextCleaner(database_path, api_key)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("文脈判断による無効地名を削除中...", total=None)
            
            # 文脈クリーニング実行
            invalid_places = cleaner.clean_context(
                confidence_threshold=confidence_threshold,
                dry_run=dry_run
            )
            
            progress.update(task, description="文脈クリーニング完了")
        
        # 結果表示
        _display_context_cleaning_results(invalid_places, dry_run, apply)
        
    except Exception as e:
        console.print(f"❌ 文脈クリーニングエラー: {str(e)}", style="red")

def _display_analysis_summary(report):
    """分析サマリーを表示"""
    console.print(Panel(
        f"📊 分析サマリー\n"
        f"総地名数: {report['total_places']}\n"
        f"高信頼度地名: {report['high_confidence']}\n"
        f"中信頼度地名: {report['medium_confidence']}\n"
        f"低信頼度地名: {report['low_confidence']}",
        title="分析サマリー",
        border_style="green"
    ))

def _display_confidence_distribution(report):
    """信頼度分布を表示"""
    console.print(Panel(
        f"📈 信頼度分布\n"
        f"0.0-0.3: {report['confidence_distribution']['0.0-0.3']}\n"
        f"0.3-0.6: {report['confidence_distribution']['0.3-0.6']}\n"
        f"0.6-0.9: {report['confidence_distribution']['0.6-0.9']}\n"
        f"0.9-1.0: {report['confidence_distribution']['0.9-1.0']}",
        title="信頼度分布",
        border_style="blue"
    ))

def _display_type_distribution(report):
    """タイプ分布を表示"""
    console.print(Panel(
        f"📊 タイプ分布\n"
        f"都道府県: {report['type_distribution']['prefecture']}\n"
        f"市区町村: {report['type_distribution']['city']}\n"
        f"自然地名: {report['type_distribution']['natural']}\n"
        f"その他: {report['type_distribution']['other']}",
        title="タイプ分布",
        border_style="yellow"
    ))

def _display_improvement_suggestions(report):
    """改善提案を表示"""
    console.print(Panel(
        f"💡 改善提案\n"
        f"{report['improvement_suggestions']}",
        title="改善提案",
        border_style="cyan"
    ))

def _display_detailed_results(analyses):
    """詳細な分析結果を表示"""
    table = Table(title="詳細な分析結果")
    table.add_column("地名", style="cyan")
    table.add_column("信頼度", style="yellow")
    table.add_column("タイプ", style="green")
    table.add_column("理由", style="blue")
    
    for analysis in analyses:
        table.add_row(
            analysis['name'],
            f"{analysis['confidence']:.2f}",
            analysis['type'],
            analysis['reasoning'][:50] + "..." if len(analysis['reasoning']) > 50 else analysis['reasoning']
        )
    
    console.print(table)

def _display_geocoding_results(result, dry_run, apply):
    """ジオコーディング結果を表示"""
    if result['applied']:
        console.print(f"✅ {result['updated_count']}件の地名をジオコーディングしました。", style="green")
    else:
        console.print(f"📋 {result['would_update']}件の地名がジオコーディング対象です。", style="blue")
        
        if result['geocoded']:
            table = Table(title="ジオコーディング予定の地名")
            table.add_column("地名", style="cyan")
            table.add_column("緯度", style="green")
            table.add_column("経度", style="green")
            table.add_column("信頼度", style="yellow")
            
            for geo in result['geocoded'][:10]:  # 最初の10件のみ表示
                table.add_row(
                    geo['name'],
                    f"{geo['latitude']:.6f}",
                    f"{geo['longitude']:.6f}",
                    f"{geo['confidence']:.2f}"
                )
            
            console.print(table)
            
            if not apply:
                console.print("\n💡 実際に更新するには --apply オプションを使用してください。", style="blue")

def _display_geocoding_statistics(stats):
    """ジオコーディング統計を表示"""
    console.print(Panel(
        f"📊 ジオコーディング統計\n"
        f"総地名数: {stats['total_places']}\n"
        f"ジオコーディング成功: {stats['successful']}\n"
        f"ジオコーディング失敗: {stats['failed']}\n"
        f"平均信頼度: {stats['average_confidence']:.2f}",
        title="ジオコーディング統計",
        border_style="green"
    ))

def _filter_issues(issues, severity_filter, type_filter):
    """問題をフィルタリング"""
    filtered = issues
    
    if severity_filter != 'all':
        filtered = [i for i in filtered if i['severity'] == severity_filter]
    
    if type_filter != 'all':
        filtered = [i for i in filtered if i['type'] == type_filter]
    
    return filtered

def _display_extraction_statistics(stats):
    """抽出統計を表示"""
    console.print(Panel(
        f"📊 抽出統計\n"
        f"総地名数: {stats['total_places']}\n"
        f"抽出成功: {stats['successful']}\n"
        f"抽出失敗: {stats['failed']}\n"
        f"平均信頼度: {stats['average_confidence']:.2f}",
        title="抽出統計",
        border_style="blue"
    ))

def _display_validation_issues(issues, severity_filter, type_filter):
    """検証問題を表示"""
    filtered_issues = _filter_issues(issues, severity_filter, type_filter)
    
    if not filtered_issues:
        console.print("✅ 問題は見つかりませんでした。", style="green")
        return
    
    table = Table(title="検証問題")
    table.add_column("地名", style="cyan")
    table.add_column("重要度", style="yellow")
    table.add_column("タイプ", style="red")
    table.add_column("理由", style="blue")
    
    for issue in filtered_issues:
        table.add_row(
            issue['name'],
            issue['severity'],
            issue['type'],
            issue['reasoning'][:50] + "..." if len(issue['reasoning']) > 50 else issue['reasoning']
        )
    
    console.print(table)

def _export_validation_results(issues, stats, output_path):
    """検証結果をエクスポート"""
    result = {
        'issues': issues,
        'statistics': stats
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def _display_context_analysis_summary(analysis_results):
    """文脈分析サマリーを表示"""
    console.print(Panel(
        f"📊 文脈分析サマリー\n"
        f"総地名数: {analysis_results['total_places']}\n"
        f"文脈一致: {analysis_results['context_match']}\n"
        f"文脈不一致: {analysis_results['context_mismatch']}\n"
        f"平均信頼度: {analysis_results['average_confidence']:.2f}",
        title="文脈分析サマリー",
        border_style="green"
    ))

def _display_context_analysis_details(analysis_results):
    """文脈分析詳細を表示"""
    table = Table(title="文脈分析詳細")
    table.add_column("地名", style="cyan")
    table.add_column("文脈", style="blue")
    table.add_column("信頼度", style="yellow")
    table.add_column("理由", style="green")
    
    for analysis in analysis_results['details']:
        table.add_row(
            analysis['name'],
            analysis['context'][:50] + "..." if len(analysis['context']) > 50 else analysis['context'],
            f"{analysis['confidence']:.2f}",
            analysis['reasoning'][:50] + "..." if len(analysis['reasoning']) > 50 else analysis['reasoning']
        )
    
    console.print(table)

def _display_context_cleaning_results(invalid_places, dry_run, apply):
    """文脈クリーニング結果を表示"""
    if apply:
        console.print(f"✅ {len(invalid_places)}件の無効地名を削除しました。", style="green")
    else:
        console.print(f"📋 {len(invalid_places)}件の地名が削除対象です。", style="blue")
        
        if invalid_places:
            table = Table(title="削除対象の地名")
            table.add_column("地名", style="cyan")
            table.add_column("文脈", style="blue")
            table.add_column("信頼度", style="yellow")
            table.add_column("理由", style="red")
            
            for place in invalid_places[:10]:  # 最初の10件のみ表示
                table.add_row(
                    place['name'],
                    place['context'][:50] + "..." if len(place['context']) > 50 else place['context'],
                    f"{place['confidence']:.2f}",
                    place['reasoning'][:50] + "..." if len(place['reasoning']) > 50 else place['reasoning']
                )
            
            console.print(table)
            
            if not apply:
                console.print("\n💡 実際に削除するには --apply オプションを使用してください。", style="blue")
                console.print("⚠️ 削除は元に戻せません。慎重に実行してください。", style="yellow")

def _apply_context_cleaning(invalid_places, database_path):
    """文脈クリーニングを適用"""
    try:
        from ..ai.context.context_cleaner import ContextCleaner
        cleaner = ContextCleaner(database_path)
        
        for place in invalid_places:
            cleaner.remove_place(place['name'])
        
        return True
    except Exception as e:
        console.print(f"❌ 文脈クリーニング適用エラー: {str(e)}", style="red")
        return False

def _display_enhanced_context_statistics(analysis_results):
    """拡張文脈統計を表示"""
    console.print(Panel(
        f"📊 拡張文脈統計\n"
        f"総地名数: {analysis_results['total_places']}\n"
        f"文脈一致: {analysis_results['context_match']}\n"
        f"文脈不一致: {analysis_results['context_mismatch']}\n"
        f"平均信頼度: {analysis_results['average_confidence']:.2f}",
        title="拡張文脈統計",
        border_style="green"
    ))

def _export_context_analysis_results(analysis_results, output_path):
    """文脈分析結果をエクスポート"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2) 