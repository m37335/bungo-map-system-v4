#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪地図システム - 更新済みGeoJSONエクスポート
座標データが追加された地名を地図用に出力
"""

import sqlite3
import json
import os
from datetime import datetime

def export_updated_geojson():
    """更新された座標データでGeoJSONエクスポート"""
    print("🗺️ 文豪地図システム - 更新済みGeoJSONエクスポート")
    print("=" * 60)
    
    try:
        # データベース接続
        conn = sqlite3.connect('data/bungo_production.db')
        cursor = conn.cursor()
        
        print("📊 データベース接続完了")
        
        # 座標データがある地名を取得
        cursor.execute('''
            SELECT p.place_name, p.lat, p.lng, p.sentence, 
                   w.title, a.name as author_name, p.confidence,
                   p.extraction_method, p.before_text, p.after_text
            FROM places p
            JOIN works w ON p.work_id = w.work_id  
            JOIN authors a ON w.author_id = a.author_id
            WHERE p.lat IS NOT NULL AND p.lng IS NOT NULL
            ORDER BY p.confidence DESC, a.name, w.title
        ''')
        
        places_data = cursor.fetchall()
        print(f"📍 座標データ取得: {len(places_data)}件")
        
        if len(places_data) == 0:
            print("❌ 座標データがありません")
            return
        
        # 出力ディレクトリ作成
        os.makedirs('output', exist_ok=True)
        
        # GeoJSON形式で構築
        features = []
        author_stats = {}
        method_stats = {}
        
        for place_name, lat, lng, sentence, work_title, author_name, confidence, method, before_text, after_text in places_data:
            # 統計カウント
            author_stats[author_name] = author_stats.get(author_name, 0) + 1
            method_stats[method] = method_stats.get(method, 0) + 1
            
            # 文脈テキスト準備
            context = ""
            if before_text:
                context += before_text[-30:] if len(before_text) > 30 else before_text
            if sentence:
                context += sentence
            if after_text:
                context += after_text[:30] if len(after_text) > 30 else after_text
            
            # GeoJSON Feature作成
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [lng, lat]  # [経度, 緯度]
                },
                'properties': {
                    'place_name': place_name,
                    'author': author_name,
                    'work': work_title,
                    'context': context[:150] + '...' if len(context) > 150 else context,
                    'sentence': sentence[:100] + '...' if sentence and len(sentence) > 100 else sentence,
                    'confidence': round(confidence, 2) if confidence else 0.5,
                    'method': method,
                    'marker-color': '#FF6B6B' if method == 'ginza_nlp' else '#4ECDC4',
                    'marker-size': 'medium',
                    'marker-symbol': 'circle'
                }
            }
            features.append(feature)
        
        # GeoJSONオブジェクト構築
        geojson = {
            'type': 'FeatureCollection',
            'name': f'bungo_map_updated_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'metadata': {
                'title': '文豪ゆかり地図システム v3.0',
                'description': '青空文庫テキストから抽出した文豪作品の舞台地名',
                'export_date': datetime.now().isoformat(),
                'total_places': len(features),
                'coordinate_coverage': f'{len(features)}/988 ({len(features)/988*100:.1f}%)',
                'authors_covered': len(author_stats),
                'extraction_methods': list(method_stats.keys())
            },
            'features': features
        }
        
        # ファイル出力
        output_filename = f"output/bungo_map_updated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        
        # 結果サマリー
        print(f"✅ GeoJSONエクスポート完了")
        print(f"📁 出力ファイル: {output_filename}")
        print(f"📍 地点数: {len(features)}件")
        print(f"💾 ファイルサイズ: {os.path.getsize(output_filename)/1024:.1f}KB")
        
        print(f"\n📊 エクスポート統計:")
        print(f"   👤 作者数: {len(author_stats)}名")
        
        # トップ作者（地名数順）
        top_authors = sorted(author_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        print(f"   📚 主要作者（地名数順）:")
        for author, count in top_authors:
            print(f"      • {author}: {count}件")
        
        print(f"\n   🔬 抽出方法別:")
        for method, count in method_stats.items():
            print(f"      • {method}: {count}件")
        
        # 品質統計
        cursor.execute('SELECT AVG(confidence) FROM places WHERE lat IS NOT NULL AND lng IS NOT NULL')
        avg_confidence = cursor.fetchone()[0]
        print(f"\n   🎯 平均信頼度: {avg_confidence:.2f}")
        
        cursor.execute('SELECT COUNT(*) FROM places WHERE lat IS NOT NULL AND lng IS NOT NULL AND confidence >= 0.8')
        high_confidence = cursor.fetchone()[0]
        print(f"   ⭐ 高信頼度地名（≥0.8）: {high_confidence}件")
        
        conn.close()
        
        print(f"\n🎉 GeoJSONエクスポート成功！")
        print("=" * 60)
        
        return output_filename
        
    except Exception as e:
        print(f"❌ エクスポートエラー: {e}")
        return None


if __name__ == "__main__":
    export_updated_geojson() 