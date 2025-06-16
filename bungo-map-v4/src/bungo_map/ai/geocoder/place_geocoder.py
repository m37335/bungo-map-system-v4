#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名ジオコーディングシステム

地名から座標を取得するジオコーディング機能を提供します。
ローカルデータベースとGoogle Maps APIを組み合わせて高精度な座標を取得します。
"""

import json
import logging
import re
import time
import os
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
    api_key: str = ''
    region: str = 'jp'
    language: str = 'ja'
    batch_size: int = 10
    retry_count: int = 3
    retry_delay: float = 1.0
    japan_bounds: Tuple[float, float, float, float] = (24.0, 45.0, 122.0, 146.0)
    use_local_db: bool = True
    use_google_maps: bool = True

    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')

@dataclass
class GeocodingResult:
    """ジオコーディング結果"""
    place_name: str
    latitude: float
    longitude: float
    confidence: float
    source: str
    prefecture: Optional[str] = None
    city: Optional[str] = None

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
            'retries': 0,
            'local_db_hits': 0,
            'google_maps_hits': 0
        }
        self.console = Console()
        
        # ローカルデータベースの初期化
        if self.config.use_local_db:
            self._init_local_databases()
        
        logger.info("🗺️ Place Geocoder v4 初期化完了")
    
    def _init_local_databases(self):
        """ローカルデータベースの初期化"""
        # 都道府県座標データベース
        self.prefecture_coordinates = {
            "北海道": (43.2203, 142.8635, 0.95),
            "青森": (40.5606, 140.6740, 0.95), "青森県": (40.5606, 140.6740, 0.95),
            # ... 他の都道府県データ ...
        }
        
        # 主要都市座標データベース
        self.city_coordinates = {
            "東京": (35.6762, 139.6503, 0.98, "東京都"),
            "京都": (35.0116, 135.7681, 0.98, "京都府"),
            "大阪": (34.6937, 135.5023, 0.98, "大阪府"),
            # ... 他の都市データ ...
        }
        
        # 歴史的地名マッピング
        self.historical_places = {
            "武蔵": (35.6762, 139.6503, 0.85, "東京都"),
            "山城": (35.0116, 135.7681, 0.85, "京都府"),
            "摂津": (34.6937, 135.5023, 0.85, "大阪府"),
            # ... 他の歴史的地名データ ...
        }
        
        # 文学ゆかりの地の座標データベース
        self.literary_places = {
            "松山": (33.8416, 132.7658, 0.95, "愛媛県"),  # 坊っちゃん
            "道後温泉": (33.8484, 132.7864, 0.90, "愛媛県"),
            "小倉": (33.8834, 130.8751, 0.90, "福岡県"),
            # ... 他の文学ゆかりの地データ ...
        }
    
    def parse_compound_place(self, place_name: str) -> Tuple[Optional[str], Optional[str]]:
        """複合地名の解析（都道府県+市区町村）"""
        prefecture_pattern = r'(.*?[都道府県])(.*)'
        match = re.match(prefecture_pattern, place_name)
        if match:
            prefecture = match.group(1)
            city = match.group(2)
            return prefecture, city
        return None, None
    
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
        
        # 1. ローカルデータベースでの検索
        if self.config.use_local_db:
            result = self._search_local_databases(name)
            if result:
                self.stats['local_db_hits'] += 1
                geocoded = place.copy()
                geocoded.update({
                    'latitude': result.latitude,
                    'longitude': result.longitude,
                    'geocoding_confidence': result.confidence,
                    'geocoding_source': result.source,
                    'prefecture': result.prefecture,
                    'city': result.city
                })
                return geocoded
        
        # 2. Google Maps APIでの検索
        if self.config.use_google_maps:
            result = self._search_google_maps(name)
            if result:
                self.stats['google_maps_hits'] += 1
                geocoded = place.copy()
                geocoded.update({
                    'latitude': result.latitude,
                    'longitude': result.longitude,
                    'geocoding_confidence': result.confidence,
                    'geocoding_source': result.source,
                    'prefecture': result.prefecture,
                    'city': result.city
                })
                return geocoded
        
        return None
    
    def _search_local_databases(self, place_name: str) -> Optional[GeocodingResult]:
        """ローカルデータベースでの検索"""
        # 1. 都市データベース検索
        if place_name in self.city_coordinates:
            lat, lng, confidence, prefecture = self.city_coordinates[place_name]
            return GeocodingResult(
                place_name=place_name,
                latitude=lat,
                longitude=lng,
                confidence=confidence,
                source="city_database",
                prefecture=prefecture,
                city=place_name
            )
        
        # 2. 都道府県データベース検索
        if place_name in self.prefecture_coordinates:
            lat, lng, confidence = self.prefecture_coordinates[place_name]
            return GeocodingResult(
                place_name=place_name,
                latitude=lat,
                longitude=lng,
                confidence=confidence,
                source="prefecture_database",
                prefecture=place_name
            )
        
        # 3. 歴史的地名検索
        if place_name in self.historical_places:
            lat, lng, confidence, modern_name = self.historical_places[place_name]
            return GeocodingResult(
                place_name=place_name,
                latitude=lat,
                longitude=lng,
                confidence=confidence,
                source="historical_database",
                prefecture=modern_name,
                city=place_name
            )
        
        # 4. 文学ゆかりの地検索
        if place_name in self.literary_places:
            lat, lng, confidence, prefecture = self.literary_places[place_name]
            return GeocodingResult(
                place_name=place_name,
                latitude=lat,
                longitude=lng,
                confidence=confidence,
                source="literary_database",
                prefecture=prefecture,
                city=place_name
            )
        
        # 5. 部分マッチング検索
        for db_name, db in [
            ("city", self.city_coordinates),
            ("prefecture", self.prefecture_coordinates),
            ("historical", self.historical_places),
            ("literary", self.literary_places)
        ]:
            for known_name, coords in db.items():
                if known_name in place_name or place_name in known_name:
                    if len(coords) == 4:  # 都市・文学データベース
                        lat, lng, confidence, prefecture = coords
                        return GeocodingResult(
                            place_name=place_name,
                            latitude=lat,
                            longitude=lng,
                            confidence=confidence * 0.8,
                            source=f"{db_name}_database_partial",
                            prefecture=prefecture,
                            city=known_name
                        )
                    else:  # 都道府県データベース
                        lat, lng, confidence = coords
                        return GeocodingResult(
                            place_name=place_name,
                            latitude=lat,
                            longitude=lng,
                            confidence=confidence * 0.8,
                            source=f"{db_name}_database_partial",
                            prefecture=known_name
                        )
        
        return None
    
    def _search_google_maps(self, place_name: str) -> Optional[GeocodingResult]:
        """Google Maps APIでの検索"""
        for attempt in range(self.config.retry_count):
            try:
                self.stats['api_calls'] += 1
                result = self.gmaps.geocode(
                    place_name,
                    region=self.config.region,
                    language=self.config.language
                )
                
                if result:
                    location = result[0]['geometry']['location']
                    lat = location['lat']
                    lng = location['lng']
                    
                    # 座標の検証
                    if self._validate_coordinates(lat, lng):
                        # 住所コンポーネントから都道府県と市区町村を抽出
                        prefecture = None
                        city = None
                        for component in result[0]['address_components']:
                            if 'administrative_area_level_1' in component['types']:
                                prefecture = component['long_name']
                            elif 'locality' in component['types']:
                                city = component['long_name']
                        
                        return GeocodingResult(
                            place_name=place_name,
                            latitude=lat,
                            longitude=lng,
                            confidence=0.9,
                            source="google_maps",
                            prefecture=prefecture,
                            city=city
                        )
                
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
        table.add_row("ローカルDBヒット", str(self.stats['local_db_hits']))
        table.add_row("Google Mapsヒット", str(self.stats['google_maps_hits']))
        table.add_row("API呼び出し", str(self.stats['api_calls']))
        table.add_row("リトライ", str(self.stats['retries']))
        
        self.console.print(table) 