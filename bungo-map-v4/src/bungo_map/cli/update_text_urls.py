#!/usr/bin/env python3
"""
作品のテキストURLを更新するスクリプト
"""

import os
import sqlite3
from pathlib import Path

def update_text_urls(db_path: str):
    """作品のテキストURLを更新"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 作品一覧を取得
    cursor.execute("SELECT work_id, title FROM works")
    works = cursor.fetchall()
    
    # テキストファイルのベースディレクトリ
    base_dir = Path("data/texts")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    for work in works:
        # テキストファイルのパスを生成
        text_path = base_dir / f"{work['title']}.txt"
        
        # テキストURLを更新
        cursor.execute(
            "UPDATE works SET text_url = ? WHERE work_id = ?",
            (str(text_path), work['work_id'])
        )
    
    conn.commit()
    conn.close()

def main():
    # データベースパスを環境変数から取得
    db_path = os.getenv('BUNGO_DB_PATH', 'data/databases/bungo_v4.db')
    update_text_urls(db_path)

if __name__ == '__main__':
    main() 