#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
設定管理システム
YAML設定ファイルの読み込みと管理
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """設定管理クラス
    
    設定ファイル（YAML）の読み込みと管理を行います。
    シングルトンパターンで実装され、アプリケーション全体で一つの設定インスタンスを共有します。
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """設定ファイルを読み込む"""
        config_path = Path("config/config.yaml")
        if not config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)
    
    @property
    def db_path(self) -> str:
        """データベースパスを取得"""
        return self._config["database"]["path"]
    
    @property
    def backup_dir(self) -> str:
        """バックアップディレクトリを取得"""
        return self._config["database"]["backup_dir"]
    
    @property
    def vacuum_after_reset(self) -> bool:
        """リセット後のVACUUM実行フラグを取得"""
        return self._config["database"]["vacuum_after_reset"]
    
    @property
    def pipeline_settings(self) -> Dict[str, Any]:
        """パイプライン設定を取得"""
        return self._config["pipeline"]
    
    @property
    def ai_settings(self) -> Dict[str, Any]:
        """AI設定を取得"""
        return self._config["ai"]
    
    @property
    def output_settings(self) -> Dict[str, Any]:
        """出力設定を取得"""
        return self._config["output"]
    
    @property
    def logging_settings(self) -> Dict[str, Any]:
        """ログ設定を取得"""
        return self._config["logging"]
    
    @property
    def cache_settings(self) -> Dict[str, Any]:
        """キャッシュ設定を取得"""
        return self._config["cache"]
    
    @property
    def quality_settings(self) -> Dict[str, Any]:
        """品質管理設定を取得"""
        return self._config["quality"]
    
    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得（ドット区切りキー対応）
        
        Args:
            key: 設定キー（例: "database.path"）
            default: デフォルト値
            
        Returns:
            Any: 設定値
        """
        try:
            value = self._config
            for k in key.split("."):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default 