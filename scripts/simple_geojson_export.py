#!/usr/bin/env python3
"""
文豪地図システム - 簡単GeoJSON出力
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

# 地名座標マッピング
COORDINATES = {
    "東京": [139.6503, 35.6762],
    "上野": [139.7744, 35.7139],
    "神田": [139.7670, 35.6914],
    "銀座": [139.7677, 35.6717],
    "新橋": [139.7591, 35.6663],
    "本郷": [139.7612, 35.7077],
    "京都": [135.7681, 35.0116],
    "熊本": [130.7417, 32.7900],
    "九州": [131.0, 33.0],
    "盛岡": [141.1527, 39.7036],
    "花巻": [141.1147, 39.3882],
    "ベルリン": [13.4050, 52.5200],
    "江戸": [139.6503, 35.6762],
}

def find_database():
    paths = [
        "bungo_project_v3/data/bungo_production.db",
        "bungo_project_v2/data/bungo_production.db"
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def main():
    print("🗺️ 文豪地図 GeoJSON出力")
    print("=" * 40)
    
    db_path = find_database()
    if not db_path:
        print("❌ データベースが見つかりません")
        return
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
        SELECT 
            a.name as author,
            w.title as work,
            p.place_name,
            p.sentence,
            p.confidence
        FROM places p
        JOIN works w ON p.work_id = w.work_id
        JOIN authors a ON w.author_id = a.author_id
        """
        
        cursor.execute(query)
        data = cursor.fetchall()
        
        features = []
        processed = 0
        
        for row in data:
            place = row['place_name']
            if place in COORDINATES:
                lng, lat = COORDINATES[place]
                
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]
                    },
                    "properties": {
                        "name": place,
                        "author": row['author'],
                        "work": row['work'],
                        "sentence": row['sentence'][:100] if row['sentence'] else "",
                        "confidence": row['confidence'] or 0.8
                    }
                }
                features.append(feature)
                processed += 1
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"bungo_map_{timestamp}.geojson"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        
        print(f"✅ GeoJSON出力完了")
        print(f"📄 ファイル: {output_file}")
        print(f"🗺️ 地点数: {processed}件")
        
        # 統計表示
        authors = set(f['properties']['author'] for f in features)
        print(f"👥 著者: {len(authors)}名")
        
        place_counts = {}
        for f in features:
            place = f['properties']['name']
            place_counts[place] = place_counts.get(place, 0) + 1
        
        print(f"\n📍 主要地名:")
        for place, count in sorted(place_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {place}: {count}回")

if __name__ == "__main__":
    main() 