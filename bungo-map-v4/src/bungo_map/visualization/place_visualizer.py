#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名の可視化機能
"""

import sqlite3
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
import folium
from folium import plugins
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json
import branca.colormap as cm
from branca.element import Figure, JavascriptFunction

@dataclass
class VisualizationConfig:
    """可視化設定"""
    map_center: Tuple[float, float] = (35.6812, 139.7671)  # 東京
    default_zoom: int = 5
    max_markers: int = 1000
    cluster_markers: bool = True
    show_popup: bool = True
    show_heatmap: bool = True
    show_timeline: bool = True

class PlaceVisualizer:
    """地名の可視化クラス"""
    
    def __init__(self, db_path: str, config: Optional[VisualizationConfig] = None):
        self.db_path = db_path
        self.config = config or VisualizationConfig()
        self._init_database()
    
    def _init_database(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS visualization_cache (
                    cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    visualization_type TEXT,
                    parameters TEXT,
                    data TEXT,
                    created_at TIMESTAMP
                )
            """)
    
    def create_map(self, places: List[Dict[str, Any]]) -> folium.Map:
        """
        地図を作成
        
        Args:
            places: 地名データのリスト
            
        Returns:
            Folium地図オブジェクト
        """
        # 地図の初期化
        m = folium.Map(
            location=self.config.map_center,
            zoom_start=self.config.default_zoom,
            tiles='CartoDB positron'
        )
        
        # マーカークラスターの追加
        if self.config.cluster_markers:
            marker_cluster = plugins.MarkerCluster().add_to(m)
        
        # ヒートマップデータの準備
        heat_data = []
        
        # マーカーの追加
        for place in places[:self.config.max_markers]:
            if not all(k in place for k in ['latitude', 'longitude']):
                continue
            
            # ポップアップ情報の作成
            popup_content = self._create_popup_content(place)
            
            # マーカーの作成
            marker = folium.CircleMarker(
                location=[place['latitude'], place['longitude']],
                radius=5,
                popup=folium.Popup(popup_content, max_width=300),
                color=self._get_marker_color(place),
                fill=True,
                fill_opacity=0.7
            )
            
            # マーカーの追加
            if self.config.cluster_markers:
                marker.add_to(marker_cluster)
            else:
                marker.add_to(m)
            
            # ヒートマップデータの追加
            if self.config.show_heatmap:
                heat_data.append([place['latitude'], place['longitude'], place.get('weight', 1)])
        
        # ヒートマップの追加
        if self.config.show_heatmap and heat_data:
            plugins.HeatMap(heat_data).add_to(m)
        
        # タイムラインの追加
        if self.config.show_timeline:
            self._add_timeline(m, places)
        
        return m
    
    def _create_popup_content(self, place: Dict[str, Any]) -> str:
        """ポップアップ内容の作成"""
        content = []
        content.append(f"<h4>{place['place_name']}</h4>")
        
        if 'canonical_name' in place:
            content.append(f"<p>正規名: {place['canonical_name']}</p>")
        
        if 'place_type' in place:
            content.append(f"<p>タイプ: {place['place_type']}</p>")
        
        if 'prefecture' in place:
            content.append(f"<p>都道府県: {place['prefecture']}</p>")
        
        if 'mention_count' in place:
            content.append(f"<p>言及回数: {place['mention_count']:,}</p>")
        
        if 'related_places' in place:
            content.append("<p>関連地名:</p>")
            content.append("<ul>")
            for related, strength in place['related_places'][:5]:
                content.append(f"<li>{related} ({strength:.2f})</li>")
            content.append("</ul>")
        
        return "\n".join(content)
    
    def _get_marker_color(self, place: Dict[str, Any]) -> str:
        """マーカー色の決定"""
        if 'mention_count' in place:
            # 言及回数に基づく色分け
            count = place['mention_count']
            if count > 100:
                return 'red'
            elif count > 50:
                return 'orange'
            elif count > 10:
                return 'yellow'
            else:
                return 'green'
        return 'blue'
    
    def _add_timeline(self, m: folium.Map, places: List[Dict[str, Any]]):
        """タイムラインの追加"""
        timeline_data = []
        
        for place in places:
            if 'first_mention' in place and 'last_mention' in place:
                timeline_data.append({
                    'coordinates': [place['latitude'], place['longitude']],
                    'name': place['place_name'],
                    'start': place['first_mention'],
                    'end': place['last_mention']
                })
        
        if timeline_data:
            plugins.Timeline(timeline_data).add_to(m)
    
    def create_trend_plot(self, temporal_data: List[Tuple[datetime, int]],
                         title: str = "時系列トレンド") -> plt.Figure:
        """
        トレンドプロットを作成
        
        Args:
            temporal_data: 時系列データ
            title: プロットのタイトル
            
        Returns:
            MatplotlibのFigureオブジェクト
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # 時系列データの準備
        dates = [date for date, _ in temporal_data]
        counts = [count for _, count in temporal_data]
        
        # メインプロット
        ax1.plot(dates, counts, marker='o', linestyle='-', linewidth=2)
        ax1.set_title(title)
        ax1.set_xlabel("日付")
        ax1.set_ylabel("言及回数")
        ax1.grid(True)
        
        # トレンドライン
        z = np.polyfit(range(len(dates)), counts, 1)
        p = np.poly1d(z)
        ax1.plot(dates, p(range(len(dates))), "r--", label='トレンド')
        
        # 移動平均
        window_size = 7
        moving_avg = np.convolve(counts, np.ones(window_size)/window_size, mode='valid')
        ax1.plot(dates[window_size-1:], moving_avg, "g--", label='移動平均')
        
        ax1.legend()
        
        # 季節性プロット
        monthly_counts = defaultdict(int)
        for date, count in temporal_data:
            month = date.strftime('%m')
            monthly_counts[month] += count
        
        months = sorted(monthly_counts.keys())
        monthly_values = [monthly_counts[m] for m in months]
        
        ax2.bar(months, monthly_values)
        ax2.set_title("月別言及回数")
        ax2.set_xlabel("月")
        ax2.set_ylabel("言及回数")
        ax2.grid(True)
        
        plt.tight_layout()
        return fig
    
    def create_network_plot(self, network_data: Dict[str, Any]) -> plt.Figure:
        """
        ネットワークプロットを作成
        
        Args:
            network_data: ネットワークデータ
            
        Returns:
            MatplotlibのFigureオブジェクト
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # ネットワークの描画
        G = nx.Graph()
        
        # ノードの追加
        for node in network_data['nodes']:
            G.add_node(node['id'], **node['attributes'])
        
        # エッジの追加
        for edge in network_data['edges']:
            G.add_edge(edge['source'], edge['target'], **edge['attributes'])
        
        # レイアウトの計算
        pos = nx.spring_layout(G)
        
        # ノードの描画
        nx.draw_networkx_nodes(G, pos, ax=ax, node_size=100)
        
        # エッジの描画
        nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.5)
        
        # ラベルの描画
        nx.draw_networkx_labels(G, pos, ax=ax)
        
        plt.title("地名ネットワーク")
        plt.axis('off')
        
        return fig
    
    def create_statistics_dashboard(self, stats: Dict[str, Any]) -> plt.Figure:
        """
        統計ダッシュボードを作成
        
        Args:
            stats: 統計データ
            
        Returns:
            MatplotlibのFigureオブジェクト
        """
        fig = plt.figure(figsize=(15, 10))
        
        # サブプロットの作成
        gs = fig.add_gridspec(2, 2)
        
        # 1. 言及回数の分布
        ax1 = fig.add_subplot(gs[0, 0])
        sns.histplot(data=stats['mention_counts'], ax=ax1)
        ax1.set_title("言及回数の分布")
        
        # 2. 都道府県別の集計
        ax2 = fig.add_subplot(gs[0, 1])
        prefecture_data = pd.DataFrame(stats['prefecture_counts'])
        sns.barplot(data=prefecture_data, x='prefecture', y='count', ax=ax2)
        ax2.set_title("都道府県別の地名数")
        plt.xticks(rotation=45)
        
        # 3. 時系列トレンド
        ax3 = fig.add_subplot(gs[1, :])
        temporal_data = pd.DataFrame(stats['temporal_data'])
        sns.lineplot(data=temporal_data, x='date', y='count', ax=ax3)
        ax3.set_title("時系列トレンド")
        
        plt.tight_layout()
        return fig
    
    def save_visualization(self, fig: plt.Figure, output_path: str):
        """
        可視化結果を保存
        
        Args:
            fig: 保存するFigureオブジェクト
            output_path: 保存先パス
        """
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    
    def generate_visualization_report(self, stats: Dict[str, Any]) -> str:
        """
        可視化レポートを生成
        
        Args:
            stats: 統計データ
            
        Returns:
            レポート文字列
        """
        report = []
        report.append("📊 可視化分析レポート")
        report.append("=" * 40)
        
        report.append("\n基本統計:")
        report.append(f"- 総地名数: {stats['total_places']:,}")
        report.append(f"- 総言及回数: {stats['total_mentions']:,}")
        report.append(f"- 平均言及回数: {stats['average_mentions']:.1f}")
        
        report.append("\n都道府県別統計:")
        for prefecture, count in sorted(stats['prefecture_counts'].items(),
                                     key=lambda x: x[1], reverse=True)[:10]:
            report.append(f"- {prefecture}: {count:,}")
        
        report.append("\n時系列トレンド:")
        report.append(f"- 期間: {stats['temporal_data']['start_date']} から {stats['temporal_data']['end_date']}")
        report.append(f"- 傾向: {stats['temporal_data']['trend']}")
        
        return "\n".join(report) 