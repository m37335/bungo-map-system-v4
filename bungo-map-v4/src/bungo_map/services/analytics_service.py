"""
Bungo Map v4.0 Analytics Service

データ分析・統計機能を提供するサービス層
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
from ..database.manager import DatabaseManager
from ..database.models import DatabaseConnection
from ..core.config import config


@dataclass
class PlaceStatistics:
    """地名統計データ"""
    place_name: str
    usage_count: int
    avg_confidence: float
    sentence_count: int
    place_type: str
    extraction_methods: List[str]


@dataclass
class AuthorStatistics:
    """作者統計データ"""
    author_id: int
    author_name: str
    work_count: int
    sentence_count: int
    place_count: int
    unique_places: int
    avg_confidence: float


@dataclass
class GeographicalDistribution:
    """地理的分布データ"""
    region: str
    place_count: int
    sentence_count: int
    top_places: List[Tuple[str, int]]


class AnalyticsService:
    """分析サービス"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager(str(config.get_database_path()))
    
    def get_place_statistics(self, limit: int = 50) -> List[PlaceStatistics]:
        """地名別統計を取得"""
        with DatabaseConnection(self.db_manager.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    pm.place_name,
                    pm.place_type,
                    COUNT(sp.sentence_id) as usage_count,
                    COUNT(DISTINCT sp.sentence_id) as sentence_count,
                    AVG(sp.confidence) as avg_confidence,
                    GROUP_CONCAT(DISTINCT sp.extraction_method) as methods
                FROM places_master pm
                JOIN sentence_places sp ON pm.place_id = sp.place_id
                GROUP BY pm.place_id, pm.place_name, pm.place_type
                ORDER BY usage_count DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append(PlaceStatistics(
                    place_name=row['place_name'],
                    usage_count=row['usage_count'],
                    avg_confidence=row['avg_confidence'],
                    sentence_count=row['sentence_count'],
                    place_type=row['place_type'],
                    extraction_methods=row['methods'].split(',') if row['methods'] else []
                ))
            
            return results
    
    def get_author_statistics(self) -> List[AuthorStatistics]:
        """作者別統計を取得"""
        with DatabaseConnection(self.db_manager.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    s.author_id,
                    'Unknown' as author_name,
                    COUNT(DISTINCT s.work_id) as work_count,
                    COUNT(DISTINCT s.sentence_id) as sentence_count,
                    COUNT(sp.place_id) as place_count,
                    COUNT(DISTINCT sp.place_id) as unique_places,
                    AVG(sp.confidence) as avg_confidence
                FROM sentences s
                LEFT JOIN sentence_places sp ON s.sentence_id = sp.sentence_id
                GROUP BY s.author_id
                ORDER BY sentence_count DESC
            """)
            
            results = []
            for row in cursor.fetchall():
                results.append(AuthorStatistics(
                    author_id=row['author_id'],
                    author_name=row['author_name'],
                    work_count=row['work_count'],
                    sentence_count=row['sentence_count'],
                    place_count=row['place_count'],
                    unique_places=row['unique_places'],
                    avg_confidence=row['avg_confidence'] or 0.0
                ))
            
            return results
    
    def get_geographical_distribution(self) -> List[GeographicalDistribution]:
        """地理的分布を取得"""
        distributions = []
        
        # 地名タイプ別分布
        for place_type in ['都道府県', '市区町村', '有名地名', '郡']:
            with DatabaseConnection(self.db_manager.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(DISTINCT pm.place_id) as place_count,
                        COUNT(sp.sentence_id) as sentence_count
                    FROM places_master pm
                    JOIN sentence_places sp ON pm.place_id = sp.place_id
                    WHERE pm.place_type = ?
                """, (place_type,))
                
                stats = cursor.fetchone()
                
                # トップ地名
                cursor = conn.execute("""
                    SELECT pm.place_name, COUNT(sp.sentence_id) as count
                    FROM places_master pm
                    JOIN sentence_places sp ON pm.place_id = sp.place_id
                    WHERE pm.place_type = ?
                    GROUP BY pm.place_name
                    ORDER BY count DESC
                    LIMIT 5
                """, (place_type,))
                
                top_places = [(row['place_name'], row['count']) 
                             for row in cursor.fetchall()]
                
                distributions.append(GeographicalDistribution(
                    region=place_type,
                    place_count=stats['place_count'],
                    sentence_count=stats['sentence_count'],
                    top_places=top_places
                ))
        
        return distributions
    
    def get_extraction_method_analysis(self) -> Dict[str, Any]:
        """抽出手法分析"""
        with DatabaseConnection(self.db_manager.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    extraction_method,
                    COUNT(*) as usage_count,
                    AVG(confidence) as avg_confidence,
                    MIN(confidence) as min_confidence,
                    MAX(confidence) as max_confidence
                FROM sentence_places
                GROUP BY extraction_method
                ORDER BY usage_count DESC
            """)
            
            methods = {}
            for row in cursor.fetchall():
                methods[row['extraction_method']] = {
                    'usage_count': row['usage_count'],
                    'avg_confidence': row['avg_confidence'],
                    'min_confidence': row['min_confidence'],
                    'max_confidence': row['max_confidence']
                }
            
            return methods
    
    def get_temporal_trends(self) -> Dict[str, Any]:
        """時系列トレンド分析（作品別）"""
        with DatabaseConnection(self.db_manager.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    s.work_id,
                    COUNT(DISTINCT s.sentence_id) as sentence_count,
                    COUNT(sp.place_id) as place_count,
                    COUNT(DISTINCT sp.place_id) as unique_places,
                    AVG(sp.confidence) as avg_confidence
                FROM sentences s
                LEFT JOIN sentence_places sp ON s.sentence_id = sp.sentence_id
                GROUP BY s.work_id
                ORDER BY s.work_id
            """)
            
            trends = {
                'work_data': [],
                'total_sentences': 0,
                'total_places': 0,
                'avg_places_per_work': 0
            }
            
            work_data = []
            for row in cursor.fetchall():
                work_data.append({
                    'work_id': row['work_id'],
                    'sentence_count': row['sentence_count'],
                    'place_count': row['place_count'],
                    'unique_places': row['unique_places'],
                    'avg_confidence': row['avg_confidence'] or 0.0
                })
            
            trends['work_data'] = work_data
            trends['total_sentences'] = sum(w['sentence_count'] for w in work_data)
            trends['total_places'] = sum(w['place_count'] for w in work_data)
            trends['avg_places_per_work'] = (
                trends['total_places'] / len(work_data) if work_data else 0
            )
            
            return trends
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """総合サマリーレポート生成"""
        stats = self.db_manager.get_statistics()
        place_stats = self.get_place_statistics(10)
        author_stats = self.get_author_statistics()
        geo_dist = self.get_geographical_distribution()
        method_analysis = self.get_extraction_method_analysis()
        
        return {
            'overview': stats,
            'top_places': place_stats,
            'author_summary': author_stats,
            'geographical_distribution': geo_dist,
            'extraction_methods': method_analysis,
            'generation_timestamp': self._get_timestamp()
        }
    
    def _get_timestamp(self) -> str:
        """現在のタイムスタンプを取得"""
        from datetime import datetime
        return datetime.now().isoformat() 