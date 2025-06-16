#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名のカテゴリ分類機能
"""

import sqlite3
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import re
from collections import defaultdict

@dataclass
class PlaceCategory:
    """地名カテゴリ情報"""
    category_id: str
    name: str
    description: str
    parent_id: Optional[str] = None
    subcategories: List['PlaceCategory'] = None
    keywords: List[str] = None

@dataclass
class CategorizedPlace:
    """カテゴリ分類された地名情報"""
    place_name: str
    canonical_name: str
    primary_category: PlaceCategory
    secondary_categories: List[PlaceCategory]
    confidence: float
    context_indicators: List[str]

class CategoryClassifier:
    """地名のカテゴリ分類クラス"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.categories = self._load_categories()
        self._init_database()
    
    def _init_database(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS place_categories (
                    category_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    parent_id TEXT,
                    keywords TEXT,
                    FOREIGN KEY (parent_id) REFERENCES place_categories(category_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS place_category_mappings (
                    place_id INTEGER,
                    category_id TEXT,
                    confidence REAL,
                    context_indicators TEXT,
                    PRIMARY KEY (place_id, category_id),
                    FOREIGN KEY (place_id) REFERENCES places_master(place_id),
                    FOREIGN KEY (category_id) REFERENCES place_categories(category_id)
                )
            """)
    
    def _load_categories(self) -> Dict[str, PlaceCategory]:
        """カテゴリの読み込み"""
        categories = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT category_id, name, description, parent_id, keywords
                FROM place_categories
            """)
            
            for row in cursor.fetchall():
                category = PlaceCategory(
                    category_id=row[0],
                    name=row[1],
                    description=row[2],
                    parent_id=row[3],
                    keywords=row[4].split(',') if row[4] else []
                )
                categories[category.category_id] = category
        
        # サブカテゴリの設定
        for category in categories.values():
            if category.parent_id:
                parent = categories.get(category.parent_id)
                if parent:
                    if parent.subcategories is None:
                        parent.subcategories = []
                    parent.subcategories.append(category)
        
        return categories
    
    def classify_place(self, place_name: str, context: Optional[str] = None) -> Optional[CategorizedPlace]:
        """
        地名をカテゴリ分類
        
        Args:
            place_name: 分類対象の地名
            context: 文脈（オプション）
            
        Returns:
            カテゴリ分類された地名情報
        """
        with sqlite3.connect(self.db_path) as conn:
            # 地名の基本情報を取得
            cursor = conn.execute("""
                SELECT place_id, canonical_name
                FROM places_master
                WHERE place_name = ? OR canonical_name = ?
            """, (place_name, place_name))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            place_id, canonical_name = row
            
            # 既存の分類を取得
            cursor = conn.execute("""
                SELECT 
                    pc.category_id,
                    pc.name,
                    pcm.confidence,
                    pcm.context_indicators
                FROM place_category_mappings pcm
                JOIN place_categories pc ON pcm.category_id = pc.category_id
                WHERE pcm.place_id = ?
                ORDER BY pcm.confidence DESC
            """, (place_id,))
            
            mappings = cursor.fetchall()
            if not mappings:
                # 新規分類
                return self._classify_new_place(place_name, canonical_name, context)
            
            # 既存の分類を使用
            primary = self.categories[mappings[0][0]]
            secondary = [self.categories[m[0]] for m in mappings[1:]]
            confidence = mappings[0][2]
            indicators = mappings[0][3].split(',') if mappings[0][3] else []
            
            return CategorizedPlace(
                place_name=place_name,
                canonical_name=canonical_name,
                primary_category=primary,
                secondary_categories=secondary,
                confidence=confidence,
                context_indicators=indicators
            )
    
    def _classify_new_place(self, place_name: str, canonical_name: str,
                          context: Optional[str]) -> Optional[CategorizedPlace]:
        """新規地名の分類"""
        # キーワードベースの分類
        category_scores = defaultdict(float)
        context_indicators = []
        
        for category in self.categories.values():
            # 地名自体のキーワードマッチング
            for keyword in category.keywords:
                if keyword in place_name or keyword in canonical_name:
                    category_scores[category.category_id] += 0.5
            
            # 文脈からのキーワードマッチング
            if context:
                for keyword in category.keywords:
                    if keyword in context:
                        category_scores[category.category_id] += 0.3
                        context_indicators.append(keyword)
        
        if not category_scores:
            return None
        
        # スコアの正規化
        max_score = max(category_scores.values())
        if max_score > 0:
            for category_id in category_scores:
                category_scores[category_id] /= max_score
        
        # カテゴリの決定
        sorted_categories = sorted(
            category_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        primary_category = self.categories[sorted_categories[0][0]]
        secondary_categories = [
            self.categories[cat_id]
            for cat_id, score in sorted_categories[1:]
            if score > 0.5
        ]
        
        return CategorizedPlace(
            place_name=place_name,
            canonical_name=canonical_name,
            primary_category=primary_category,
            secondary_categories=secondary_categories,
            confidence=sorted_categories[0][1],
            context_indicators=context_indicators
        )
    
    def add_category(self, category: PlaceCategory):
        """
        カテゴリを追加
        
        Args:
            category: 追加するカテゴリ
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO place_categories
                (category_id, name, description, parent_id, keywords)
                VALUES (?, ?, ?, ?, ?)
            """, (
                category.category_id,
                category.name,
                category.description,
                category.parent_id,
                ','.join(category.keywords) if category.keywords else None
            ))
        
        self.categories[category.category_id] = category
    
    def get_category_hierarchy(self) -> List[PlaceCategory]:
        """
        カテゴリ階層を取得
        
        Returns:
            トップレベルのカテゴリリスト
        """
        return [
            category
            for category in self.categories.values()
            if not category.parent_id
        ]
    
    def generate_category_report(self, categorized: CategorizedPlace) -> str:
        """
        カテゴリ分類レポートを生成
        
        Args:
            categorized: カテゴリ分類された地名情報
            
        Returns:
            レポート文字列
        """
        report = []
        report.append(f"地名: {categorized.place_name}")
        report.append(f"正規名: {categorized.canonical_name}")
        report.append(f"\n主要カテゴリ: {categorized.primary_category.name}")
        report.append(f"説明: {categorized.primary_category.description}")
        report.append(f"信頼度: {categorized.confidence:.2f}")
        
        if categorized.secondary_categories:
            report.append("\n副次カテゴリ:")
            for category in categorized.secondary_categories:
                report.append(f"- {category.name}")
        
        if categorized.context_indicators:
            report.append("\n文脈指標:")
            for indicator in categorized.context_indicators:
                report.append(f"- {indicator}")
        
        return "\n".join(report) 