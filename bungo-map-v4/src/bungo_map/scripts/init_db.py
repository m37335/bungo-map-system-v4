#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベース初期化スクリプト
"""

import os
import logging
from pathlib import Path
from ..database.schema_manager import SchemaManager

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """データベースの初期化"""
    # データベースのパスを設定
    db_path = Path("/app/bungo-map-v4/data/databases/bungo_v4.db").resolve()
    
    # 既存のデータベースを削除
    if db_path.exists():
        logger.info(f"既存のデータベースを削除: {db_path}")
        os.remove(db_path)
    
    # データベースディレクトリを作成
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # スキーママネージャーを初期化
    logger.info(f"データベースを初期化: {db_path}")
    SchemaManager(str(db_path))

if __name__ == "__main__":
    init_database() 