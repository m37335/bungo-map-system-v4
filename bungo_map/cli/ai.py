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
        
        # 統計表示
        if not dry_run:
            stats = geocoder.get_geocoding_statistics()
            _display_geocoding_statistics(stats)
        
    except Exception as e:
        console.print(f"❌ ジオコーディングエラー: {str(e)}", style="red")

@ai.command()
@click.option('--limit', '-l', type=int, help='検証する地名数の上限')
@click.option('--severity', '-s', type=click.Choice(['high', 'medium', 'low', 'all']), default='all', help='表示する問題の重要度')
@click.option('--issue-type', '-t', type=click.Choice(['false_positive', 'context_mismatch', 'suspicious', 'all']), default='all', help='表示する問題のタイプ')
@click.option('--output', '-o', help='検証結果の出力ファイルパス')
def validate_extraction(limit, severity, issue_type, output):
    """🔍 地名抽出品質の検証"""
    
    database_path = get_database_path()
    if not Path(database_path).exists():
        console.print(f"❌ データベースが見つかりません: {database_path}", style="red")
        return
    
    try:
        from ..ai.validators.extraction_validator import ExtractionValidator
        validator = ExtractionValidator(database_path)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("地名抽出を検証中...", total=None)
            
            # 抽出検証実行
            issues = validator.validate_all_extractions(limit=limit)
            
            # 統計取得
            stats = validator.get_extraction_statistics()
            
            progress.update(task, description="検証完了")
    
        # フィルタリング
        filtered_issues = _filter_issues(issues, severity, issue_type)
        
        # 結果表示
        _display_extraction_statistics(stats)
        _display_validation_issues(filtered_issues, severity, issue_type)
        
        # ファイル出力
        if output:
            _export_validation_results(filtered_issues, stats, output)
            console.print(f"✅ 検証結果を保存しました: {output}", style="green")
        
    except Exception as e:
        console.print(f"❌ 検証エラー: {str(e)}", style="red")

@ai.command()
@click.option('--api-key', envvar='OPENAI_API_KEY', help='OpenAI APIキー')
def test_connection(api_key):
    """🔧 OpenAI API接続テスト"""
    
    if not api_key:
        console.print("❌ OpenAI APIキーが設定されていません。", style="red")
        return
    
    try:
        from ..ai.models.openai_client import OpenAIClient
        client = OpenAIClient(api_key)
        
        # テスト用の簡単な分析
        test_analysis = client.analyze_place_name("東京", "テスト用の文脈", "テスト作品", "テスト作者")
        
        console.print("✅ OpenAI API接続成功！", style="green")
        console.print(f"テスト結果: {test_analysis.place_name} - 信頼度: {test_analysis.confidence:.2f}")
        
    except Exception as e:
        console.print(f"❌ API接続エラー: {str(e)}", style="red")

