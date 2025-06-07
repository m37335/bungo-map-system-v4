"""
ジオコーディングサービス - シンプル動作版
文豪地図システム v3.0
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GeocodingResult:
    """ジオコーディング結果"""
    place_name: str
    latitude: float
    longitude: float
    confidence: float
    source: str


class GeocodingService:
    """ジオコーディングサービス（動作確認版）"""
    
    def __init__(self):
        # 文学ゆかりの地の座標データベース
        self.known_coordinates = {
            # 主要都市
            "東京": (35.6762, 139.6503, 0.95, "known_database"),
            "京都": (35.0116, 135.7681, 0.95, "known_database"),
            "大阪": (34.6937, 135.5023, 0.95, "known_database"),
            "名古屋": (35.1815, 136.9066, 0.90, "known_database"),
            
            # 文学作品の舞台
            "松山": (33.8416, 132.7658, 0.95, "known_database"),
            "道後温泉": (33.8484, 132.7864, 0.90, "known_database"),
            "小倉": (33.8834, 130.8751, 0.85, "known_database"),
            "新橋": (35.6657, 139.7588, 0.85, "known_database"),
            
            # 歴史的地名
            "江戸": (35.6762, 139.6503, 0.90, "historical_mapping"),  # 現在の東京
            "平安京": (35.0116, 135.7681, 0.90, "historical_mapping"),  # 現在の京都
            "大坂": (34.6937, 135.5023, 0.90, "historical_mapping"),  # 現在の大阪
            "羅生門": (35.0116, 135.7681, 0.80, "historical_mapping"),  # 京都の歴史的建造物
            "朱雀大路": (35.0116, 135.7681, 0.75, "historical_mapping"),  # 平安京の大路
            "洛中": (35.0116, 135.7681, 0.80, "historical_mapping"),  # 京都市中心部
            
            # その他の地名
            "シラクス": (37.0755, 15.2866, 0.70, "approximate"),  # シチリア島
        }
    
    async def geocode_place(self, place_name: str) -> Optional[GeocodingResult]:
        """地名をジオコーディング（非同期版）"""
        return self.geocode_place_sync(place_name)
    
    def geocode_place_sync(self, place_name: str) -> Optional[GeocodingResult]:
        """地名をジオコーディング（同期版）"""
        print(f"🗺️ ジオコーディング: {place_name}")
        
        # 既知の座標データベースから検索
        if place_name in self.known_coordinates:
            lat, lng, confidence, source = self.known_coordinates[place_name]
            result = GeocodingResult(
                place_name=place_name,
                latitude=lat,
                longitude=lng,
                confidence=confidence,
                source=source
            )
            print(f"   ✅ 座標取得: ({lat:.4f}, {lng:.4f}) 信頼度:{confidence:.2f}")
            return result
        
        # 部分マッチング検索
        for known_name, (lat, lng, confidence, source) in self.known_coordinates.items():
            if known_name in place_name or place_name in known_name:
                result = GeocodingResult(
                    place_name=place_name,
                    latitude=lat,
                    longitude=lng,
                    confidence=confidence * 0.8,  # 部分マッチは信頼度下げる
                    source=f"{source}_partial"
                )
                print(f"   ✅ 部分マッチ: ({lat:.4f}, {lng:.4f}) 信頼度:{confidence*0.8:.2f}")
                return result
        
        print(f"   ❌ 座標取得失敗: {place_name}")
        return None
    
    def get_success_rate(self, place_names):
        """ジオコーディング成功率を計算"""
        successful = 0
        for place_name in place_names:
            if self.geocode_place_sync(place_name):
                successful += 1
        
        return successful / len(place_names) if place_names else 0 