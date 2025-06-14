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
@click.option('--limit', type=int, help='分析する地名数の上限')
@click.option('--confidence', type=float, default=0.7, help='信頼度の閾値')
@click.option('--save/--no-save', default=True, help='分析結果をデータベースに保存')
def analyze(limit: int, confidence: float, save: bool):
    """地名データ品質分析（信頼度・タイプ分析）"""
    db_path = get_database_path()
    cleaner = PlaceCleaner(db_path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("地名データを分析中...", total=None)
        
        try:
            analyses = cleaner.analyze_all_places(
                limit=limit,
                confidence_threshold=confidence,
                save_to_db=save
            )
            
            # 結果の表示
            table = Table(title="地名分析結果")
            table.add_column("地名", style="cyan")
            table.add_column("信頼度", style="green")
            table.add_column("タイプ", style="yellow")
            table.add_column("有効", style="magenta")
            table.add_column("正規化名", style="blue")
            
            for analysis in analyses:
                table.add_row(
                    analysis.place_name,
                    f"{analysis.confidence:.2f}",
                    analysis.place_type,
                    "✅" if analysis.is_valid else "❌",
                    analysis.normalized_name
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]エラーが発生しました: {str(e)}[/red]")
            raise click.Abort()

@ai.command()
@click.option('--limit', type=int, help='正規化する地名数の上限')
@click.option('--confidence', type=float, default=0.7, help='信頼度の閾値')
def normalize(limit: int, confidence: float):
    """地名正規化実行（漢字表記統一等）"""
    db_path = get_database_path()
    cleaner = PlaceCleaner(db_path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("地名を正規化中...", total=None)
        
        try:
            analyses = cleaner.analyze_all_places(
                limit=limit,
                confidence_threshold=confidence,
                save_to_db=True
            )
            
            # 結果の表示
            table = Table(title="地名正規化結果")
            table.add_column("元の地名", style="cyan")
            table.add_column("正規化名", style="green")
            table.add_column("信頼度", style="yellow")
            
            for analysis in analyses:
                if analysis.normalized_name != analysis.place_name:
                    table.add_row(
                        analysis.place_name,
                        analysis.normalized_name,
                        f"{analysis.confidence:.2f}"
                    )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]エラーが発生しました: {str(e)}[/red]")
            raise click.Abort()

@ai.command()
@click.option('--limit', type=int, help='クリーニングする地名数の上限')
@click.option('--confidence', type=float, default=0.3, help='削除する信頼度の閾値')
@click.option('--dry-run/--no-dry-run', default=True, help='実際の削除を行わず、対象のみ表示')
def clean(limit: int, confidence: float, dry_run: bool):
    """無効地名削除（低信頼度データ除去）"""
    db_path = get_database_path()
    cleaner = PlaceCleaner(db_path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("地名を分析中...", total=None)
        
        try:
            analyses = cleaner.analyze_all_places(limit=limit)
            result = cleaner.remove_invalid_places(
                analyses,
                confidence_threshold=confidence,
                dry_run=dry_run
            )
            
            if result["applied"]:
                console.print(f"[green]✅ {result['deleted_count']}件の地名を削除しました[/green]")
            else:
                console.print(f"[yellow]⚠️ 削除対象: {result['would_delete']}件[/yellow]")
                
                if result["candidates"]:
                    table = Table(title="削除候補")
                    table.add_column("地名", style="cyan")
                    table.add_column("信頼度", style="yellow")
                    table.add_column("理由", style="red")
                    
                    for candidate in result["candidates"]:
                        table.add_row(
                            candidate["name"],
                            f"{candidate['confidence']:.2f}",
                            candidate["reasoning"]
                        )
                    
                    console.print(table)
            
        except Exception as e:
            console.print(f"[red]エラーが発生しました: {str(e)}[/red]")
            raise click.Abort()

@ai.command()
@click.option('--limit', type=int, help='検証する地名数の上限')
def validate_extraction(limit: int):
    """地名抽出精度検証システム"""
    db_path = get_database_path()
    validator = ExtractionValidator(db_path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("地名抽出を検証中...", total=None)
        
        try:
            issues = validator.validate_all_extractions(limit=limit)
            
            if issues:
                table = Table(title="検証結果")
                table.add_column("地名", style="cyan")
                table.add_column("問題", style="red")
                table.add_column("重要度", style="yellow")
                table.add_column("提案", style="green")
                
                for issue in issues:
                    table.add_row(
                        issue.place_name,
                        issue.description,
                        issue.severity,
                        issue.suggestion
                    )
                
                console.print(table)
            else:
                console.print("[green]✅ 問題は見つかりませんでした[/green]")
            
        except Exception as e:
            console.print(f"[red]エラーが発生しました: {str(e)}[/red]")
            raise click.Abort()

@ai.command()
@click.option('--limit', type=int, help='分析する地名数の上限')
def analyze_context(limit: int):
    """文脈ベース地名分析"""
    db_path = get_database_path()
    cleaner = PlaceCleaner(db_path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("文脈を分析中...", total=None)
        
        try:
            analyses = cleaner.analyze_all_places(limit=limit)
            
            table = Table(title="文脈分析結果")
            table.add_column("地名", style="cyan")
            table.add_column("文脈タイプ", style="yellow")
            table.add_column("信頼度", style="green")
            table.add_column("推論", style="blue")
            
            for analysis in analyses:
                if hasattr(analysis, 'context_analysis'):
                    table.add_row(
                        analysis.place_name,
                        analysis.context_analysis.context_type,
                        f"{analysis.context_analysis.confidence:.2f}",
                        analysis.context_analysis.reasoning
                    )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]エラーが発生しました: {str(e)}[/red]")
            raise click.Abort()

@ai.command()
@click.option('--limit', type=int, help='クリーニングする地名数の上限')
@click.option('--confidence', type=float, default=0.3, help='削除する信頼度の閾値')
@click.option('--dry-run/--no-dry-run', default=True, help='実際の削除を行わず、対象のみ表示')
def clean_context(limit: int, confidence: float, dry_run: bool):
    """文脈判断による無効地名削除"""
    db_path = get_database_path()
    cleaner = PlaceCleaner(db_path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("文脈を分析中...", total=None)
        
        try:
            analyses = cleaner.analyze_all_places(limit=limit)
            result = cleaner.remove_invalid_places(
                analyses,
                confidence_threshold=confidence,
                dry_run=dry_run
            )
            
            if result["applied"]:
                console.print(f"[green]✅ {result['deleted_count']}件の地名を削除しました[/green]")
            else:
                console.print(f"[yellow]⚠️ 削除対象: {result['would_delete']}件[/yellow]")
                
                if result["candidates"]:
                    table = Table(title="削除候補")
                    table.add_column("地名", style="cyan")
                    table.add_column("信頼度", style="yellow")
                    table.add_column("理由", style="red")
                    
                    for candidate in result["candidates"]:
                        table.add_row(
                            candidate["name"],
                            f"{candidate['confidence']:.2f}",
                            candidate["reasoning"]
                        )
                    
                    console.print(table)
            
        except Exception as e:
            console.print(f"[red]エラーが発生しました: {str(e)}[/red]")
            raise click.Abort()

@ai.command()
def test_connection():
    """OpenAI API接続テスト"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            console.print("[red]❌ OpenAI APIキーが設定されていません[/red]")
            return
        
        cleaner = PlaceCleaner(get_database_path())
        result = cleaner.analyze_place_name("東京")
        
        if result:
            console.print("[green]✅ OpenAI API接続テスト成功[/green]")
            console.print(Panel(
                f"地名: {result['place_name']}\n"
                f"信頼度: {result['confidence']}\n"
                f"タイプ: {result['place_type']}\n"
                f"有効: {'✅' if result['is_valid'] else '❌'}\n"
                f"正規化名: {result['normalized_name']}",
                title="テスト結果"
            ))
        else:
            console.print("[red]❌ API応答が不正です[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ エラーが発生しました: {str(e)}[/red]")
        raise click.Abort()

if __name__ == '__main__':
    ai() 