@ai.command()
@click.option('--place-name', '-p', help='特定の地名を文脈分析（指定しない場合は疑わしい地名を自動選択）')
@click.option('--single-char', is_flag=True, help='一文字地名のみを対象にする')
@click.option('--limit', '-l', type=int, default=20, help='分析する地名数の上限')
@click.option('--output', '-o', help='分析結果の出力ファイルパス')
@click.option('--api-key', envvar='OPENAI_API_KEY', help='OpenAI APIキー')
def analyze_context(place_name, single_char, limit, output, api_key):
    """🔍 地名の文脈分析 - AI による詳細な文脈妥当性検証"""
    
    # APIキーのデバッグ出力
    console.print(f"🔍 文脈分析開始", style="blue")
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
    
    # データベースから文脈情報を取得
    import sqlite3
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("地名データを取得中...", total=None)
        
        # SQLクエリを構築
        if place_name:
            # 特定の地名を指定
            query = """
                SELECT DISTINCT p.place_name, p.sentence, p.before_text, p.after_text,
                       w.title as work_title, a.name as author, w.publication_year,
                       COUNT(*) as frequency
                FROM places p
                LEFT JOIN works w ON p.work_id = w.work_id
                LEFT JOIN authors a ON w.author_id = a.author_id
                WHERE p.place_name = ?
                GROUP BY p.place_name, p.sentence, w.title, a.name
                ORDER BY frequency DESC
                LIMIT ?
            """
            params = (place_name, limit)
        elif single_char:
            # 一文字地名のみ
            query = """
                SELECT DISTINCT p.place_name, p.sentence, p.before_text, p.after_text,
                       w.title as work_title, a.name as author, w.publication_year,
                       COUNT(*) as frequency
                FROM places p
                LEFT JOIN works w ON p.work_id = w.work_id
                LEFT JOIN authors a ON w.author_id = a.author_id
                WHERE LENGTH(p.place_name) = 1
                GROUP BY p.place_name, p.sentence, w.title, a.name
                ORDER BY frequency DESC
                LIMIT ?
            """
            params = (limit,)
        else:
            # 疑わしい地名（一文字または抽出回数が多い）
            query = """
                SELECT DISTINCT p.place_name, p.sentence, p.before_text, p.after_text,
                       w.title as work_title, a.name as author, w.publication_year,
                       COUNT(*) as frequency
                FROM places p
                LEFT JOIN works w ON p.work_id = w.work_id
                LEFT JOIN authors a ON w.author_id = a.author_id
                WHERE LENGTH(p.place_name) <= 2 OR 
                      p.place_name IN (
                          SELECT place_name FROM places 
                          GROUP BY place_name 
                          HAVING COUNT(*) > 5
                      )
                GROUP BY p.place_name, p.sentence, w.title, a.name
                ORDER BY frequency DESC
                LIMIT ?
            """
            params = (limit,)
        
        cursor = conn.execute(query, params)
        places_data = []
        for row in cursor:
            places_data.append({
                'place_name': row['place_name'],
                'sentence': row['sentence'] or '',
                'before_text': row['before_text'] or '',
                'after_text': row['after_text'] or '',
                'work_title': row['work_title'] or '',
                'author': row['author'] or '',
                'work_year': row['publication_year'],
                'frequency': row['frequency']
            })
        
        progress.update(task, description=f"文脈分析を実行中... ({len(places_data)}件)")
        
        # PlaceCleanerで文脈分析を実行
        cleaner = PlaceCleaner(database_path, api_key)
        analysis_results = []
        
        for i, place_data in enumerate(places_data):
            try:
                result = cleaner.analyze_with_context(place_data, include_context=True)
                result['frequency'] = place_data['frequency']
                result['sentence'] = place_data['sentence']
                analysis_results.append(result)
                
                progress.update(task, description=f"文脈分析中... ({i+1}/{len(places_data)})")
                
            except Exception as e:
                console.print(f"⚠️ 分析エラー [{place_data['place_name']}]: {str(e)}", style="yellow")
                continue
    
    conn.close()
    
    if not analysis_results:
        console.print("⚠️ 分析対象の地名が見つかりませんでした。", style="yellow")
        return
    
    # 結果の表示
    _display_context_analysis_summary(analysis_results)
    _display_context_analysis_details(analysis_results)
    
    # ファイル出力
    if output:
        _export_context_analysis_results(analysis_results, output)
        console.print(f"✅ 文脈分析結果を保存しました: {output}", style="green")

