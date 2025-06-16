#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名の時系列分析機能
"""

import sqlite3
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import json

@dataclass
class TemporalStats:
    """時系列統計情報"""
    place_name: str
    first_mention: datetime
    last_mention: datetime
    total_mentions: int
    mention_trend: List[Tuple[datetime, int]]
    related_places: List[Tuple[str, float]]
    seasonal_pattern: Optional[Dict[str, float]] = None

@dataclass
class TrendAnalysis:
    """トレンド分析結果"""
    place_name: str
    trend_direction: str
    trend_strength: float
    seasonal_components: Dict[str, float]
    change_points: List[datetime]
    forecast: List[Tuple[datetime, float]]

class TemporalAnalyzer:
    """地名の時系列分析クラス"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS temporal_stats (
                    place_id INTEGER,
                    first_mention TIMESTAMP,
                    last_mention TIMESTAMP,
                    total_mentions INTEGER,
                    trend_data TEXT,
                    related_places TEXT,
                    seasonal_pattern TEXT,
                    PRIMARY KEY (place_id),
                    FOREIGN KEY (place_id) REFERENCES places_master(place_id)
                )
            """)
    
    def analyze_place_temporal(self, place_name: str) -> TemporalStats:
        """
        地名の時系列分析を実行
        
        Args:
            place_name: 分析対象の地名
            
        Returns:
            時系列統計情報
        """
        with sqlite3.connect(self.db_path) as conn:
            # 地名の基本情報を取得
            cursor = conn.execute("""
                SELECT 
                    pm.place_id,
                    MIN(s.created_at) as first_mention,
                    MAX(s.created_at) as last_mention,
                    COUNT(*) as total_mentions
                FROM places_master pm
                JOIN sentence_places sp ON pm.place_id = sp.place_id
                JOIN sentences s ON sp.sentence_id = s.sentence_id
                WHERE pm.place_name = ?
                GROUP BY pm.place_id
            """, (place_name,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            place_id, first_mention, last_mention, total_mentions = row
            
            # 時系列データの取得
            cursor = conn.execute("""
                SELECT 
                    DATE(s.created_at) as date,
                    COUNT(*) as mention_count
                FROM sentence_places sp
                JOIN sentences s ON sp.sentence_id = s.sentence_id
                WHERE sp.place_id = ?
                GROUP BY DATE(s.created_at)
                ORDER BY date
            """, (place_id,))
            
            mention_trend = [(datetime.strptime(row[0], '%Y-%m-%d'), row[1])
                           for row in cursor.fetchall()]
            
            # 関連地名の分析
            cursor = conn.execute("""
                SELECT 
                    pm2.place_name,
                    COUNT(*) as co_mention_count
                FROM sentence_places sp1
                JOIN sentence_places sp2 ON sp1.sentence_id = sp2.sentence_id
                JOIN places_master pm2 ON sp2.place_id = pm2.place_id
                WHERE sp1.place_id = ? AND sp2.place_id != ?
                GROUP BY pm2.place_id
                ORDER BY co_mention_count DESC
                LIMIT 10
            """, (place_id, place_id))
            
            related_places = [(row[0], row[1] / total_mentions)
                            for row in cursor.fetchall()]
            
            # 季節性パターンの分析
            seasonal_pattern = self._analyze_seasonality(mention_trend)
            
            return TemporalStats(
                place_name=place_name,
                first_mention=first_mention,
                last_mention=last_mention,
                total_mentions=total_mentions,
                mention_trend=mention_trend,
                related_places=related_places,
                seasonal_pattern=seasonal_pattern
            )
    
    def _analyze_seasonality(self, mention_trend: List[Tuple[datetime, int]]) -> Dict[str, float]:
        """季節性パターンの分析"""
        if not mention_trend:
            return None
        
        # 月別の集計
        monthly_counts = defaultdict(int)
        for date, count in mention_trend:
            month = date.strftime('%Y-%m')
            monthly_counts[month] += count
        
        # 季節性指標の計算
        seasonal_pattern = {}
        for month in range(1, 13):
            month_str = f"{month:02d}"
            month_counts = [count for m, count in monthly_counts.items()
                          if m.endswith(month_str)]
            if month_counts:
                seasonal_pattern[month_str] = np.mean(month_counts)
        
        return seasonal_pattern
    
    def analyze_trend(self, place_name: str) -> TrendAnalysis:
        """
        トレンド分析を実行
        
        Args:
            place_name: 分析対象の地名
            
        Returns:
            トレンド分析結果
        """
        # 時系列データの取得
        temporal_stats = self.analyze_place_temporal(place_name)
        if not temporal_stats:
            return None
        
        # 時系列データの準備
        dates = [date for date, _ in temporal_stats.mention_trend]
        counts = [count for _, count in temporal_stats.mention_trend]
        
        # トレンドの方向性を判定
        slope, _, r_value, _, _ = stats.linregress(
            range(len(dates)),
            counts
        )
        
        trend_direction = "上昇" if slope > 0 else "下降" if slope < 0 else "横ばい"
        trend_strength = abs(r_value)
        
        # 変化点の検出
        change_points = self._detect_change_points(dates, counts)
        
        # 予測値の計算
        forecast = self._calculate_forecast(dates, counts)
        
        return TrendAnalysis(
            place_name=place_name,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            seasonal_components=temporal_stats.seasonal_pattern,
            change_points=change_points,
            forecast=forecast
        )
    
    def _detect_change_points(self, dates: List[datetime],
                            counts: List[int]) -> List[datetime]:
        """変化点の検出"""
        if len(counts) < 3:
            return []
        
        # 移動平均の計算
        window_size = 3
        moving_avg = np.convolve(counts, np.ones(window_size)/window_size, mode='valid')
        
        # 変化点の検出
        change_points = []
        for i in range(1, len(moving_avg)-1):
            if (moving_avg[i] - moving_avg[i-1]) * (moving_avg[i+1] - moving_avg[i]) < 0:
                change_points.append(dates[i+window_size-1])
        
        return change_points
    
    def _calculate_forecast(self, dates: List[datetime],
                          counts: List[int]) -> List[Tuple[datetime, float]]:
        """予測値の計算"""
        if len(counts) < 2:
            return []
        
        # 単純な線形回帰による予測
        x = np.array(range(len(dates)))
        y = np.array(counts)
        
        slope, intercept = np.polyfit(x, y, 1)
        
        # 将来の30日間を予測
        last_date = dates[-1]
        forecast = []
        for i in range(1, 31):
            future_date = last_date + timedelta(days=i)
            predicted_count = slope * (len(dates) + i) + intercept
            forecast.append((future_date, max(0, predicted_count)))
        
        return forecast
    
    def save_temporal_stats(self, stats: TemporalStats):
        """
        時系列統計情報を保存
        
        Args:
            stats: 保存する統計情報
        """
        with sqlite3.connect(self.db_path) as conn:
            # 地名IDを取得
            cursor = conn.execute("""
                SELECT place_id FROM places_master
                WHERE place_name = ?
            """, (stats.place_name,))
            
            place_id = cursor.fetchone()[0]
            
            # 統計情報を保存
            conn.execute("""
                INSERT OR REPLACE INTO temporal_stats
                (place_id, first_mention, last_mention, total_mentions,
                 trend_data, related_places, seasonal_pattern)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                place_id,
                stats.first_mention,
                stats.last_mention,
                stats.total_mentions,
                json.dumps([(d.isoformat(), c) for d, c in stats.mention_trend]),
                json.dumps(stats.related_places),
                json.dumps(stats.seasonal_pattern)
            ))
    
    def generate_temporal_report(self, stats: TemporalStats) -> str:
        """
        時系列レポートを生成
        
        Args:
            stats: 時系列統計情報
            
        Returns:
            レポート文字列
        """
        report = []
        report.append(f"📊 {stats.place_name} の時系列分析レポート")
        report.append("=" * 40)
        
        report.append("\n基本情報:")
        report.append(f"- 初出: {stats.first_mention.strftime('%Y-%m-%d')}")
        report.append(f"- 最終: {stats.last_mention.strftime('%Y-%m-%d')}")
        report.append(f"- 総言及回数: {stats.total_mentions:,}")
        
        if stats.seasonal_pattern:
            report.append("\n季節性パターン:")
            for month, count in sorted(stats.seasonal_pattern.items()):
                report.append(f"- {month}月: {count:.1f}")
        
        report.append("\n関連地名:")
        for place, strength in stats.related_places:
            report.append(f"- {place}: {strength:.2f}")
        
        return "\n".join(report)
    
    def plot_temporal_trend(self, stats: TemporalStats, save_path: Optional[str] = None):
        """
        時系列トレンドをプロット
        
        Args:
            stats: 時系列統計情報
            save_path: 保存先パス（オプション）
        """
        plt.figure(figsize=(12, 6))
        
        # 時系列データのプロット
        dates = [date for date, _ in stats.mention_trend]
        counts = [count for _, count in stats.mention_trend]
        
        plt.plot(dates, counts, label='実際の言及回数')
        
        # トレンドライン
        z = np.polyfit(range(len(dates)), counts, 1)
        p = np.poly1d(z)
        plt.plot(dates, p(range(len(dates))), "r--", label='トレンド')
        
        plt.title(f"{stats.place_name} の時系列トレンド")
        plt.xlabel("日付")
        plt.ylabel("言及回数")
        plt.legend()
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
        
        plt.close() 