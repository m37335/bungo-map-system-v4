"""
Bungo Map v4.0 Configuration Management

システム全体の設定を管理
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """データベース設定"""
    path: str = "../../data/databases/bungo_v4.db"
    backup_path: str = "../../data/backups"
    migration_path: str = "src/bungo_map/database/migrations"
    

@dataclass  
class ExtractionConfig:
    """地名抽出設定"""
    confidence_threshold: float = 0.5
    max_places_per_sentence: int = 10
    enable_ai_validation: bool = False
    

@dataclass
class APIConfig:
    """API設定"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: list = None
    

@dataclass
class VisualizationConfig:
    """可視化設定"""
    map_center_lat: float = 35.6762
    map_center_lng: float = 139.6503
    default_zoom: int = 6
    max_markers: int = 1000


class Config:
    """システム設定管理"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.project_root = Path(__file__).parent.parent.parent.parent.parent
        
        # 設定初期化
        self.database = DatabaseConfig()
        self.extraction = ExtractionConfig()
        self.api = APIConfig()
        self.visualization = VisualizationConfig()
        
        # 環境変数からの設定読み込み
        self._load_from_env()
    
    def _load_from_env(self):
        """環境変数から設定を読み込み"""
        # データベース設定
        if db_path := os.getenv("BUNGO_DB_PATH"):
            self.database.path = db_path
            
        # API設定
        if api_host := os.getenv("BUNGO_API_HOST"):
            self.api.host = api_host
            
        if api_port := os.getenv("BUNGO_API_PORT"):
            self.api.port = int(api_port)
            
        if debug := os.getenv("BUNGO_DEBUG"):
            self.api.debug = debug.lower() == "true"
    
    def get_database_path(self) -> Path:
        """データベースパスを取得"""
        if Path(self.database.path).is_absolute():
            return Path(self.database.path)
        return self.project_root / self.database.path
    
    def get_backup_path(self) -> Path:
        """バックアップパスを取得"""
        if Path(self.database.backup_path).is_absolute():
            return Path(self.database.backup_path)
        return self.project_root / self.database.backup_path
    
    def ensure_paths(self):
        """必要なディレクトリを作成"""
        self.get_database_path().parent.mkdir(parents=True, exist_ok=True)
        self.get_backup_path().mkdir(parents=True, exist_ok=True)


# グローバル設定インスタンス
config = Config() 