@ai.command()
@click.option('--confidence-threshold', '-t', type=float, default=0.8, help='無効判定する信頼度の閾値')
@click.option('--dry-run', is_flag=True, default=True, help='実際の削除は行わず、対象のみ表示')
@click.option('--apply', is_flag=True, help='実際にデータベースから削除')
@click.option('--api-key', envvar='OPENAI_API_KEY', help='OpenAI APIキー')
def clean_context(confidence_threshold, dry_run, apply, api_key):
    """🧹 文脈分析に基づく地名クリーニング - 誤抽出された地名を削除"""
    
    if not api_key:
        console.print("❌ OpenAI APIキーが設定されていません。", style="red")
        console.print("環境変数 OPENAI_API_KEY を設定するか、--api-key オプションを使用してください。")
        return
    
    database_path = get_database_path()
    if not Path(database_path).exists():
        console.print(f"❌ データベースが見つかりません: {database_path}", style="red")
        return
    
    # applyフラグが指定された場合はdry_runを無効化
    if apply:
        dry_run = False
    
    import sqlite3
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("疑わしい地名を取得中...", total=None)
        
        # 疑わしい地名（一文字 + 出現頻度の高い地名）を取得
        query = """
            SELECT DISTINCT p.place_name, p.sentence, p.before_text, p.after_text,
                   COUNT(*) as frequency
            FROM places p
            WHERE LENGTH(p.place_name) <= 2 OR 
                  p.place_name IN (
                      SELECT place_name FROM places 
                      GROUP BY place_name 
                      HAVING COUNT(*) > 10
                  )
            GROUP BY p.place_name, p.sentence
            ORDER BY frequency DESC
            LIMIT 50
        """
        
        cursor = conn.execute(query)
        places_data = []
        for row in cursor:
            places_data.append({
                'place_name': row['place_name'],
                'sentence': row['sentence'] or '',
                'before_text': row['before_text'] or '',
                'after_text': row['after_text'] or '',
                'frequency': row['frequency']
            })
        
        progress.update(task, description=f"文脈分析を実行中... ({len(places_data)}件)")
        
        # PlaceCleanerで文脈分析を実行
        cleaner = PlaceCleaner(database_path, api_key)
        invalid_places = []
        
        for i, place_data in enumerate(places_data):
            try:
                result = cleaner.analyze_with_context(place_data, include_context=True)
                
                # 無効と判定され、信頼度が閾値以上の場合は削除対象
                if (not result['is_valid'] and 
                    result.get('context_analysis', {}).get('confidence', 0) >= confidence_threshold):
                    invalid_places.append({
                        'place_name': result['place_name'],
                        'context_type': result.get('context_analysis', {}).get('context_type', 'unknown'),
                        'confidence': result.get('context_analysis', {}).get('confidence', 0),
                        'reasoning': result.get('context_analysis', {}).get('reasoning', ''),
                        'alternative_interpretation': result.get('context_analysis', {}).get('alternative_interpretation', ''),
                        'frequency': place_data['frequency']
                    })
                
                progress.update(task, description=f"文脈分析中... ({i+1}/{len(places_data)})")
                
            except Exception as e:
                console.print(f"⚠️ 分析エラー [{place_data['place_name']}]: {str(e)}", style="yellow")
                continue
    
    conn.close()
    
    if not invalid_places:
        console.print("✅ 削除対象の誤抽出地名は見つかりませんでした。", style="green")
        return
    
    # 結果表示
    _display_context_cleaning_results(invalid_places, dry_run, apply)
    
    # 実際の削除処理
    if not dry_run:
        _apply_context_cleaning(invalid_places, database_path)

def _display_analysis_summary(report):
    """分析サマリーを表示"""
    summary = report['summary']
    
    table = Table(title="📊 地名分析サマリー")
    table.add_column("項目", style="cyan")
    table.add_column("件数", style="green")
    table.add_column("割合", style="yellow")
    
    table.add_row("総地名数", str(summary['total_places']), "-")
    table.add_row("有効地名", str(summary['valid_places']), f"{summary['validity_rate']:.1%}")
    table.add_row("無効地名", str(summary['invalid_places']), f"{1-summary['validity_rate']:.1%}")
    table.add_row("正規化対象", str(report['normalization_candidates']), "-")
    table.add_row("問題地名", str(report['problematic_places']), "-")
    
    console.print(table)

def _display_confidence_distribution(report):
    """信頼度分布を表示"""
    dist = report['confidence_distribution']
    
    table = Table(title="🎯 信頼度分布")
    table.add_column("信頼度", style="cyan")
    table.add_column("件数", style="green")
    
    for range_name, count in dist.items():
        table.add_row(range_name, str(count))
    
    console.print(table)

def _display_type_distribution(report):
    """地名タイプ分布を表示"""
    types = report['type_distribution']
    
    table = Table(title="🏘️ 地名タイプ分布")
    table.add_column("タイプ", style="cyan")
    table.add_column("件数", style="green")
    
    for place_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
        table.add_row(place_type, str(count))
    
    console.print(table)

def _display_improvement_suggestions(report):
    """改善提案を表示"""
    suggestions = report['improvement_suggestions']
    
    if suggestions:
        panel_content = "\n".join([f"• {suggestion}" for suggestion in suggestions])
        console.print(Panel(panel_content, title="💡 改善提案", border_style="blue"))

