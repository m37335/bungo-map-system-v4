"""
データベース接続管理

データベース接続を管理するクラス
"""

import sqlite3
import logging
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """データベース接続管理クラス"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
    
    def __enter__(self) -> sqlite3.Connection:
        """コンテキストマネージャーのエントリーポイント"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            return self.connection
        except Exception as e:
            logger.error(f"データベース接続エラー: {e}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーの終了処理"""
        if self.connection:
            try:
                if exc_type is None:
                    self.connection.commit()
                else:
                    self.connection.rollback()
            finally:
                self.connection.close()
                self.connection = None 