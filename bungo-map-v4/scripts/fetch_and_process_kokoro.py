#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
夏目漱石「こころ」テキスト取得・処理システム

青空文庫からテキストを取得して、v3の高度な処理システムで
センテンス分割してv4データベースに追加
"""

import sys
import sqlite3
import requests
import re
import time
from datetime import datetime

# v3パスを追加
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/bungo_map')

try:
    from bungo_map.processors.aozora_content_processor import AozoraContentProcessor
    print("✅ v3コンテンツ処理システム利用可能")
    V3_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ v3システム利用不可: {e}")
    V3_AVAILABLE = False

def fetch_aozora_text(url: str) -> str:
    """青空文庫からテキストを取得"""
    print(f"📥 青空文庫からテキスト取得: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Shift_JISでデコード
        content = response.content.decode('shift_jis', errors='ignore')
        print(f"✅ テキスト取得成功: {len(content):,}文字")
        return content
        
    except Exception as e:
        print(f"❌ テキスト取得エラー: {e}")
        return ""

def process_kokoro_text():
    """「こころ」のテキスト処理"""
    print("📚 夏目漱石「こころ」処理開始")
    print("=" * 50)
    
    db_path = '/app/bungo-map-v4/data/databases/bungo_v4.db'
    
    # データベースから作品情報取得
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("""
            SELECT w.work_id, w.title, w.aozora_url, a.author_id, a.name
            FROM works w
            JOIN authors a ON w.author_id = a.author_id
            WHERE w.title = 'こころ' AND a.name = '夏目漱石'
        """)
        
        work_info = cursor.fetchone()
        if not work_info:
            print("❌ 作品情報が見つかりません")
            return
        
        work_id, title, aozora_url, author_id, author_name = work_info
        print(f"📖 対象作品: {title} ({author_name})")
        print(f"🔗 URL: {aozora_url}")
    
    # テキスト取得
    raw_content = fetch_aozora_text(aozora_url)
    if not raw_content:
        return
    
    # v3コンテンツ処理システムで処理
    if V3_AVAILABLE:
        processor = AozoraContentProcessor()
        print("🔧 v3コンテンツ処理システムで処理中...")
        
        # 本文抽出・文分割
        main_content = processor.extract_main_content(raw_content)
        sentences = processor.split_into_sentences(main_content)
        
        print(f"✅ 処理完了:")
        print(f"  📄 本文: {len(main_content):,}文字")
        print(f"  📝 文数: {len(sentences)}文")
        
        # センテンス例表示
        if sentences:
            print(f"\n📝 センテンス例:")
            for i, sentence in enumerate(sentences[:3], 1):
                print(f"  {i}. {sentence[:50]}...")
    
    else:
        # 簡易処理
        print("🔧 簡易処理システムで処理中...")
        # HTMLタグ除去
        main_content = re.sub(r'<[^>]+>', '', raw_content)
        # 簡易文分割
        sentences = re.split(r'[。！？]', main_content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        
        print(f"✅ 簡易処理完了: {len(sentences)}文")
    
    # v4データベースにセンテンス追加
    print(f"\n🗃️ v4データベースにセンテンス追加中...")
    
    with sqlite3.connect(db_path) as conn:
        # 既存センテンスをクリア
        conn.execute("DELETE FROM sentences WHERE work_id = ?", (work_id,))
        
        # 新しいセンテンスを追加
        added_count = 0
        
        for i, sentence_text in enumerate(sentences):
            if len(sentence_text.strip()) < 5:
                continue
            
            # 前後の文脈設定
            before_text = sentences[i-1] if i > 0 else ""
            after_text = sentences[i+1] if i < len(sentences)-1 else ""
            
            conn.execute("""
                INSERT INTO sentences (
                    sentence_text, work_id, author_id, before_text, after_text,
                    position_in_work, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                sentence_text.strip(),
                work_id,
                author_id,
                before_text.strip()[:500],  # 長さ制限
                after_text.strip()[:500],
                i + 1,
                datetime.now()
            ))
            
            added_count += 1
        
        # 作品の文数更新
        conn.execute(
            "UPDATE works SET sentence_count = ?, content_length = ? WHERE work_id = ?",
            (added_count, len(main_content), work_id)
        )
        
        conn.commit()
        
        print(f"✅ センテンス追加完了: {added_count}文")
    
    # 最終統計
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM sentences WHERE work_id = ?", (work_id,))
        final_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM sentences")
        total_sentences = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM works")
        total_works = cursor.fetchone()[0]
    
    print(f"\n📊 処理完了統計:")
    print(f"📚 「こころ」センテンス数: {final_count:,}")
    print(f"📝 総センテンス数: {total_sentences:,}")
    print(f"📖 総作品数: {total_works:,}")
    print(f"\n🎉 夏目漱石「こころ」処理完了！")

if __name__ == "__main__":
    process_kokoro_text() 