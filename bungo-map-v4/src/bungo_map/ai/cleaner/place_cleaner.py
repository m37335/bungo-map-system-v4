#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名クリーニングシステム

地名データの品質を向上させるためのクリーニング機能を提供します。
低信頼度データの除去、座標の検証、重複の削除などの機能を含みます。
"""

import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()

@dataclass
class CleanerConfig:
    """クリーニング設定"""
    min_confidence: float = 0.7
    min_accuracy: float = 0.8
    remove_duplicates: bool = True
    validate_coordinates: bool = True
    validate_context: bool = True
    japan_bounds: Tuple[float, float, float, float] = (24.0, 45.0, 122.0, 146.0)  # 日本の大まかな境界

class PlaceCleaner:
    """地名クリーニングクラス"""
    
    def __init__(self, config: Optional[CleanerConfig] = None):
        """初期化"""
        self.config = config or CleanerConfig()
        self.stats = {
            'total_places': 0,
            'removed_low_confidence': 0,
            'removed_invalid_coords': 0,
            'removed_duplicates': 0,
            'removed_invalid_context': 0,
            'cleaned_places': 0
        }
        self.console = Console()
        logger.info("🧹 Place Cleaner v4 初期化完了")
    
    def clean_places(self, places: List[Dict]) -> List[Dict]:
        """地名リストをクリーニング"""
        self.stats['total_places'] = len(places)
        cleaned = []
        seen_names = set()
        
        for place in places:
            # 低信頼度データの除去
            if not self._validate_confidence(place):
                self.stats['removed_low_confidence'] += 1
                continue
            
            # 座標の検証
            if self.config.validate_coordinates and not self._validate_coordinates(place):
                self.stats['removed_invalid_coords'] += 1
                continue
            
            # 文脈の検証
            if self.config.validate_context and not self._validate_context(place):
                self.stats['removed_invalid_context'] += 1
                continue
            
            # 重複の除去
            name = place.get('name', '').strip()
            if self.config.remove_duplicates and name in seen_names:
                self.stats['removed_duplicates'] += 1
                continue
            
            seen_names.add(name)
            cleaned.append(place)
            self.stats['cleaned_places'] += 1
        
        return cleaned
    
    def _validate_confidence(self, place: Dict) -> bool:
        """信頼度の検証"""
        confidence = place.get('confidence', 0.0)
        accuracy = place.get('accuracy', 0.0)
        return confidence >= self.config.min_confidence and accuracy >= self.config.min_accuracy
    
    def _validate_coordinates(self, place: Dict) -> bool:
        """座標の検証"""
        lat = place.get('latitude')
        lng = place.get('longitude')
        
        if lat is None or lng is None:
            return False
        
        min_lat, max_lat, min_lng, max_lng = self.config.japan_bounds
        return min_lat <= lat <= max_lat and min_lng <= lng <= max_lng
    
    def _validate_context(self, place: Dict) -> bool:
        """文脈の検証"""
        context = place.get('context', '')
        if not context:
            return False
        
        # 文脈が空でないことを確認
        return len(context.strip()) > 0
    
    def display_stats(self) -> None:
        """統計情報の表示"""
        table = Table(title="クリーニング結果")
        table.add_column("項目", style="cyan")
        table.add_column("値", style="green")
        
        table.add_row("総地名数", str(self.stats['total_places']))
        table.add_row("低信頼度除去", str(self.stats['removed_low_confidence']))
        table.add_row("無効座標除去", str(self.stats['removed_invalid_coords']))
        table.add_row("重複除去", str(self.stats['removed_duplicates']))
        table.add_row("無効文脈除去", str(self.stats['removed_invalid_context']))
        table.add_row("クリーニング後", str(self.stats['cleaned_places']))
        
        self.console.print(table) 