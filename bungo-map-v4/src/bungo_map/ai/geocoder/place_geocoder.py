#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名ジオコーディングシステム

地名から座標を取得するジオコーディング機能を提供します。
Google Maps APIを使用して高精度な座標を取得します。
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import googlemaps
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()

@dataclass
class GeocoderConfig:
    """ジオコーディング設定"""
    api_key: str
    region: str = 'jp'
    language: str = 'ja'
    batch_size: int = 10
    retry_count: int = 3
    retry_delay: float = 1.0
    japan_bounds: Tuple[float, float, float, float] = (24.0, 45.0, 122.0, 146.0)

class PlaceGeocoder:
    """地名ジオコーディングクラス"""
    
    def __init__(self, config: Optional[GeocoderConfig] = None):
        """初期化"""
        self.config = config or GeocoderConfig(api_key='')
        self.gmaps = googlemaps.Client(key=self.config.api_key)
        self.stats = {
            'total_places': 0,
            'successful_geocoding': 0,
            'failed_geocoding': 0,
            'api_calls': 0,
            'retries': 0
        }
        self.console = Console()
        logger.info("🗺️ Place Geocoder v4 初期化完了")
    
    def geocode_places(self, places: List[Dict]) -> List[Dict]:
        """地名リストをジオコーディング"""
        self.stats['total_places'] = len(places)
        geocoded = []
        
        # バッチ処理
        for i in range(0, len(places), self.config.batch_size):
            batch = places[i:i + self.config.batch_size]
            for place in batch:
                try:
                    geocoded_place = self._geocode_place(place)
                    if geocoded_place:
                        geocoded.append(geocoded_place)
                        self.stats['successful_geocoding'] += 1
                    else:
                        self.stats['failed_geocoding'] += 1
                except Exception as e:
                    logger.error(f"ジオコーディングエラー: {e}")
                    self.stats['failed_geocoding'] += 1
            
            # API制限を考慮して待機
            if i + self.config.batch_size < len(places):
                time.sleep(1.0)
        
        return geocoded
    
    def _geocode_place(self, place: Dict) -> Optional[Dict]:
        """個別の地名をジオコーディング"""
        name = place.get('name', '')
        if not name:
            return None
        
        # 既に座標がある場合は検証のみ
        if 'latitude' in place and 'longitude' in place:
            if self._validate_coordinates(place['latitude'], place['longitude']):
                return place
            return None
        
        # Google Maps APIを使用してジオコーディング
        for attempt in range(self.config.retry_count):
            try:
                self.stats['api_calls'] += 1
                result = self.gmaps.geocode(
                    name,
                    region=self.config.region,
                    language=self.config.language
                )
                
                if result:
                    location = result[0]['geometry']['location']
                    lat = location['lat']
                    lng = location['lng']
                    
                    # 座標の検証
                    if self._validate_coordinates(lat, lng):
                        geocoded = place.copy()
                        geocoded.update({
                            'latitude': lat,
                            'longitude': lng,
                            'geocoding_confidence': 0.9,  # Google Mapsの結果は高信頼
                            'geocoding_source': 'google_maps'
                        })
                        return geocoded
                
                return None
            
            except Exception as e:
                if attempt < self.config.retry_count - 1:
                    self.stats['retries'] += 1
                    time.sleep(self.config.retry_delay)
                else:
                    raise e
    
    def _validate_coordinates(self, lat: float, lng: float) -> bool:
        """座標の検証"""
        min_lat, max_lat, min_lng, max_lng = self.config.japan_bounds
        return min_lat <= lat <= max_lat and min_lng <= lng <= max_lng
    
    def display_stats(self) -> None:
        """統計情報の表示"""
        table = Table(title="ジオコーディング結果")
        table.add_column("項目", style="cyan")
        table.add_column("値", style="green")
        
        table.add_row("総地名数", str(self.stats['total_places']))
        table.add_row("成功", str(self.stats['successful_geocoding']))
        table.add_row("失敗", str(self.stats['failed_geocoding']))
        table.add_row("API呼び出し", str(self.stats['api_calls']))
        table.add_row("リトライ", str(self.stats['retries']))
        
        self.console.print(table) 