def _display_detailed_results(analyses):
    """個別の地名分析結果を詳細表示"""
    console.print("\n")
    
    table = Table(title="📍 個別地名分析結果")
    table.add_column("地名", style="cyan", width=15)
    table.add_column("信頼度", style="green", justify="center", width=8)
    table.add_column("タイプ", style="blue", width=10)
    table.add_column("判定", style="yellow", width=8)
    table.add_column("正規化", style="magenta", width=15)
    table.add_column("理由", style="white", width=50)
    
    for analysis in analyses[:50]:  # 最初の50件のみ表示
        # 判定の色分け
        if analysis.confidence >= 0.8:
            validity = "[green]✅ 有効[/green]"
        elif analysis.confidence >= 0.5:
            validity = "[yellow]⚠️ 注意[/yellow]"
        else:
            validity = "[red]❌ 無効[/red]"
        
        # 理由を短縮
        reasoning = analysis.reasoning[:45] + "..." if len(analysis.reasoning) > 45 else analysis.reasoning
        
        # 正規化名の表示
        normalized = analysis.normalized_name if analysis.normalized_name != analysis.place_name else "-"
        
        table.add_row(
            analysis.place_name,
            f"{analysis.confidence:.2f}",
            analysis.place_type,
            validity,
            normalized,
            reasoning
        )
    
    console.print(table)
    
    if len(analyses) > 50:
        console.print(f"\n💡 {len(analyses)}件中最初の50件を表示しました。完全な結果は --output オプションでファイル出力してください。", style="blue")

def _display_geocoding_results(result, dry_run, apply):
    """ジオコーディング結果を表示"""
    console.print(f"\n📍 ジオコーディング結果")
    
    # サマリー表示
    table = Table(title="🌍 ジオコーディングサマリー")
    table.add_column("項目", style="cyan")
    table.add_column("件数", style="green")
    
    table.add_row("処理対象", str(result['total_processed']))
    table.add_row("成功", str(result['successful']))
    table.add_row("失敗", str(result['failed']))
    table.add_row("スキップ", str(result['skipped']))
    
    console.print(table)
    
    # 成功した結果の表示
    if result['results']:
        result_table = Table(title="📍 ジオコーディング成功地名")
        result_table.add_column("地名", style="cyan", width=15)
        result_table.add_column("緯度", style="green", width=10)
        result_table.add_column("経度", style="green", width=10)
        result_table.add_column("精度", style="yellow", width=8)
        result_table.add_column("ソース", style="blue", width=10)
        result_table.add_column("住所", style="white", width=40)
        
        for geo_result in result['results'][:20]:  # 最初の20件のみ表示
            result_table.add_row(
                geo_result['place_name'],
                f"{geo_result['latitude']:.6f}",
                f"{geo_result['longitude']:.6f}",
                geo_result['accuracy'],
                geo_result['provider'],
                geo_result['address'][:35] + "..." if len(geo_result['address']) > 35 else geo_result['address']
            )
        
        console.print(result_table)
        
        if len(result['results']) > 20:
            console.print(f"\n💡 {len(result['results'])}件中最初の20件を表示しました。", style="blue")
    
    # 適用に関するメッセージ
    if dry_run and not apply:
        console.print("\n💡 実際にデータベースを更新するには --apply オプションを使用してください。", style="blue")
    elif not dry_run:
        console.print(f"\n✅ {result['successful']}件の地名の座標をデータベースに保存しました。", style="green")

def _display_geocoding_statistics(stats):
    """ジオコーディング統計を表示"""
    summary = stats['summary']
    
    console.print(f"\n📊 ジオコーディング統計")
    
    # 全体統計
    overall_table = Table(title="🌏 全体統計")
    overall_table.add_column("項目", style="cyan")
    overall_table.add_column("値", style="green")
    
    overall_table.add_row("総地名数", str(summary['total_places']))
    overall_table.add_row("ジオコーディング済み", str(summary['geocoded_places']))
    overall_table.add_row("ジオコーディング率", f"{summary['geocoding_rate']:.1f}%")
    overall_table.add_row("平均AI信頼度", f"{summary['avg_ai_confidence']:.2f}")
    
    console.print(overall_table)
    
    # ステータス別統計
    if len(stats) > 1:  # summaryのみでない場合
        status_table = Table(title="📈 ステータス別統計")
        status_table.add_column("ステータス", style="cyan")
        status_table.add_column("件数", style="green")
        status_table.add_column("平均信頼度", style="yellow")
        
        for status, data in stats.items():
            if status != 'summary':
                status_table.add_row(
                    status,
                    str(data['count']),
                    f"{data['avg_confidence']:.2f}"
                )
        
        console.print(status_table)

def _filter_issues(issues, severity_filter, type_filter):
    """問題をフィルタリング"""
    filtered = issues
    
    if severity_filter != 'all':
        filtered = [issue for issue in filtered if issue.severity == severity_filter]
    
    if type_filter != 'all':
        filtered = [issue for issue in filtered if issue.issue_type == type_filter]
    
    return filtered

