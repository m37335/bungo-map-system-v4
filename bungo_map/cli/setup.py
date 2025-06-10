"""
初期セットアップCLI
APIキー設定とシステム初期化
"""

import os
import getpass
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()

@click.group()
def setup():
    """🔧 初期セットアップ"""
    pass

@setup.command()
@click.option('--interactive', '-i', is_flag=True, help='対話式セットアップ')
@click.option('--api-key', help='OpenAI APIキーを直接指定')
@click.option('--user-config', is_flag=True, help='ユーザーディレクトリに設定ファイルを作成')
def init(interactive, api_key, user_config):
    """🚀 システム初期化"""
    
    console.print(Panel.fit(
        "🌟 文豪地図システム v3.0 初期セットアップ",
        style="bold blue"
    ))
    
    if interactive:
        _interactive_setup()
    elif api_key:
        _quick_setup(api_key, user_config)
    else:
        _show_setup_options()

@setup.command()
def check():
    """✅ 設定状況の確認"""
    from ..utils.config import config
    
    console.print("🔍 設定状況チェック\n")
    
    # OpenAI API
    if config.is_api_key_configured():
        console.print("✅ OpenAI APIキー: 設定済み", style="green")
        # APIキーの最初の数文字のみ表示
        masked_key = f"{config.get('OPENAI_API_KEY')[:8]}..."
        console.print(f"   キー: {masked_key}")
    else:
        console.print("❌ OpenAI APIキー: 未設定", style="red")
    
    # データベース
    from ..utils.database_utils import get_database_path
    db_path = get_database_path()
    if Path(db_path).exists():
        console.print(f"✅ データベース: {db_path}", style="green")
    else:
        console.print(f"⚠️ データベース: {db_path} (未作成)", style="yellow")
    
    # 環境変数
    env_sources = []
    if Path('.env').exists():
        env_sources.append('.env (プロジェクト)')
    if Path.home().joinpath('.bungo_map', '.env').exists():
        env_sources.append('~/.bungo_map/.env (ユーザー)')
    
    if env_sources:
        console.print(f"📝 設定ファイル: {', '.join(env_sources)}", style="blue")
    else:
        console.print("📝 設定ファイル: なし", style="yellow")

@setup.command()
@click.option('--backup', is_flag=True, help='既存設定をバックアップ')
def reset(backup):
    """🔄 設定リセット"""
    
    if backup:
        _backup_existing_config()
    
    if Confirm.ask("設定をリセットしますか？"):
        _reset_configuration()
        console.print("✅ 設定をリセットしました", style="green")

def _interactive_setup():
    """対話式セットアップ"""
    console.print("📝 対話式セットアップを開始します\n")
    
    # OpenAI APIキー入力
    while True:
        api_key = Prompt.ask(
            "OpenAI APIキーを入力してください",
            password=True
        )
        
        if api_key and len(api_key) > 20:  # 基本的な検証
            break
        else:
            console.print("❌ 有効なAPIキーを入力してください", style="red")
    
    # 保存場所選択
    save_location = Prompt.ask(
        "設定の保存場所を選択してください",
        choices=["project", "user", "env"],
        default="user"
    )
    
    # 設定保存
    if save_location == "project":
        _save_to_project_env(api_key)
    elif save_location == "user":
        _save_to_user_config(api_key)
    else:
        _show_env_instructions(api_key)
    
    console.print("✅ セットアップ完了！", style="green")
    console.print("テスト実行: python main.py ai test-connection")

def _quick_setup(api_key: str, user_config: bool):
    """クイックセットアップ"""
    if user_config:
        _save_to_user_config(api_key)
    else:
        _save_to_project_env(api_key)
    
    console.print("✅ APIキーを設定しました", style="green")

def _show_setup_options():
    """セットアップオプションを表示"""
    console.print(Panel(
        """セットアップ方法を選択してください:

🔧 対話式セットアップ:
  python main.py setup init --interactive

⚡ クイックセットアップ:
  python main.py setup init --api-key YOUR_KEY --user-config

📋 手動セットアップ:
  1. cp env.example .env
  2. .env ファイルを編集
  3. python main.py setup check

🔍 設定確認:
  python main.py setup check""",
        title="セットアップオプション",
        border_style="blue"
    ))

def _save_to_project_env(api_key: str):
    """プロジェクトの.envファイルに保存"""
    env_file = Path('.env')
    
    if not Path('env.example').exists():
        console.print("❌ env.example が見つかりません", style="red")
        return
    
    # テンプレートをコピー
    if not env_file.exists():
        env_content = Path('env.example').read_text()
    else:
        env_content = env_file.read_text()
    
    # APIキーを置換
    env_content = env_content.replace(
        'OPENAI_API_KEY=your_openai_api_key_here',
        f'OPENAI_API_KEY={api_key}'
    )
    
    env_file.write_text(env_content)
    console.print(f"✅ プロジェクト設定ファイルに保存: {env_file}", style="green")

def _save_to_user_config(api_key: str):
    """ユーザーディレクトリに保存"""
    from ..utils.config import config
    env_file_path = config.create_user_env_file()
    
    # APIキーを設定
    env_file = Path(env_file_path)
    content = env_file.read_text()
    content = content.replace(
        'OPENAI_API_KEY=your_openai_api_key_here',
        f'OPENAI_API_KEY={api_key}'
    )
    env_file.write_text(content)
    
    console.print(f"✅ ユーザー設定ファイルに保存: {env_file}", style="green")

def _show_env_instructions(api_key: str):
    """環境変数設定手順を表示"""
    console.print(Panel(f"""
環境変数設定方法:

# Bash/Zsh の場合:
export OPENAI_API_KEY='{api_key}'
echo 'export OPENAI_API_KEY="{api_key}"' >> ~/.bashrc

# Fish の場合:
set -gx OPENAI_API_KEY '{api_key}'

# PowerShell の場合:
$env:OPENAI_API_KEY='{api_key}'
""", title="環境変数設定", border_style="yellow"))

def _backup_existing_config():
    """既存設定をバックアップ"""
    backup_files = []
    
    if Path('.env').exists():
        backup_path = Path('.env.backup')
        Path('.env').rename(backup_path)
        backup_files.append(str(backup_path))
    
    if backup_files:
        console.print(f"📦 バックアップ作成: {', '.join(backup_files)}", style="blue")

def _reset_configuration():
    """設定をリセット"""
    files_to_remove = ['.env']
    
    for file_path in files_to_remove:
        if Path(file_path).exists():
            Path(file_path).unlink()

if __name__ == '__main__':
    setup() 