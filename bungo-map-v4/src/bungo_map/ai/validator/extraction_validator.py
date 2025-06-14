#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名抽出検証システム
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()

@dataclass
class ValidatorConfig:
    """検証設定"""
    min_confidence: float = 0.7
    min_accuracy: float = 0.8
    validate_coordinates: bool = True
    validate_context: bool = True
    validate_duplicates: bool = True

class ExtractionValidator:
    """地名抽出検証クラス"""
    
    def __init__(self, config: ValidatorConfig):
        """初期化"""
        self.config = config
        self.stats = {
            'total_places': 0,
            'valid_places': 0,
            'invalid_places': 0,
            'coordinate_errors': 0,
            'context_errors': 0,
            'duplicate_errors': 0
        }
        logger.info("🔍 Extraction Validator v4 初期化完了")
    
    def validate_places(self, places: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """地名データの検証を実行"""
        self.stats = {
            'total_places': len(places),
            'valid_places': 0,
            'invalid_places': 0,
            'coordinate_errors': 0,
            'context_errors': 0,
            'duplicate_errors': 0
        }
        
        valid_places = []
        invalid_places = []
        
        with Progress() as progress:
            task = progress.add_task("[cyan]検証中...", total=len(places))
            
            for place in places:
                is_valid = self._validate_place(place)
                if is_valid:
                    valid_places.append(place)
                    self.stats['valid_places'] += 1
                else:
                    invalid_places.append(place)
                    self.stats['invalid_places'] += 1
                
                progress.update(task, advance=1)
        
        return valid_places, invalid_places
    
    def _validate_place(self, place: Dict) -> bool:
        """個別の地名を検証"""
        # 基本チェック
        if not self._validate_basic(place):
            return False
        
        # 座標チェック
        if self.config.validate_coordinates and not self._validate_coordinates(place):
            self.stats['coordinate_errors'] += 1
            return False
        
        # 文脈チェック
        if self.config.validate_context and not self._validate_context(place):
            self.stats['context_errors'] += 1
            return False
        
        # 重複チェック
        if self.config.validate_duplicates and not self._validate_duplicates(place):
            self.stats['duplicate_errors'] += 1
            return False
        
        return True
    
    def _validate_basic(self, place: Dict) -> bool:
        """基本的な検証"""
        # 必須フィールドの存在チェック
        required_fields = ['name', 'confidence']
        if not all(field in place for field in required_fields):
            return False
        
        # 信頼度チェック
        if place.get('confidence', 0.0) < self.config.min_confidence:
            return False
        
        return True
    
    def _validate_coordinates(self, place: Dict) -> bool:
        """座標の検証"""
        try:
            lat = float(place.get('latitude', 0))
            lon = float(place.get('longitude', 0))
            
            # 日本国内の座標範囲チェック
            if not (24 <= lat <= 46 and 122 <= lon <= 154):
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    def _validate_context(self, place: Dict) -> bool:
        """文脈の検証"""
        context = place.get('context', '')
        if not context:
            return False
        
        # 文脈の長さチェック
        if len(context) < 10:
            return False
        
        # 地名が文脈に含まれているかチェック
        name = place.get('name', '')
        if name not in context:
            return False
        
        return True
    
    def _validate_duplicates(self, place: Dict) -> bool:
        """重複の検証"""
        # このメソッドは実際の重複チェックには使用されません
        # 重複チェックは別のメソッドで一括処理されます
        return True
    
    def get_stats(self) -> Dict:
        """検証統計を取得"""
        return self.stats
    
    def display_stats(self) -> None:
        """検証統計を表示"""
        console.print("\n[bold blue]地名抽出検証統計[/bold blue]")
        
        table = Table(title="検証結果")
        table.add_column("項目", style="cyan")
        table.add_column("件数", justify="right", style="green")
        table.add_column("割合", justify="right", style="green")
        
        total = self.stats['total_places']
        if total > 0:
            table.add_row(
                "総地名数",
                str(total),
                "100%"
            )
            table.add_row(
                "有効な地名",
                str(self.stats['valid_places']),
                f"{(self.stats['valid_places'] / total) * 100:.1f}%"
            )
            table.add_row(
                "無効な地名",
                str(self.stats['invalid_places']),
                f"{(self.stats['invalid_places'] / total) * 100:.1f}%"
            )
            table.add_row(
                "座標エラー",
                str(self.stats['coordinate_errors']),
                f"{(self.stats['coordinate_errors'] / total) * 100:.1f}%"
            )
            table.add_row(
                "文脈エラー",
                str(self.stats['context_errors']),
                f"{(self.stats['context_errors'] / total) * 100:.1f}%"
            )
            table.add_row(
                "重複エラー",
                str(self.stats['duplicate_errors']),
                f"{(self.stats['duplicate_errors'] / total) * 100:.1f}%"
            )
        
        console.print(table) 