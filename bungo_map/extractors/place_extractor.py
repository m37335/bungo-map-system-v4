#!/usr/bin/env python3
"""
地名抽出クラス
作品から地名を抽出し、placesテーブルに登録する
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Set
from rich.console import Console
from rich.progress import Progress

from bungo_map.extractors.ginza_place_extractor import GinzaPlaceExtractor
from bungo_map.extractors.advanced_place_extractor import AdvancedPlaceExtractor
from bungo_map.extractors.improved_place_extractor import ImprovedPlaceExtractor
from bungo_map.extractors.enhanced_place_extractor import EnhancedPlaceExtractor

class PlaceExtractor:
    def __init__(self, db_path: str):
        self.console = Console()
        self.db_path = db_path
        self.extractors = [
            GinzaPlaceExtractor(),
            AdvancedPlaceExtractor(),
            ImprovedPlaceExtractor(),
            EnhancedPlaceExtractor()
        ]
    
    def _get_db_connection(self) -> sqlite3.Connection:
        """データベース接続を取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def extract_places(self, work_id: int, text: str) -> List[Dict[str, Any]]:
        """作品から地名を抽出"""
        places = []
        seen_places: Set[str] = set()
        for extractor in self.extractors:
            try:
                if isinstance(extractor, GinzaPlaceExtractor):
                    extracted = extractor.extract_places_from_text(work_id, text)
                elif isinstance(extractor, AdvancedPlaceExtractor):
                    extracted = extractor.extract_places_combined(text)
                elif isinstance(extractor, ImprovedPlaceExtractor):
                    extracted = extractor.extract_places_with_deduplication(work_id, text)
                elif isinstance(extractor, EnhancedPlaceExtractor):
                    extracted = extractor.extract_places(work_id, text)
                else:
                    continue
                for place in extracted:
                    if getattr(place, 'place_name', None) and place.place_name not in seen_places:
                        seen_places.add(place.place_name)
                        places.append({
                            'work_id': work_id,
                            'place_name': place.place_name,
                            'lat': getattr(place, 'lat', None),
                            'lng': getattr(place, 'lng', None),
                            'before_text': getattr(place, 'before_text', ''),
                            'sentence': getattr(place, 'sentence', ''),
                            'after_text': getattr(place, 'after_text', ''),
                            'confidence': getattr(place, 'confidence', 0.0),
                            'extraction_method': extractor.__class__.__name__
                        })
            except Exception as e:
                self.console.print(f"[red]❌ 抽出エラー ({extractor.__class__.__name__}): {e}[/red]")
        return places 