def _display_extraction_statistics(stats):
    """抽出統計を表示"""
    console.print(f"\n📊 地名抽出統計")
    
    # 基本統計
    basic_table = Table(title="📈 基本統計")
    basic_table.add_column("項目", style="cyan")
    basic_table.add_column("値", style="green")
    
    basic_table.add_row("総地名数", str(stats.total_places))
    basic_table.add_row("ユニーク地名数", str(stats.unique_places))
    basic_table.add_row("重複率", f"{((stats.total_places - stats.unique_places) / stats.total_places * 100):.1f}%")
    basic_table.add_row("平均信頼度", f"{stats.avg_confidence:.2f}")
    
    console.print(basic_table)
    
    # 抽出方法別統計
    if stats.extraction_methods:
        method_table = Table(title="🔧 抽出方法別統計")
        method_table.add_column("方法", style="cyan")
        method_table.add_column("件数", style="green")
        method_table.add_column("割合", style="yellow")
        
        total = sum(stats.extraction_methods.values())
        for method, count in sorted(stats.extraction_methods.items(), key=lambda x: x[1], reverse=True):
            method_table.add_row(
                method or '不明',
                str(count),
                f"{(count / total * 100):.1f}%"
            )
        
        console.print(method_table)
    
    # 疑わしいパターン
    if stats.suspicious_patterns:
        console.print(f"\n⚠️ 疑わしいパターン:")
        for pattern in stats.suspicious_patterns:
            console.print(f"  • {pattern}", style="yellow")

def _display_validation_issues(issues, severity_filter, type_filter):
    """検証問題を表示"""
    if not issues:
        console.print("\n✅ 検証問題は見つかりませんでした。", style="green")
        return
    
    console.print(f"\n⚠️ 検証問題: {len(issues)}件")
    
    # 問題サマリー
    issue_types = {}
    severities = {}
    
    for issue in issues:
        issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1
        severities[issue.severity] = severities.get(issue.severity, 0) + 1
    
    summary_table = Table(title="🔍 問題サマリー")
    summary_table.add_column("分類", style="cyan")
    summary_table.add_column("件数", style="green")
    
    for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
        summary_table.add_row(issue_type, str(count))
    
    console.print(summary_table)
    
    # 重要度別サマリー
    severity_table = Table(title="📊 重要度別")
    severity_table.add_column("重要度", style="cyan")
    severity_table.add_column("件数", style="green")
    
    for severity in ['high', 'medium', 'low']:
        if severity in severities:
            severity_table.add_row(severity, str(severities[severity]))
    
    console.print(severity_table)
    
    # 詳細問題リスト（最初の20件）
    detail_table = Table(title="🔎 詳細問題リスト")
    detail_table.add_column("地名", style="cyan", width=15)
    detail_table.add_column("問題", style="red", width=15)
    detail_table.add_column("重要度", style="yellow", width=8)
    detail_table.add_column("説明", style="white", width=25)
    detail_table.add_column("文脈", style="blue", width=30)
    
    for issue in issues[:20]:
        # 重要度に応じた色分け
        severity_color = {
            'high': '[red]🔴 高[/red]',
            'medium': '[yellow]🟡 中[/yellow]',
            'low': '[green]🟢 低[/green]'
        }.get(issue.severity, issue.severity)
        
        # 文脈の短縮
        context = issue.context[:25] + "..." if len(issue.context) > 25 else issue.context
        
        detail_table.add_row(
            issue.place_name,
            issue.issue_type,
            severity_color,
            issue.description,
            context
        )
    
    console.print(detail_table)
    
    if len(issues) > 20:
        console.print(f"\n💡 {len(issues)}件中最初の20件を表示しました。全結果は --output オプションでファイル出力してください。", style="blue")

