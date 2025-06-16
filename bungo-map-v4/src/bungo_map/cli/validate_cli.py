import json
import yaml
import click
from pathlib import Path
from jsonschema import validate as jsonschema_validate
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from bungo_map.database.manager import DatabaseManager
from bungo_map.database.schema_manager import SchemaManager

console = Console()

def load_json_file(file_path):
    """JSONファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[red]エラー: ファイルの読み込みに失敗しました: {str(e)}[/red]")
        raise click.Abort()

def load_yaml_file(file_path):
    """YAMLファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]エラー: ファイルの読み込みに失敗しました: {str(e)}[/red]")
        raise click.Abort()

def validate_data_against_schema(data, schema):
    """データをスキーマに対して検証"""
    try:
        jsonschema_validate(instance=data, schema=schema)
        return True, []
    except Exception as e:
        return False, [str(e)]

def check_data_consistency(data, rules):
    """データの一貫性をチェック"""
    issues = []
    
    for rule in rules['rules']:
        if rule['type'] == 'reference_check':
            # 参照チェック
            source_values = set()
            for item in data['texts']:
                source_values.update(item['places'])
            
            target_values = {place['name'] for place in data['places']}
            missing_refs = source_values - target_values
            
            if missing_refs:
                issues.append({
                    'rule': rule['name'],
                    'severity': rule['severity'],
                    'message': f"参照エラー: {missing_refs} がplacesに存在しません"
                })
        
        elif rule['type'] == 'range_check':
            # 範囲チェック
            if 'coordinates' in rule['field']:
                for place in data['places']:
                    coords = place['coordinates']
                    if not (-90 <= coords['latitude'] <= 90):
                        issues.append({
                            'rule': rule['name'],
                            'severity': rule['severity'],
                            'message': f"緯度が範囲外: {coords['latitude']}"
                        })
                    if not (-180 <= coords['longitude'] <= 180):
                        issues.append({
                            'rule': rule['name'],
                            'severity': rule['severity'],
                            'message': f"経度が範囲外: {coords['longitude']}"
                        })
            elif 'confidence' in rule['field']:
                for place in data['places']:
                    conf = place['metadata']['confidence']
                    if not (0 <= conf <= 1):
                        issues.append({
                            'rule': rule['name'],
                            'severity': rule['severity'],
                            'message': f"信頼度が範囲外: {conf}"
                        })
    
    return issues

@click.group()
def cli():
    """データ検証コマンド群"""
    pass

@cli.command()
@click.option('--db-path', required=True, help='データベースファイルのパス')
@click.option('--strict', is_flag=True, help='厳格モードで検証')
@click.option('--output', '-o', help='検証レポートの出力先')
def validate_data(db_path, strict, output):
    """データの検証を実行"""
    import sys
    try:
        # データベース接続
        db_manager = DatabaseManager(db_path)
        schema_manager = SchemaManager(db_path)
        # スキーマ検証
        if not schema_manager.verify_schema():
            console.print("[red]スキーマ検証に失敗しました[/red]")
            sys.exit(1)
        # データ検証
        issues = []
        # 地名データの検証
        places = db_manager.get_all_places()
        for place in places:
            if not place.get('place_name'):
                issues.append({'severity': 'error','message': f"地名が設定されていません: {place}"})
            confidence = place.get('confidence', 0)
            if not (0 <= confidence <= 1):
                issues.append({'severity': 'error','message': f"信頼度が範囲外です: {confidence}"})
            place_type = place.get('place_type')
            valid_types = ['都道府県', '市区町村', '有名地名', '郡', '歴史地名']
            if place_type not in valid_types:
                issues.append({'severity': 'error','message': f"無効な地名タイプです: {place_type}"})
        # 結果の表示
        if issues:
            table = Table(title="検証結果")
            table.add_column("重要度", style="cyan")
            table.add_column("メッセージ", style="yellow")
            for issue in issues:
                severity = issue.get('severity', 'error')
                message = issue.get('message', '')
                table.add_row(severity, message)
            console.print(table)
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(issues, f, ensure_ascii=False, indent=2)
                console.print(f"[green]検証レポートを保存しました: {output}[/green]")
            if strict and any(issue.get('severity') == 'error' for issue in issues):
                sys.exit(1)
        else:
            console.print("[green]検証完了: 問題は見つかりませんでした[/green]")
    except Exception as e:
        console.print(f"[red]データベースに接続できません: {str(e)}[/red]")
        sys.exit(1)

@cli.command()
@click.option('--db-path', required=True, help='データベースファイルのパス')
def validate_schema(db_path):
    """スキーマの検証を実行"""
    console.print("[bold blue]スキーマ検証を開始[/bold blue]")
    
    try:
        schema_manager = SchemaManager(db_path)
        if schema_manager.verify_schema():
            console.print("[green]スキーマは有効です[/green]")
        else:
            console.print("[red]スキーマに問題があります[/red]")
            raise click.Abort()
    except Exception as e:
        console.print(f"[red]スキーマエラー: {str(e)}[/red]")
        raise click.Abort()

@cli.command()
@click.option('--db-path', required=True, help='データベースファイルのパス')
def validate_consistency(db_path):
    """データの一貫性を検証"""
    console.print("[bold blue]一貫性チェックを開始[/bold blue]")
    
    try:
        db_manager = DatabaseManager(db_path)
        issues = []
        
        # 地名の参照整合性チェック
        places = db_manager.get_all_places()
        place_names = {place['place_name'] for place in places}
        
        # 文書内の地名参照チェック
        sentences = db_manager.get_all_sentences()
        for sentence in sentences:
            for place_ref in sentence.get('places', []):
                if place_ref not in place_names:
                    issues.append({
                        'rule': 'reference_check',
                        'severity': 'error',
                        'message': f"存在しない地名への参照: {place_ref}"
                    })
        
        # 結果の表示
        if issues:
            table = Table(title="一貫性チェック結果")
            table.add_column("ルール", style="cyan")
            table.add_column("重要度", style="yellow")
            table.add_column("メッセージ", style="red")
            
            for issue in issues:
                table.add_row(
                    issue.get('rule', ''),
                    issue.get('severity', 'error'),
                    issue.get('message', '')
                )
            
            console.print(table)
        else:
            console.print("[green]一貫性チェック完了: 問題は見つかりませんでした[/green]")
            
    except Exception as e:
        console.print(f"[red]データベースに接続できません: {str(e)}[/red]")
        raise click.Abort()

if __name__ == '__main__':
    cli() 