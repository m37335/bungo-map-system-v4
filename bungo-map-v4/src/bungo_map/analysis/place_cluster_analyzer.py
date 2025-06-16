#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名のクラスタリング分析機能
"""

import sqlite3
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import networkx as nx
from datetime import datetime

@dataclass
class PlaceCluster:
    """地名クラスタ情報"""
    cluster_id: int
    places: List[str]
    center: Tuple[float, float]
    radius: float
    density: float
    characteristics: Dict[str, float]
    created_at: datetime

@dataclass
class ClusterStats:
    """クラスタリング統計情報"""
    total_clusters: int
    total_places: int
    average_cluster_size: float
    silhouette_score: float
    cluster_characteristics: Dict[int, Dict[str, float]]

class PlaceClusterAnalyzer:
    """地名のクラスタリング分析クラス"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
        self.scaler = StandardScaler()
    
    def _init_database(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS place_clusters (
                    cluster_id INTEGER PRIMARY KEY,
                    center_lat REAL,
                    center_lon REAL,
                    radius REAL,
                    density REAL,
                    characteristics TEXT,
                    created_at TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS place_cluster_mappings (
                    place_id INTEGER,
                    cluster_id INTEGER,
                    distance REAL,
                    PRIMARY KEY (place_id, cluster_id),
                    FOREIGN KEY (place_id) REFERENCES places_master(place_id),
                    FOREIGN KEY (cluster_id) REFERENCES place_clusters(cluster_id)
                )
            """)
    
    def perform_clustering(self, method: str = 'dbscan', **kwargs) -> List[PlaceCluster]:
        """
        地名のクラスタリングを実行
        
        Args:
            method: クラスタリング手法 ('dbscan' or 'kmeans')
            **kwargs: クラスタリングパラメータ
            
        Returns:
            クラスタ情報のリスト
        """
        # 地名データの取得
        places_data = self._get_places_data()
        if not places_data:
            return []
        
        # 特徴量の準備
        features = self._prepare_features(places_data)
        
        # クラスタリングの実行
        if method == 'dbscan':
            clusters = self._perform_dbscan(features, **kwargs)
        else:
            clusters = self._perform_kmeans(features, **kwargs)
        
        # クラスタ情報の生成
        place_clusters = self._create_cluster_info(clusters, places_data)
        
        # クラスタ情報の保存
        self._save_clusters(place_clusters)
        
        return place_clusters
    
    def _get_places_data(self) -> List[Dict[str, Any]]:
        """地名データの取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    pm.place_id,
                    pm.place_name,
                    pm.latitude,
                    pm.longitude,
                    pm.mention_count,
                    pm.work_count,
                    pm.author_count,
                    pm.place_type,
                    pm.prefecture
                FROM places_master pm
                WHERE pm.latitude IS NOT NULL 
                AND pm.longitude IS NOT NULL
            """)
            
            return [
                {
                    'place_id': row[0],
                    'place_name': row[1],
                    'latitude': row[2],
                    'longitude': row[3],
                    'mention_count': row[4],
                    'work_count': row[5],
                    'author_count': row[6],
                    'place_type': row[7],
                    'prefecture': row[8]
                }
                for row in cursor.fetchall()
            ]
    
    def _prepare_features(self, places_data: List[Dict[str, Any]]) -> np.ndarray:
        """特徴量の準備"""
        features = []
        for place in places_data:
            feature_vector = [
                place['latitude'],
                place['longitude'],
                place['mention_count'],
                place['work_count'],
                place['author_count']
            ]
            features.append(feature_vector)
        
        return self.scaler.fit_transform(features)
    
    def _perform_dbscan(self, features: np.ndarray, **kwargs) -> np.ndarray:
        """DBSCANによるクラスタリング"""
        eps = kwargs.get('eps', 0.5)
        min_samples = kwargs.get('min_samples', 5)
        
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        return dbscan.fit_predict(features)
    
    def _perform_kmeans(self, features: np.ndarray, **kwargs) -> np.ndarray:
        """K-meansによるクラスタリング"""
        n_clusters = kwargs.get('n_clusters', 5)
        
        kmeans = KMeans(n_clusters=n_clusters)
        return kmeans.fit_predict(features)
    
    def _create_cluster_info(self, cluster_labels: np.ndarray,
                           places_data: List[Dict[str, Any]]) -> List[PlaceCluster]:
        """クラスタ情報の生成"""
        clusters = defaultdict(list)
        
        # クラスタごとの地名をグループ化
        for i, label in enumerate(cluster_labels):
            if label != -1:  # ノイズでない場合
                clusters[label].append(places_data[i])
        
        # クラスタ情報の生成
        place_clusters = []
        for cluster_id, places in clusters.items():
            # 中心点の計算
            center_lat = np.mean([p['latitude'] for p in places])
            center_lon = np.mean([p['longitude'] for p in places])
            
            # 半径の計算
            radius = max(
                np.sqrt(
                    (p['latitude'] - center_lat) ** 2 +
                    (p['longitude'] - center_lon) ** 2
                )
                for p in places
            )
            
            # 密度の計算
            density = len(places) / (np.pi * radius ** 2)
            
            # 特徴量の計算
            characteristics = {
                'mention_count': np.mean([p['mention_count'] for p in places]),
                'work_count': np.mean([p['work_count'] for p in places]),
                'author_count': np.mean([p['author_count'] for p in places])
            }
            
            place_clusters.append(PlaceCluster(
                cluster_id=cluster_id,
                places=[p['place_name'] for p in places],
                center=(center_lat, center_lon),
                radius=radius,
                density=density,
                characteristics=characteristics,
                created_at=datetime.now()
            ))
        
        return place_clusters
    
    def _save_clusters(self, clusters: List[PlaceCluster]):
        """クラスタ情報の保存"""
        with sqlite3.connect(self.db_path) as conn:
            for cluster in clusters:
                # クラスタ情報の保存
                conn.execute("""
                    INSERT INTO place_clusters
                    (cluster_id, center_lat, center_lon, radius,
                     density, characteristics, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    cluster.cluster_id,
                    cluster.center[0],
                    cluster.center[1],
                    cluster.radius,
                    cluster.density,
                    str(cluster.characteristics),
                    cluster.created_at
                ))
                
                # 地名とクラスタのマッピングを保存
                for place_name in cluster.places:
                    cursor = conn.execute("""
                        SELECT place_id FROM places_master
                        WHERE place_name = ?
                    """, (place_name,))
                    
                    place_id = cursor.fetchone()[0]
                    
                    # 距離の計算
                    cursor = conn.execute("""
                        SELECT latitude, longitude
                        FROM places_master
                        WHERE place_id = ?
                    """, (place_id,))
                    
                    lat, lon = cursor.fetchone()
                    distance = np.sqrt(
                        (lat - cluster.center[0]) ** 2 +
                        (lon - cluster.center[1]) ** 2
                    )
                    
                    conn.execute("""
                        INSERT INTO place_cluster_mappings
                        (place_id, cluster_id, distance)
                        VALUES (?, ?, ?)
                    """, (place_id, cluster.cluster_id, distance))
    
    def get_cluster_stats(self) -> ClusterStats:
        """
        クラスタリング統計情報を取得
        
        Returns:
            統計情報
        """
        with sqlite3.connect(self.db_path) as conn:
            # 基本統計
            cursor = conn.execute("""
                SELECT 
                    COUNT(DISTINCT cluster_id) as total_clusters,
                    COUNT(DISTINCT place_id) as total_places,
                    AVG(place_count) as avg_cluster_size
                FROM (
                    SELECT cluster_id, COUNT(*) as place_count
                    FROM place_cluster_mappings
                    GROUP BY cluster_id
                )
            """)
            
            total_clusters, total_places, avg_size = cursor.fetchone()
            
            # クラスタの特徴量
            cursor = conn.execute("""
                SELECT cluster_id, characteristics
                FROM place_clusters
            """)
            
            characteristics = {
                row[0]: eval(row[1])
                for row in cursor.fetchall()
            }
        
        return ClusterStats(
            total_clusters=total_clusters,
            total_places=total_places,
            average_cluster_size=avg_size,
            silhouette_score=0.0,  # 計算が必要な場合は実装
            cluster_characteristics=characteristics
        )
    
    def generate_cluster_report(self, cluster: PlaceCluster) -> str:
        """
        クラスタレポートを生成
        
        Args:
            cluster: クラスタ情報
            
        Returns:
            レポート文字列
        """
        report = []
        report.append(f"クラスタID: {cluster.cluster_id}")
        report.append(f"地名数: {len(cluster.places)}")
        report.append(f"中心座標: ({cluster.center[0]:.4f}, {cluster.center[1]:.4f})")
        report.append(f"半径: {cluster.radius:.2f}度")
        report.append(f"密度: {cluster.density:.2f}")
        
        report.append("\n特徴量:")
        for key, value in cluster.characteristics.items():
            report.append(f"- {key}: {value:.2f}")
        
        report.append("\n含まれる地名:")
        for place in cluster.places:
            report.append(f"- {place}")
        
        return "\n".join(report) 