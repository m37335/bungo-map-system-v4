"""
設定管理ユーティリティ
環境変数・設定ファイルの統合管理
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

class Config:
    """アプリケーション設定管理クラス"""
    
    def __init__(self):
        """設定を初期化"""
        self._load_environment()
        self._validate_required_settings()
    
    def _load_environment(self):
        """環境変数を読み込み"""
        # .envファイルの場所を探す
        env_paths = [
            '.env',
            '../.env',
            '../../.env',
            Path.home() / '.bungo_map' / '.env'
        ]
        
        for env_path in env_paths:
            if Path(env_path).exists():
                load_dotenv(env_path)
                break
    
    def _validate_required_settings(self):
        """必須設定の検証"""
        required_for_ai = ['OPENAI_API_KEY']
        missing_settings = []
        
        for setting in required_for_ai:
            if not self.get(setting):
                missing_settings.append(setting)
        
        if missing_settings:
            self._show_setup_guide(missing_settings)
    
    def _show_setup_guide(self, missing_settings: list):
        """設定ガイドを表示"""
        print("🔧 初期設定が必要です！\n")
        
        if 'OPENAI_API_KEY' in missing_settings:
            print("📝 OpenAI APIキーの設定方法:")
            print("1. https://platform.openai.com/api-keys にアクセス")
            print("2. 新しいAPIキーを作成")
            print("3. 以下のいずれかの方法で設定:\n")
            
            print("方法A: 環境変数で設定（推奨）")
            print("  export OPENAI_API_KEY='your-api-key-here'")
            print("  # または .env ファイルに記録\n")
            
            print("方法B: コマンド引数で指定")
            print("  python main.py ai analyze --api-key 'your-api-key-here'\n")
            
            print("方法C: .envファイルを作成")
            print("  cp env.example .env")
            print("  # .env ファイル内のAPIキーを編集\n")
        
        print("⚠️ セキュリティ注意事項:")
        print("- APIキーは他人に見せないでください")
        print("- Gitにコミットしないでください")
        print("- 定期的にローテーションしてください\n")
    
    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        return os.getenv(key, default)
    
    def get_openai_config(self) -> Dict[str, Any]:
        """OpenAI関連の設定を取得"""
        return {
            'api_key': self.get('OPENAI_API_KEY'),
            'model': self.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
            'max_tokens': int(self.get('OPENAI_MAX_TOKENS', 1000)),
            'temperature': float(self.get('OPENAI_TEMPERATURE', 0.1)),
            'timeout': int(self.get('OPENAI_TIMEOUT', 30)),
        }
    
    def get_processing_limits(self) -> Dict[str, int]:
        """処理制限設定を取得"""
        return {
            'daily_api_limit': int(self.get('DAILY_API_LIMIT', 1000)),
            'batch_size': int(self.get('BATCH_SIZE', 10)),
        }
    
    def is_api_key_configured(self) -> bool:
        """APIキーが設定されているかチェック"""
        return bool(self.get('OPENAI_API_KEY'))
    
    def create_user_env_file(self) -> str:
        """ユーザー用の.envファイルを作成"""
        user_config_dir = Path.home() / '.bungo_map'
        user_config_dir.mkdir(exist_ok=True)
        
        env_file = user_config_dir / '.env'
        
        if not env_file.exists():
            # テンプレートから作成
            template_content = f"""# 文豪地図システム - ユーザー設定
# 自動生成日: {Path().cwd()}

# OpenAI API キー（必須）
OPENAI_API_KEY=your_openai_api_key_here

# データベースパス（オプション）
BUNGO_DB_PATH={Path.cwd() / 'data' / 'bungo_production.db'}

# ログレベル
LOG_LEVEL=INFO

# 処理制限
DAILY_API_LIMIT=1000
BATCH_SIZE=10
"""
            env_file.write_text(template_content)
            print(f"✅ ユーザー設定ファイルを作成しました: {env_file}")
            print("   このファイルを編集してAPIキーを設定してください。")
        
        return str(env_file)

# グローバル設定インスタンス
config = Config() 