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

class GeocodingProvider(ABC):
    """ジオコーディングプロバイダーの基底クラス"""
    
    @abstractmethod
    def geocode(self, place_name: str, context: str = "") -> Optional[GeocodingResult]:
        """地名をジオコーディング"""
        pass

class NominatimProvider(GeocodingProvider):
    """OpenStreetMap Nominatim API プロバイダー（無料）"""
    
    def __init__(self, user_agent: str = "BungoMap/1.0"):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.user_agent = user_agent
        self.rate_limit_delay = 1.0  # 1秒間隔（利用規約準拠）
        
    def geocode(self, place_name: str, context: str = "") -> Optional[GeocodingResult]:
        """Nominatim APIで地名をジオコーディング"""
        try:
            # 日本に限定した検索クエリ
            query = f"{place_name}, Japan"
            
            params = {
                'q': query,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'jp',  # 日本に限定
                'addressdetails': 1
            }
            
            headers = {'User-Agent': self.user_agent}
            
            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            results = response.json()
            
            if results:
                result = results[0]
                
                # 精度判定
                accuracy = self._determine_accuracy(result)
                
                return GeocodingResult(
                    latitude=float(result['lat']),
                    longitude=float(result['lon']),
                    accuracy=accuracy,
                    address=result.get('display_name', ''),
                    provider='nominatim',
                    confidence=float(result.get('importance', 0.5))
                )
            
            # レート制限遵守
            time.sleep(self.rate_limit_delay)
            return None
            
        except Exception as e:
            print(f"Nominatim geocoding error for {place_name}: {str(e)}")
            return None
    
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
        
    def geocode(self, place_name: str, context: str = "") -> Optional[GeocodingResult]:
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
                
                # 精度判定
                accuracy = self._determine_accuracy(result)
                
                return GeocodingResult(
                    latitude=location['lat'],
                    longitude=location['lng'],
                    accuracy=accuracy,
                    address=result['formatted_address'],
                    provider='google',
                    confidence=1.0  # Googleは常に高信頼度
                )
            
            return None
            
        except Exception as e:
            print(f"Google geocoding error for {place_name}: {str(e)}")
            return None
    
    def _determine_accuracy(self, result: Dict[str, Any]) -> str:
        """結果の精度を判定"""
        location_type = result.get('geometry', {}).get('location_type', '')
        
        if location_type == 'ROOFTOP':
            return 'high'
        elif location_type in ['RANGE_INTERPOLATED', 'GEOMETRIC_CENTER']:
            return 'medium'
        else:
            return 'low' 