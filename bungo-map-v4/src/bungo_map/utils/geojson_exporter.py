#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GeoJSONエクスポート機能
データベースの地名データをGeoJSON形式で出力
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from ..database.models import Author, Work, PlaceMaster as Place


class GeoJSONExporter:
    """GeoJSONエクスポートクラス"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_places_with_metadata(self) -> List[Dict[str, Any]]:
        """座標付き地名データを作者・作品情報と共に取得"""
        places_data = []
        
        with self.db_manager.get_connection() as conn:
            query = """
            SELECT 
                p.place_id, p.work_id, p.place_name, p.lat, p.lng,
                p.before_text, p.sentence, p.after_text, p.confidence, p.extraction_method,
                w.title as work_title, w.wiki_url as work_wiki_url,
                a.name as author_name, a.wikipedia_url as author_wiki_url,
                a.birth_year, a.death_year
            FROM places p
            JOIN works w ON p.work_id = w.work_id
            JOIN authors a ON w.author_id = a.author_id
            WHERE p.lat IS NOT NULL AND p.lng IS NOT NULL
            ORDER BY a.name, w.title, p.place_name
            """
            
            cursor = conn.execute(query)
            for row in cursor.fetchall():
                places_data.append({
                    'place_id': row[0],
                    'work_id': row[1],
                    'place_name': row[2],
                    'lat': row[3],
                    'lng': row[4],
                    'before_text': row[5],
                    'sentence': row[6],
                    'after_text': row[7],
                    'confidence': row[8],
                    'extraction_method': row[9],
                    'work_title': row[10],
                    'work_wiki_url': row[11],
                    'author_name': row[12],
                    'author_wiki_url': row[13],
                    'birth_year': row[14],
                    'death_year': row[15]
                })
        
        return places_data
    
    def create_geojson_feature(self, place_data: Dict[str, Any]) -> Dict[str, Any]:
        """地名データからGeoJSONのFeatureを作成"""
        
        # 作者の生没年表示
        lifespan = ""
        if place_data['birth_year'] and place_data['death_year']:
            lifespan = f"({place_data['birth_year']}-{place_data['death_year']})"
        elif place_data['birth_year']:
            lifespan = f"({place_data['birth_year']}-)"
        
        # 文脈文章の構築
        context = ""
        if place_data['before_text'] or place_data['sentence'] or place_data['after_text']:
            parts = []
            if place_data['before_text']:
                parts.append(place_data['before_text'])
            if place_data['sentence']:
                parts.append(f"**{place_data['sentence']}**")  # 地名部分を強調
            if place_data['after_text']:
                parts.append(place_data['after_text'])
            context = "".join(parts)
        
        # MapKit用のプロパティ設計
        properties = {
            "place_id": place_data['place_id'],
            "place_name": place_data['place_name'],
            "author_name": place_data['author_name'],
            "author_lifespan": lifespan,
            "work_title": place_data['work_title'],
            "context": context,
            "confidence": place_data['confidence'],
            "extraction_method": place_data['extraction_method'],
            
            # ピンの表示用
            "title": place_data['place_name'],
            "subtitle": f"{place_data['author_name']}『{place_data['work_title']}』",
            
            # 詳細情報
            "work_wiki_url": place_data['work_wiki_url'],
            "author_wiki_url": place_data['author_wiki_url'],
            
            # カテゴリ分類
            "category": self._classify_place_category(place_data['place_name']),
            "era": self._classify_era(place_data['birth_year']),
            
            # メタデータ
            "work_id": place_data['work_id'],
        }
        
        # GeoJSONのFeature作成
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [place_data['lng'], place_data['lat']]  # GeoJSONは[経度, 緯度]の順
            },
            "properties": properties
        }
        
        return feature
    
    def _classify_place_category(self, place_name: str) -> str:
        """地名のカテゴリ分類"""
        if any(suffix in place_name for suffix in ['県', '府', '道', '都']):
            return "prefecture"
        elif any(suffix in place_name for suffix in ['市', '区', '町', '村']):
            return "city"
        elif any(suffix in place_name for suffix in ['海', '湖', '川', '山', '島']):
            return "nature"
        elif any(keyword in place_name for keyword in ['温泉', '神社', '寺', '駅']):
            return "landmark"
        elif place_name in ['本郷', '上野', '浅草', '朱雀大路']:
            return "district"
        else:
            return "other"
    
    def _classify_era(self, birth_year: Optional[int]) -> str:
        """作者の生年による時代分類"""
        if not birth_year:
            return "unknown"
        elif birth_year < 1870:
            return "edo"
        elif birth_year < 1912:
            return "meiji"
        elif birth_year < 1926:
            return "taisho"
        elif birth_year < 1945:
            return "early_showa"
        else:
            return "modern"
    
    def create_geojson(self) -> Dict[str, Any]:
        """GeoJSONデータを作成"""
        places_data = self.get_places_with_metadata()
        
        # 統計情報
        total_places = len(places_data)
        unique_authors = len(set(place['author_name'] for place in places_data))
        unique_works = len(set(place['work_title'] for place in places_data))
        
        # Features作成
        features = []
        for place_data in places_data:
            feature = self.create_geojson_feature(place_data)
            features.append(feature)
        
        # GeoJSON FeatureCollection作成
        geojson = {
            "type": "FeatureCollection",
            "metadata": {
                "title": "文豪ゆかり地図",
                "description": "日本の文豪作品に登場する地名データ",
                "version": "2.0.0",
                "generated_at": datetime.now().isoformat(),
                "total_places": total_places,
                "unique_authors": unique_authors,
                "unique_works": unique_works,
                "coordinate_system": "WGS84",
                "data_source": "bungo-map v2.0"
            },
            "features": features
        }
        
        return geojson
    
    def export_to_file(self, output_path: str, indent: int = 2) -> bool:
        """GeoJSONファイルにエクスポート"""
        try:
            # ディレクトリが存在しない場合は作成
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # GeoJSONデータ作成
            geojson_data = self.create_geojson()
            
            # ファイルに書き込み
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(geojson_data, f, ensure_ascii=False, indent=indent)
            
            return True
            
        except Exception as e:
            print(f"GeoJSONエクスポートエラー: {e}")
            return False
    
    def get_export_stats(self) -> Dict[str, Any]:
        """エクスポート可能データの統計情報"""
        places_data = self.get_places_with_metadata()
        
        # 統計計算
        stats = {
            "total_places": len(places_data),
            "unique_authors": len(set(place['author_name'] for place in places_data)),
            "unique_works": len(set(place['work_title'] for place in places_data)),
        }
        
        # 作者別統計
        author_stats = {}
        for place in places_data:
            author = place['author_name']
            if author not in author_stats:
                author_stats[author] = {"places": 0, "works": set()}
            author_stats[author]["places"] += 1
            author_stats[author]["works"].add(place['work_title'])
        
        # 作者別統計を整理
        for author in author_stats:
            author_stats[author]["works"] = len(author_stats[author]["works"])
        
        stats["by_author"] = author_stats
        
        # カテゴリ別統計
        category_stats = {}
        for place in places_data:
            category = self._classify_place_category(place['place_name'])
            category_stats[category] = category_stats.get(category, 0) + 1
        
        stats["by_category"] = category_stats
        
        return stats 