"""
データベース操作ユーティリティ
"""

import os
from pathlib import Path

def get_database_path() -> str:
    """
    標準的なデータベースパスを取得
    
    Returns:
        str: データベースファイルパス
    """
    # 環境変数から取得を試行
    db_path = os.getenv('BUNGO_DB_PATH')
    if db_path and Path(db_path).exists():
        return db_path
    
    # デフォルトパスを試行
    default_paths = [
        'data/bungo_production.db',
        'data/bungo_map.db',
        '../data/bungo_production.db',
        '../data/bungo_map.db'
    ]
    
    for path in default_paths:
        if Path(path).exists():
            return path
    
    # どれも見つからない場合は最初のデフォルトパスを返す
    return default_paths[0] 