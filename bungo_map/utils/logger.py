#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ログ設定モジュール
"""

import logging
import sys
from typing import Optional


def setup_logger(name: str, level: int = logging.INFO, 
                format_string: Optional[str] = None) -> logging.Logger:
    """
    ロガーを設定
    
    Args:
        name: ロガー名
        level: ログレベル
        format_string: フォーマット文字列
    
    Returns:
        設定済みロガー
    """
    
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # ロガーの取得
    logger = logging.getLogger(name)
    
    # 既にハンドラーが設定されている場合はそのまま返す
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # コンソールハンドラーの作成
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # フォーマッタの設定
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    
    # ハンドラーをロガーに追加
    logger.addHandler(handler)
    
    return logger 