def _export_validation_results(issues, stats, output_path):
    """検証結果をエクスポート"""
    import json
    
    result = {
        "statistics": {
            "total_places": stats.total_places,
            "unique_places": stats.unique_places,
            "avg_confidence": stats.avg_confidence,
            "extraction_methods": stats.extraction_methods,
            "suspicious_patterns": stats.suspicious_patterns
        },
        "issues": [
            {
                "place_id": issue.place_id,
                "place_name": issue.place_name,
                "issue_type": issue.issue_type,
                "severity": issue.severity,
                "description": issue.description,
                "context": issue.context,
                "suggestion": issue.suggestion
            }
            for issue in issues
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def _display_context_analysis_summary(analysis_results):
    """文脈分析サマリーを表示"""
    summary = {
        "total_places": len(analysis_results),
        "valid_places": sum(1 for result in analysis_results if result['is_valid']),
        "invalid_places": sum(1 for result in analysis_results if not result['is_valid']),
        "validity_rate": sum(1 for result in analysis_results if result['is_valid']) / len(analysis_results) * 100
    }
    
    table = Table(title="📊 地名文脈分析サマリー")
    table.add_column("項目", style="cyan")
    table.add_column("件数", style="green")
    table.add_column("割合", style="yellow")
    
    table.add_row("総地名数", str(summary['total_places']))
    table.add_row("有効地名", str(summary['valid_places']))
    table.add_row("無効地名", str(summary['invalid_places']))
    table.add_row("有効率", f"{summary['validity_rate']:.1f}%")
    
    console.print(table)

def _display_context_analysis_details(analysis_results):
    """個別の地名文脈分析結果を詳細表示"""
    console.print("\n")
    
    table = Table(title="📍 個別地名文脈分析結果（拡張版）")
    table.add_column("地名", style="cyan", width=10)
    table.add_column("有効性", style="green", justify="center", width=8)
    table.add_column("作品", style="blue", width=15)
    table.add_column("作者", style="magenta", width=12)
    table.add_column("文脈", style="yellow", width=12)
    table.add_column("理由", style="white", width=40)
    
    for result in analysis_results[:30]:  # 最初の30件のみ表示
        # 有効性の色分け
        validity = "[green]✅ 有効[/green]" if result['is_valid'] else "[red]❌ 無効[/red]"
        
        # 理由を短縮
        reasoning = result['reasoning'][:35] + "..." if len(result['reasoning']) > 35 else result['reasoning']
        
        # 文脈情報の取得
        context_type = result.get('context_analysis', {}).get('context_type', result['place_type'])
        
        # 作品・作者情報の取得
        work_title = result.get('work_title', '不明')[:12] + "..." if len(result.get('work_title', '')) > 12 else result.get('work_title', '不明')
        author = result.get('author', '不明')[:10] + "..." if len(result.get('author', '')) > 10 else result.get('author', '不明')
        
        table.add_row(
            result['place_name'],
            validity,
            work_title,
            author,
            context_type,
            reasoning
        )
    
    console.print(table)
    
    if len(analysis_results) > 30:
        console.print(f"\n💡 {len(analysis_results)}件中最初の30件を表示しました。完全な結果は --output オプションでファイル出力してください。", style="blue")
    
    # 拡張統計情報の表示
    _display_enhanced_context_statistics(analysis_results)

def _display_context_cleaning_results(invalid_places, dry_run, apply):
    """文脈分析に基づく地名クリーニング結果を表示"""
    console.print(f"\n📍 文脈分析に基づく地名クリーニング結果")
    
    # サマリー表示
    table = Table(title="🧹 文脈分析に基づく地名クリーニングサマリー")
    table.add_column("項目", style="cyan")
    table.add_column("件数", style="green")
    
    table.add_row("処理対象", str(len(invalid_places)))
    table.add_row("削除対象", str(len(invalid_places)))
    
    console.print(table)
    
    # 削除対象の表示
    if invalid_places:
        invalid_table = Table(title="📋 削除対象の誤抽出地名")
        invalid_table.add_column("地名", style="cyan")
        invalid_table.add_column("信頼度", style="yellow")
        invalid_table.add_column("理由", style="red")
        
        for place in invalid_places[:20]:  # 最初の20件のみ表示
            invalid_table.add_row(
                place['place_name'],
                f"{place['confidence']:.2f}",
                place['reasoning'][:50] + "..." if len(place['reasoning']) > 50 else place['reasoning']
            )
        
        console.print(invalid_table)
        
        if len(invalid_places) > 20:
            console.print(f"\n💡 {len(invalid_places)}件中最初の20件を表示しました。全結果は --output オプションでファイル出力してください。", style="blue")
    
    # 適用に関するメッセージ
    if dry_run and not apply:
        console.print("\n💡 実際にデータベースを更新するには --apply オプションを使用してください。", style="blue")
    elif not dry_run:
        console.print(f"\n✅ {len(invalid_places)}件の誤抽出地名を削除しました。", style="green")

def _apply_context_cleaning(invalid_places, database_path):
    """文脈分析に基づく地名クリーニングを実行"""
    import sqlite3
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("誤抽出地名を削除中...", total=None)
        
        for i, place in enumerate(invalid_places):
            try:
                # SQLクエリを構築
                query = """
                    DELETE FROM places
                    WHERE place_name = ?
                """
                params = (place['place_name'],)
                
                conn.execute(query, params)
                
                progress.update(task, description=f"削除中... ({i+1}/{len(invalid_places)})")
                
            except Exception as e:
                console.print(f"⚠️ 削除エラー [{place['place_name']}]: {str(e)}", style="yellow")
                continue
    
    conn.commit()
    conn.close()

def _display_enhanced_context_statistics(analysis_results):
    """拡張文脈分析統計を表示"""
    if not analysis_results:
        return
    
    # 作者別統計
    author_stats = {}
    context_type_stats = {}
    work_stats = {}
    
    for result in analysis_results:
        author = result.get('author', '不明')
        work = result.get('work_title', '不明')
        context_type = result.get('context_analysis', {}).get('context_type', 'unknown')
        is_valid = result.get('is_valid', True)
        
        # 作者別統計
        if author not in author_stats:
            author_stats[author] = {'total': 0, 'valid': 0, 'invalid': 0}
        author_stats[author]['total'] += 1
        if is_valid:
            author_stats[author]['valid'] += 1
        else:
            author_stats[author]['invalid'] += 1
        
        # 文脈タイプ別統計
        if context_type not in context_type_stats:
            context_type_stats[context_type] = 0
        context_type_stats[context_type] += 1
        
        # 作品別統計
        if work not in work_stats:
            work_stats[work] = {'total': 0, 'valid': 0}
        work_stats[work]['total'] += 1
        if is_valid:
            work_stats[work]['valid'] += 1
    
    # 作者別統計表示
    if len(author_stats) > 1:
        console.print("\n📚 作者別地名有効性統計")
        author_table = Table()
        author_table.add_column("作者", style="cyan")
        author_table.add_column("総数", style="white")
        author_table.add_column("有効", style="green")
        author_table.add_column("無効", style="red")
        author_table.add_column("有効率", style="yellow")
        
        for author, stats in sorted(author_stats.items(), key=lambda x: x[1]['total'], reverse=True)[:10]:
            if author != '不明':
                valid_rate = (stats['valid'] / stats['total'] * 100) if stats['total'] > 0 else 0
                author_table.add_row(
                    author[:15],
                    str(stats['total']),
                    str(stats['valid']),
                    str(stats['invalid']),
                    f"{valid_rate:.1f}%"
                )
        
        console.print(author_table)
    
    # 文脈タイプ別統計表示
    console.print("\n🔍 文脈タイプ別統計")
    context_table = Table()
    context_table.add_column("文脈タイプ", style="cyan")
    context_table.add_column("件数", style="white")
    context_table.add_column("割合", style="yellow")
    
    total_contexts = sum(context_type_stats.values())
    for context_type, count in sorted(context_type_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_contexts * 100) if total_contexts > 0 else 0
        context_table.add_row(
            context_type,
            str(count),
            f"{percentage:.1f}%"
        )
    
    console.print(context_table)

def _export_context_analysis_results(analysis_results, output_path):
    """拡張文脈分析結果をエクスポート"""
    import json
    
    result = {
        "analysis_results": [
            {
                "place_name": result['place_name'],
                "is_valid": result['is_valid'],
                "place_type": result['place_type'],
                "reasoning": result['reasoning'],
                "context_analysis": result.get('context_analysis', {}),
                "sentence": result.get('sentence', ''),
                "work_title": result.get('work_title', ''),
                "author": result.get('author', ''),
                "work_year": result.get('work_year', None),
                "frequency": result.get('frequency', 0)
            }
            for result in analysis_results
        ],
        "summary": {
            "total_analyzed": len(analysis_results),
            "valid_places": sum(1 for r in analysis_results if r['is_valid']),
            "invalid_places": sum(1 for r in analysis_results if not r['is_valid']),
            "unique_authors": len(set(r.get('author', '不明') for r in analysis_results)),
            "unique_works": len(set(r.get('work_title', '不明') for r in analysis_results))
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    ai() 