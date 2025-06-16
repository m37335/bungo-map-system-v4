#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名のジオコーディング機能
"""

import os
import json
import sqlite3
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import googlemaps
from .place_normalizer import PlaceNormalizer, NormalizedPlace

@dataclass
class GeocodedPlace:
    """ジオコーディングされた地名情報"""
    place_name: str
    canonical_name: str
    latitude: float
    longitude: float
    prefecture: Optional[str] = None
    place_type: Optional[str] = None
    confidence: float = 1.0

class PlaceGeocoder:
    """地名のジオコーディングクラス"""
    
    def __init__(self, db_path: str, api_key: Optional[str] = None):
        self.db_path = db_path
        self.normalizer = PlaceNormalizer()
        self.gmaps = googlemaps.Client(key=api_key) if api_key else None
        self._init_database()
    
    def _init_database(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS geocoding_cache (
                    place_name TEXT PRIMARY KEY,
                    canonical_name TEXT,
                    latitude REAL,
                    longitude REAL,
                    prefecture TEXT,
                    place_type TEXT,
                    confidence REAL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_geocoding_cache_canonical 
                ON geocoding_cache(canonical_name)
            """)
    
    def geocode(self, place_name: str) -> Optional[GeocodedPlace]:
        """
        地名をジオコーディング
        
        Args:
            place_name: ジオコーディング対象の地名
            
        Returns:
            ジオコーディングされた地名情報
        """
        # キャッシュを確認
        cached = self._get_from_cache(place_name)
        if cached:
            return cached
        
        # 地名を正規化
        normalized = self.normalizer.normalize(place_name)
        
        # Google Maps APIでジオコーディング
        if self.gmaps:
            try:
                result = self.gmaps.geocode(normalized.canonical_name)
                if result:
                    location = result[0]['geometry']['location']
                    geocoded = GeocodedPlace(
                        place_name=place_name,
                        canonical_name=normalized.canonical_name,
                        latitude=location['lat'],
                        longitude=location['lng'],
                        prefecture=normalized.prefecture,
                        place_type=normalized.place_type,
                        confidence=normalized.confidence
                    )
                    self._save_to_cache(geocoded)
                    return geocoded
            except Exception as e:
                print(f"Google Maps APIエラー: {e}")
        
        return None
    
    def _get_from_cache(self, place_name: str) -> Optional[GeocodedPlace]:
        """キャッシュから地名情報を取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT place_name, canonical_name, latitude, longitude,
                       prefecture, place_type, confidence
                FROM geocoding_cache
                WHERE place_name = ?
            """, (place_name,))
            row = cursor.fetchone()
            
            if row:
                return GeocodedPlace(
                    place_name=row[0],
                    canonical_name=row[1],
                    latitude=row[2],
                    longitude=row[3],
                    prefecture=row[4],
                    place_type=row[5],
                    confidence=row[6]
                )
        
        return None
    
    def _save_to_cache(self, geocoded: GeocodedPlace):
        """地名情報をキャッシュに保存"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO geocoding_cache
                (place_name, canonical_name, latitude, longitude,
                 prefecture, place_type, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                geocoded.place_name,
                geocoded.canonical_name,
                geocoded.latitude,
                geocoded.longitude,
                geocoded.prefecture,
                geocoded.place_type,
                geocoded.confidence
            ))
    
    def batch_geocode(self, place_names: List[str]) -> List[GeocodedPlace]:
        """
        複数の地名を一括でジオコーディング
        
        Args:
            place_names: ジオコーディング対象の地名リスト
            
        Returns:
            ジオコーディングされた地名情報のリスト
        """
        results = []
        for place_name in place_names:
            geocoded = self.geocode(place_name)
            if geocoded:
                results.append(geocoded)
        return results 