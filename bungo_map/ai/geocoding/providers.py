"""
ジオコーディングプロバイダー

複数のジオコーディングサービスに対応
"""

import requests
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

@dataclass
class GeocodingResult:
    """ジオコーディング結果"""
    latitude: float
    longitude: float
    accuracy: str  # 'high', 'medium', 'low'
    address: str
    provider: str
    confidence: float = 1.0
    success: bool = True  # ジオコーディングが成功したかどうか

@dataclass
class GeocodingResultWrapper:
    """GeocodingResultのラッパークラス"""
    result: Optional[GeocodingResult]
    success: bool
    error_message: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """ジオコーディングが成功したかどうか"""
        return self.success and self.result is not None

    @classmethod
    def success(cls, result: GeocodingResult) -> 'GeocodingResultWrapper':
        """成功時のラッパーを作成"""
        return cls(result=result, success=True)

    @classmethod
    def failure(cls, error_message: str) -> 'GeocodingResultWrapper':
        """失敗時のラッパーを作成"""
        return cls(result=None, success=False, error_message=error_message)

class GeocodingProvider(ABC):
    """ジオコーディングプロバイダーの基底クラス"""
    
    @abstractmethod
    def geocode(self, place_name: str, context: str = "") -> GeocodingResultWrapper:
        """地名をジオコーディング"""
        pass

class NominatimProvider(GeocodingProvider):
    """Nominatimジオコーディングプロバイダー（無料）"""
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        
    def geocode(self, place_name: str, context: str = "") -> GeocodingResultWrapper:
        """Nominatimで地名をジオコーディング"""
        try:
            # 日本に限定した検索
            query = f"{place_name}, Japan"
            
            params = {
                'q': query,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1,
                'countrycodes': 'jp',
                'accept-language': 'ja'
            }
            
            headers = {
                'User-Agent': 'BungoMap/1.0'  # 必須
            }
            
            response = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data:
                result = data[0]
                return GeocodingResultWrapper.success(GeocodingResult(
                    latitude=float(result['lat']),
                    longitude=float(result['lon']),
                    accuracy=self._determine_accuracy(result),
                    address=result.get('display_name', ''),
                    provider='nominatim',
                    confidence=0.8  # Nominatimは中程度の信頼度
                ))
            
            return GeocodingResultWrapper.failure(f"No results found for {place_name}")
            
        except Exception as e:
            return GeocodingResultWrapper.failure(f"Nominatim geocoding error for {place_name}: {str(e)}")
    
    def _determine_accuracy(self, result: Dict[str, Any]) -> str:
        """結果の精度を判定"""
        place_rank = result.get('place_rank', 30)
        osm_type = result.get('osm_type', '')
        
        if place_rank <= 16 and osm_type in ['node', 'way']:
            return 'high'
        elif place_rank <= 20:
            return 'medium'
        else:
            return 'low'

class GoogleProvider(GeocodingProvider):
    """Google Geocoding API プロバイダー（有料）"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        
    def geocode(self, place_name: str, context: str = "") -> GeocodingResultWrapper:
        """Google Geocoding APIで地名をジオコーディング"""
        try:
            # 日本に限定した検索
            query = f"{place_name}, Japan"
            
            params = {
                'address': query,
                'key': self.api_key,
                'region': 'jp',
                'language': 'ja'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                location = result['geometry']['location']
                
                return GeocodingResultWrapper.success(GeocodingResult(
                    latitude=location['lat'],
                    longitude=location['lng'],
                    accuracy=self._determine_accuracy(result),
                    address=result['formatted_address'],
                    provider='google',
                    confidence=1.0  # Googleは常に高信頼度
                ))
            
            return GeocodingResultWrapper.failure(f"No results found for {place_name}")
            
        except Exception as e:
            return GeocodingResultWrapper.failure(f"Google geocoding error for {place_name}: {str(e)}")
    
    def _determine_accuracy(self, result: Dict[str, Any]) -> str:
        """結果の精度を判定"""
        location_type = result.get('geometry', {}).get('location_type', '')
        
        if location_type == 'ROOFTOP':
            return 'high'
        elif location_type in ['RANGE_INTERPOLATED', 'GEOMETRIC_CENTER']:
            return 'medium'
        else:
            return 'low' 