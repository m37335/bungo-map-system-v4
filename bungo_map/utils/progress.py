#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
進捗管理システム
Rich UIを使用した進捗表示機能を提供
"""

import logging
from typing import Optional, Dict, Any
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

logger = logging.getLogger(__name__)

class ProgressManager:
    """進捗管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            expand=True
        )
        self.tasks: Dict[str, Any] = {}
    
    def start_task(self, description: str, total: int) -> str:
        """タスクを開始
        
        Args:
            description: タスクの説明
            total: 総ステップ数
            
        Returns:
            str: タスクID
        """
        task_id = self.progress.add_task(description, total=total)
        self.tasks[description] = task_id
        return task_id
    
    def update_task(self, description: str, advance: int = 1) -> None:
        """タスクの進捗を更新
        
        Args:
            description: タスクの説明
            advance: 進捗量
        """
        if description in self.tasks:
            self.progress.update(self.tasks[description], advance=advance)
    
    def complete_task(self, description: str) -> None:
        """タスクを完了
        
        Args:
            description: タスクの説明
        """
        if description in self.tasks:
            self.progress.update(self.tasks[description], completed=True)
            del self.tasks[description]
    
    def __enter__(self):
        """コンテキストマネージャー開始"""
        self.progress.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        self.progress.stop() 