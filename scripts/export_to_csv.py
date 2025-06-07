#!/usr/bin/env python3
"""
データベース統合・CSV出力スクリプト
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime
from pathlib import Path


def main():
    """メイン処理"""
    print("🗺️ 文豪ゆかり地図システム - データベースCSV出力")
    print("=" * 60)
    
    # データベースファイルのパス
    db_path = "data/bungo_production.db"
    
    if not os.path.exists(db_path):
        print(f"❌ データベースファイルが見つかりません: {db_path}")
        return
    
    print(f"📁 使用データベース: {db_path}")
    
    # 出力ディレクトリ作成
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # データベース接続
    with sqlite3.connect(db_path) as conn:
        # 基本統計表示
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM authors")
        author_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM works")
        work_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM places")
        place_count = cursor.fetchone()[0]
        
        print(f"\n📊 データベース概要")
        print(f"📚 著者数: {author_count}")
        print(f"📖 作品数: {work_count}")
        print(f"📍 地名数: {place_count}")
        
        print("\n📤 CSV出力開始...")
        
        # 1. 個別テーブルCSV出力
        tables = ['authors', 'works', 'places']
        for table in tables:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            output_path = output_dir / f"{table}.csv"
            df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"✅ {table}テーブル: {len(df)}件 → {output_path}")
        
        # 2. 統合データCSV出力
        query = """
        SELECT 
            a.name as author_name,
            w.title as work_title,
            w.wiki_url as work_wiki_url,
            p.place_name,
            p.lat,
            p.lng,
            p.before_text,
            p.sentence,
            p.after_text,
            p.aozora_url,
            p.confidence,
            p.extraction_method,
            a.created_at as author_created_at,
            w.created_at as work_created_at,
            p.created_at as place_created_at
        FROM places p
        JOIN works w ON p.work_id = w.work_id
        JOIN authors a ON w.author_id = a.author_id
        ORDER BY a.name, w.title, p.place_name
        """
        
        df = pd.read_sql_query(query, conn)
        
        # 統合データCSV出力
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unified_path = output_dir / f"bungo_unified_data_{timestamp}.csv"
        df.to_csv(unified_path, index=False, encoding='utf-8')
        
        print(f"✅ 統合データ: {len(df)}件 → {unified_path}")
        
        print(f"\n🎉 CSV出力完了!")
        print(f"📂 出力先: {output_dir.absolute()}")
        print(f"🌟 メインファイル: {unified_path}")


if __name__ == "__main__":
    main()