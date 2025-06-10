"""
AI モジュール専用ロガー
"""

import logging
import sys
from typing import Optional

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    AI モジュール用のロガーを取得
    
    Args:
        name: ロガー名
        level: ログレベル
        
    Returns:
        logging.Logger: 設定済みロガー
    """
    logger = logging.getLogger(f"bungo_map.ai.{name}")
    
    if not logger.handlers:
        # コンソールハンドラを追加
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # フォーマッタを設定
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.setLevel(level)
        
        # 親ロガーへの伝播を防ぐ
        logger.propagate = False
    
    return logger 