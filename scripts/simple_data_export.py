#!/usr/bin/env python3
"""
文豪地図システム - 簡単データ出力
既存のデータベースからデータを取得・出力
"""

import sqlite3
import os
import json
import csv
from datetime import datetime
from pathlib import Path

def find_database():
    """利用可能なデータベースファイルを検索"""
    possible_paths = [
        "bungo_project_v3/data/bungo_production.db",
        "bungo_project_v2/data/bungo_production.db", 
        "bungo_project/data/bungo_production.db",
        "data/bungo_production.db"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def export_database_info(db_path):
    """データベース情報をエクスポート"""
    print(f"🗺️ 文豪地図システム - データ出力")
    print("=" * 50)
    print(f"📁 使用データベース: {db_path}")
    
    # 出力ディレクトリ作成
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row  # 辞書形式で取得
        cursor = conn.cursor()
        
        # テーブル一覧取得
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n📋 テーブル一覧: {tables}")
        
        results = {}
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"📊 {table}: {count}件")
                
                # データサンプル取得
                cursor.execute(f"SELECT * FROM {table} LIMIT 5")
                sample_data = [dict(row) for row in cursor.fetchall()]
                
                results[table] = {
                    "count": count,
                    "sample": sample_data
                }
                
                # CSVエクスポート
                cursor.execute(f"SELECT * FROM {table}")
                all_data = [dict(row) for row in cursor.fetchall()]
                
                if all_data:
                    csv_path = output_dir / f"{table}.csv"
                    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                        fieldnames = all_data[0].keys()
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(all_data)
                    print(f"   ✅ CSV出力: {csv_path}")
                
            except Exception as e:
                print(f"   ❌ {table}テーブルエラー: {e}")
        
        # 結合データエクスポート
        try:
            # places テーブルがある場合、結合クエリ実行
            if 'places' in tables and 'works' in tables and 'authors' in tables:
                print(f"\n🔗 統合データ作成中...")
                
                query = """
                SELECT 
                    a.name as author_name,
                    w.title as work_title,
                    p.place_name,
                    p.lat,
                    p.lng,
                    p.sentence,
                    p.confidence
                FROM places p
                LEFT JOIN works w ON p.work_id = w.work_id  
                LEFT JOIN authors a ON w.author_id = a.author_id
                ORDER BY a.name, w.title, p.place_name
                """
                
                cursor.execute(query)
                unified_data = [dict(row) for row in cursor.fetchall()]
                
                if unified_data:
                    # JSON出力
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    json_path = output_dir / f"bungo_unified_{timestamp}.json"
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(unified_data, f, ensure_ascii=False, indent=2)
                    print(f"   ✅ JSON出力: {json_path} ({len(unified_data)}件)")
                    
                    # CSV出力
                    csv_path = output_dir / f"bungo_unified_{timestamp}.csv"
                    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                        if unified_data:
                            fieldnames = unified_data[0].keys()
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(unified_data)
                    print(f"   ✅ CSV出力: {csv_path} ({len(unified_data)}件)")
                    
                    # サンプル表示
                    print(f"\n📄 データサンプル（最初の3件）:")
                    for i, item in enumerate(unified_data[:3]):
                        print(f"   {i+1}. 著者: {item.get('author_name', 'N/A')}")
                        print(f"      作品: {item.get('work_title', 'N/A')}")
                        print(f"      地名: {item.get('place_name', 'N/A')}")
                        print(f"      座標: ({item.get('lat', 'N/A')}, {item.get('lng', 'N/A')})")
                        print(f"      文章: {item.get('sentence', 'N/A')[:50]}...")
                        print()
                
        except Exception as e:
            print(f"   ❌ 統合データエラー: {e}")
        
        # 結果JSON出力
        results_path = output_dir / f"database_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n🎉 出力完了!")
        print(f"📂 出力先: {output_dir.absolute()}")
        print(f"📋 情報ファイル: {results_path}")

def main():
    """メイン実行"""
    db_path = find_database()
    
    if not db_path:
        print("❌ データベースファイルが見つかりません")
        print("以下のパスを確認してください:")
        print("  - bungo_project_v3/data/bungo_production.db")
        print("  - bungo_project_v2/data/bungo_production.db")
        print("  - bungo_project/data/bungo_production.db")
        return
    
    export_database_info(db_path)

if __name__ == "__main__":
    main() 