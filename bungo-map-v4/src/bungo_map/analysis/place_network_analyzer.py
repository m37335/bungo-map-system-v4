#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名のネットワーク分析機能
"""

import sqlite3
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import networkx as nx
import numpy as np
from datetime import datetime
import json

@dataclass
class NetworkNode:
    """ネットワークノード情報"""
    place_id: int
    place_name: str
    canonical_name: str
    degree: int
    betweenness: float
    pagerank: float
    cluster: Optional[int] = None

@dataclass
class NetworkEdge:
    """ネットワークエッジ情報"""
    source_id: int
    target_id: int
    weight: float
    relation_type: str
    context: str

@dataclass
class NetworkStats:
    """ネットワーク統計情報"""
    total_nodes: int
    total_edges: int
    average_degree: float
    density: float
    average_clustering: float
    diameter: float
    communities: List[Set[str]]

class PlaceNetworkAnalyzer:
    """地名のネットワーク分析クラス"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
        self.graph = nx.Graph()
    
    def _init_database(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS place_networks (
                    network_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    description TEXT,
                    created_at TIMESTAMP,
                    nodes TEXT,
                    edges TEXT,
                    stats TEXT
                )
            """)
    
    def build_network(self, min_weight: float = 0.1) -> nx.Graph:
        """
        地名ネットワークを構築
        
        Args:
            min_weight: エッジの最小重み
            
        Returns:
            構築されたネットワーク
        """
        with sqlite3.connect(self.db_path) as conn:
            # 地名ノードの取得
            cursor = conn.execute("""
                SELECT 
                    pm.place_id,
                    pm.place_name,
                    pm.canonical_name,
                    pm.mention_count
                FROM places_master pm
                WHERE pm.mention_count > 0
            """)
            
            for row in cursor.fetchall():
                self.graph.add_node(
                    row[0],
                    place_name=row[1],
                    canonical_name=row[2],
                    mention_count=row[3]
                )
            
            # 関係性エッジの取得
            cursor = conn.execute("""
                SELECT 
                    source_place_id,
                    target_place_id,
                    strength,
                    relation_type,
                    context
                FROM place_relations
                WHERE strength >= ?
            """, (min_weight,))
            
            for row in cursor.fetchall():
                self.graph.add_edge(
                    row[0],
                    row[1],
                    weight=row[2],
                    relation_type=row[3],
                    context=row[4]
                )
        
        return self.graph
    
    def analyze_network(self) -> NetworkStats:
        """
        ネットワークの分析を実行
        
        Returns:
            ネットワーク統計情報
        """
        if not self.graph.nodes():
            self.build_network()
        
        # 基本統計の計算
        total_nodes = self.graph.number_of_nodes()
        total_edges = self.graph.number_of_edges()
        average_degree = sum(dict(self.graph.degree()).values()) / total_nodes
        density = nx.density(self.graph)
        average_clustering = nx.average_clustering(self.graph)
        
        # 直径の計算（最大最短経路長）
        try:
            diameter = nx.diameter(self.graph)
        except nx.NetworkXError:
            diameter = float('inf')
        
        # コミュニティ検出
        communities = list(nx.community.greedy_modularity_communities(self.graph))
        
        return NetworkStats(
            total_nodes=total_nodes,
            total_edges=total_edges,
            average_degree=average_degree,
            density=density,
            average_clustering=average_clustering,
            diameter=diameter,
            communities=communities
        )
    
    def get_central_places(self, top_n: int = 10) -> List[NetworkNode]:
        """
        中心的な地名を取得
        
        Args:
            top_n: 取得する地名の数
            
        Returns:
            中心的な地名のリスト
        """
        if not self.graph.nodes():
            self.build_network()
        
        # 中心性指標の計算
        degree_centrality = nx.degree_centrality(self.graph)
        betweenness_centrality = nx.betweenness_centrality(self.graph)
        pagerank = nx.pagerank(self.graph)
        
        # 総合スコアの計算
        scores = {}
        for node in self.graph.nodes():
            scores[node] = (
                degree_centrality[node] +
                betweenness_centrality[node] +
                pagerank[node]
            ) / 3
        
        # 上位ノードの取得
        top_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        return [
            NetworkNode(
                place_id=node_id,
                place_name=self.graph.nodes[node_id]['place_name'],
                canonical_name=self.graph.nodes[node_id]['canonical_name'],
                degree=self.graph.degree(node_id),
                betweenness=betweenness_centrality[node_id],
                pagerank=pagerank[node_id]
            )
            for node_id, _ in top_nodes
        ]
    
    def get_related_places(self, place_id: int, max_distance: int = 2) -> List[NetworkNode]:
        """
        関連する地名を取得
        
        Args:
            place_id: 対象の地名ID
            max_distance: 最大距離
            
        Returns:
            関連する地名のリスト
        """
        if not self.graph.nodes():
            self.build_network()
        
        if place_id not in self.graph:
            return []
        
        # 指定距離以内のノードを取得
        related_nodes = set()
        for distance in range(1, max_distance + 1):
            related_nodes.update(
                node for node in self.graph.nodes()
                if nx.shortest_path_length(self.graph, place_id, node) == distance
            )
        
        return [
            NetworkNode(
                place_id=node_id,
                place_name=self.graph.nodes[node_id]['place_name'],
                canonical_name=self.graph.nodes[node_id]['canonical_name'],
                degree=self.graph.degree(node_id),
                betweenness=nx.betweenness_centrality(self.graph)[node_id],
                pagerank=nx.pagerank(self.graph)[node_id]
            )
            for node_id in related_nodes
        ]
    
    def save_network(self, name: str, description: str = ""):
        """
        ネットワークを保存
        
        Args:
            name: ネットワーク名
            description: 説明
        """
        if not self.graph.nodes():
            self.build_network()
        
        # ノードとエッジの情報をJSON形式に変換
        nodes = {
            str(node): {
                'place_name': self.graph.nodes[node]['place_name'],
                'canonical_name': self.graph.nodes[node]['canonical_name'],
                'mention_count': self.graph.nodes[node]['mention_count']
            }
            for node in self.graph.nodes()
        }
        
        edges = [
            {
                'source': str(edge[0]),
                'target': str(edge[1]),
                'weight': self.graph.edges[edge]['weight'],
                'relation_type': self.graph.edges[edge]['relation_type'],
                'context': self.graph.edges[edge]['context']
            }
            for edge in self.graph.edges()
        ]
        
        # 統計情報の計算
        stats = self.analyze_network()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO place_networks
                (name, description, created_at, nodes, edges, stats)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                name,
                description,
                datetime.now(),
                json.dumps(nodes),
                json.dumps(edges),
                json.dumps({
                    'total_nodes': stats.total_nodes,
                    'total_edges': stats.total_edges,
                    'average_degree': stats.average_degree,
                    'density': stats.density,
                    'average_clustering': stats.average_clustering,
                    'diameter': stats.diameter
                })
            ))
    
    def generate_network_report(self, stats: NetworkStats) -> str:
        """
        ネットワークレポートを生成
        
        Args:
            stats: ネットワーク統計情報
            
        Returns:
            レポート文字列
        """
        report = []
        report.append("📊 ネットワーク分析レポート")
        report.append("=" * 40)
        
        report.append("\n基本統計:")
        report.append(f"- ノード数: {stats.total_nodes:,}")
        report.append(f"- エッジ数: {stats.total_edges:,}")
        report.append(f"- 平均次数: {stats.average_degree:.2f}")
        report.append(f"- 密度: {stats.density:.4f}")
        report.append(f"- 平均クラスタリング係数: {stats.average_clustering:.4f}")
        report.append(f"- 直径: {stats.diameter}")
        
        report.append("\nコミュニティ:")
        for i, community in enumerate(stats.communities, 1):
            report.append(f"\nコミュニティ {i}:")
            for place in sorted(community):
                report.append(f"- {place}")
        
        return "\n".join(report) 