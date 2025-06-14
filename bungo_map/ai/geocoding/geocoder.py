"""
地名ジオコーダー

AI検証済み地名のジオコーディングを管理
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from .providers import NominatimProvider, GoogleProvider, GeocodingResult, GeocodingResultWrapper
from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class PlaceRecord:
    """地名レコード"""
    place_id: int
    place_name: str
    ai_confidence: float
    ai_place_type: str
    ai_is_valid: bool
    ai_normalized_name: str
    current_lat: Optional[float]
    current_lng: Optional[float]
    geocoding_status: str

class PlaceGeocoder:
    """地名ジオコーディング管理クラス"""
    
    def __init__(self, db_path: str, use_google: bool = False, google_api_key: Optional[str] = None):
        """
        Args:
            db_path: データベースファイルパス
            use_google: Google Geocoding APIを使用するか
            google_api_key: Google APIキー（use_google=Trueの場合必須）
        """
        self.db_path = db_path
        self.nominatim = NominatimProvider()
        self.google = GoogleProvider(google_api_key) if use_google and google_api_key else None
        
    def get_places_for_geocoding(self, 
                               min_ai_confidence: float = 0.7,
                               valid_only: bool = True,
                               limit: Optional[int] = None) -> List[PlaceRecord]:
        """ジオコーディング対象の地名を取得"""
        query = """
        SELECT 
            place_id, place_name, ai_confidence, ai_place_type, ai_is_valid,
            ai_normalized_name, lat, lng, geocoding_status
        FROM places 
        WHERE ai_confidence >= ?
        """
        
        params = [min_ai_confidence]
        
        if valid_only:
            query += " AND ai_is_valid = 1"
        
        # まだジオコーディングされていない、または失敗したもの
        query += " AND (geocoding_status IS NULL OR geocoding_status IN ('pending', 'failed'))"
        
        if limit:
            query += f" LIMIT {limit}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            results = []
            
            for row in cursor.fetchall():
                results.append(PlaceRecord(
                    place_id=row[0],
                    place_name=row[1],
                    ai_confidence=row[2] or 0.0,
                    ai_place_type=row[3] or 'unknown',
                    ai_is_valid=bool(row[4]) if row[4] is not None else False,
                    ai_normalized_name=row[5] or row[1],
                    current_lat=row[6],
                    current_lng=row[7],
                    geocoding_status=row[8] or 'pending'
                ))
        
        return results
    
    def geocode_place(self, place_record: PlaceRecord) -> GeocodingResultWrapper:
        """単一地名のジオコーディング"""
        # 正規化名を優先使用
        search_name = place_record.ai_normalized_name or place_record.place_name
        
        logger.info(f"ジオコーディング: {search_name} (信頼度: {place_record.ai_confidence:.2f})")
        
        # Nominatimを最初に試行（無料）
        result = self.nominatim.geocode(search_name)
        
        # Google APIが利用可能で、Nominatimで結果が得られなかった場合
        if not result.is_success and self.google:
            logger.info(f"Nominatim失敗、Google APIを試行: {search_name}")
            result = self.google.geocode(search_name)
        
        return result
    
    def batch_geocode(self, 
                     min_ai_confidence: float = 0.7,
                     limit: Optional[int] = None,
                     dry_run: bool = False) -> Dict[str, Any]:
        """バッチジオコーディング実行"""
        places = self.get_places_for_geocoding(min_ai_confidence, limit=limit)
        
        results = {
            'total': len(places),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'results': []
        }
        
        for place in places:
            logger.info(f"ジオコーディング: {place.place_name}")
            
            # 既にジオコーディング済みの場合はスキップ
            if place.current_lat is not None and place.current_lng is not None:
                results['skipped'] += 1
                logger.info(f"スキップ: {place.place_name} (既にジオコーディング済み)")
                continue
            
            geocoding_result = self.geocode_place(place)
            
            if geocoding_result.is_success:
                results['successful'] += 1
                result = geocoding_result.result
                results['results'].append({
                    'place_id': place.place_id,
                    'place_name': place.place_name,
                    'latitude': result.latitude,
                    'longitude': result.longitude,
                    'accuracy': result.accuracy,
                    'provider': result.provider,
                    'address': result.address
                })
                
                if not dry_run:
                    self._save_geocoding_result(place.place_id, result)
                
                logger.info(f"成功: {place.place_name} -> ({result.latitude:.6f}, {result.longitude:.6f})")
            else:
                results['failed'] += 1
                if not dry_run:
                    self._update_geocoding_status(place.place_id, 'failed', None)
                
                logger.warning(f"失敗: {place.place_name} - {geocoding_result.error_message}")
        
        logger.info(f"ジオコーディング完了: 成功 {results['successful']}, 失敗 {results['failed']}, スキップ {results['skipped']}")
        return results
    
    def _save_geocoding_result(self, place_id: int, result: GeocodingResult):
        """ジオコーディング結果をデータベースに保存"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE places SET
                    lat = ?,
                    lng = ?,
                    geocoding_status = 'success',
                    geocoding_source = ?,
                    geocoding_accuracy = ?,
                    geocoding_updated_at = ?
                WHERE place_id = ?
            """, (
                result.latitude,
                result.longitude,
                result.provider,
                result.accuracy,
                datetime.now().isoformat(),
                place_id
            ))
    
    def _update_geocoding_status(self, place_id: int, status: str, source: Optional[str]):
        """ジオコーディング状態のみを更新"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE places SET
                    geocoding_status = ?,
                    geocoding_source = ?,
                    geocoding_updated_at = ?
                WHERE place_id = ?
            """, (
                status,
                source,
                datetime.now().isoformat(),
                place_id
            ))
    
    def get_geocoding_statistics(self) -> Dict[str, Any]:
        """ジオコーディング統計を取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    geocoding_status,
                    COUNT(*) as count,
                    AVG(ai_confidence) as avg_confidence
                FROM places 
                WHERE ai_analyzed_at IS NOT NULL
                GROUP BY geocoding_status
            """)
            
            stats = {}
            for row in cursor.fetchall():
                status = row[0] or 'pending'
                stats[status] = {
                    'count': row[1],
                    'avg_confidence': row[2] or 0.0
                }
            
            # 総計
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN lat IS NOT NULL AND lng IS NOT NULL THEN 1 END) as geocoded,
                    AVG(ai_confidence) as avg_ai_confidence
                FROM places 
                WHERE ai_analyzed_at IS NOT NULL
            """)
            
            row = cursor.fetchone()
            stats['summary'] = {
                'total_places': row[0],
                'geocoded_places': row[1],
                'geocoding_rate': (row[1] / row[0]) * 100 if row[0] > 0 else 0,
                'avg_ai_confidence': row[2] or 0.0
            }
        
        return stats 