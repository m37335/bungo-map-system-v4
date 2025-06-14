#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗾 青空文庫→v4データベース新規作品追加システム

v3の優秀な青空文庫取得システムを使用して、
v4データベースに新しい作品を追加します。
"""

import sys
import os
import sqlite3
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# v3パスを追加
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/bungo_map')

try:
    # v3の青空文庫システムをインポート
    from bungo_map.extractors.aozora_search import AozoraSearcher
    from bungo_map.extractors.aozora_extractor import AozoraExtractor
    from bungo_map.processors.aozora_content_processor import AozoraContentProcessor
    V3_AVAILABLE = True
    print("✅ v3青空文庫システム読み込み成功")
except ImportError as e:
    print(f"⚠️ v3青空文庫システム読み込み失敗: {e}")
    V3_AVAILABLE = False

class AozoraToV4Adder:
    """青空文庫→v4データベース追加システム"""
    
    def __init__(self, db_path: str = '/app/bungo-map-v4/data/databases/bungo_v4.db'):
        self.db_path = db_path
        
        print("🔧 青空文庫→v4追加システム初期化中...")
        
        if V3_AVAILABLE:
            self.searcher = AozoraSearcher()
            self.extractor = AozoraExtractor()
            self.processor = AozoraContentProcessor()
            print("✅ v3青空文庫システム初期化完了")
        else:
            print("⚠️ v3システム利用不可")
            sys.exit(1)
    
    def add_new_work(self, author_name: str, work_title: str) -> bool:
        """新しい作品をv4データベースに追加"""
        print(f"\n🎯 作品追加開始: {author_name} - {work_title}")
        print("=" * 60)
        
        try:
            # 1. 青空文庫URL検索
            aozora_url = self.searcher.search_work_url(author_name, work_title)
            if not aozora_url:
                print(f"❌ 青空文庫URL未発見: {work_title}")
                return False
            
            print(f"✅ 青空文庫URL発見: {aozora_url}")
            
            # 2. テキストコンテンツ取得
            raw_content = self.extractor.download_and_extract_text(aozora_url)
            if not raw_content or len(raw_content) < 100:
                print(f"❌ テキスト取得失敗または内容不足: {len(raw_content) if raw_content else 0}文字")
                return False
            
            print(f"✅ テキスト取得成功: {len(raw_content):,}文字")
            
            # 3. コンテンツ処理（v3システム）
            processed_result = self.processor.process_work_content(0, raw_content)
            if not processed_result['success']:
                print(f"❌ コンテンツ処理失敗: {processed_result.get('error', 'Unknown error')}")
                return False
            
            sentences = processed_result['sentences']
            main_content = processed_result['main_content']
            
            print(f"✅ コンテンツ処理成功: {len(main_content):,}文字 → {len(sentences)}文")
            
            # 4. v4データベースに追加
            work_id = self._add_to_v4_database(
                author_name=author_name,
                work_title=work_title,
                aozora_url=aozora_url,
                main_content=main_content,
                sentences=sentences
            )
            
            if work_id:
                print(f"🎉 作品追加完了: {work_title} (work_id: {work_id})")
                return True
            else:
                print(f"❌ データベース追加失敗")
                return False
                
        except Exception as e:
            print(f"❌ 作品追加エラー: {e}")
            return False
    
    def _add_to_v4_database(self, author_name: str, work_title: str, 
                           aozora_url: str, main_content: str, sentences: List[str]) -> Optional[int]:
        """v4データベースに作品データを追加"""
        print(f"🗃️ v4データベースに追加中...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 作家情報の取得または作成
                author_id = self._get_or_create_author(conn, author_name)
                
                # 作品の重複チェック
                cursor = conn.execute(
                    "SELECT work_id FROM works WHERE title = ? AND author_id = ?",
                    (work_title, author_id)
                )
                existing_work = cursor.fetchone()
                
                if existing_work:
                    print(f"⚠️ 作品が既に存在します: {work_title}")
                    return existing_work[0]
                
                # 新規作品追加
                cursor = conn.execute("""
                    INSERT INTO works (title, author_id, aozora_url, content_length, sentence_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    work_title,
                    author_id,
                    aozora_url,
                    len(main_content),
                    len(sentences),
                    datetime.now()
                ))
                
                work_id = cursor.lastrowid
                print(f"✅ 作品追加: work_id={work_id}")
                
                # センテンスデータ追加
                sentence_count = self._add_sentences(conn, work_id, author_id, sentences)
                
                # 作品の文数を更新
                conn.execute(
                    "UPDATE works SET sentence_count = ? WHERE work_id = ?",
                    (sentence_count, work_id)
                )
                
                conn.commit()
                print(f"✅ センテンス追加完了: {sentence_count}文")
                
                return work_id
                
        except Exception as e:
            print(f"❌ データベース追加エラー: {e}")
            return None
    
    def _get_or_create_author(self, conn: sqlite3.Connection, author_name: str) -> int:
        """作家情報の取得または作成"""
        # 既存作家チェック
        cursor = conn.execute(
            "SELECT author_id FROM authors WHERE name = ?",
            (author_name,)
        )
        existing_author = cursor.fetchone()
        
        if existing_author:
            return existing_author[0]
        
        # 新規作家追加
        cursor = conn.execute("""
            INSERT INTO authors (name, created_at)
            VALUES (?, ?)
        """, (author_name, datetime.now()))
        
        author_id = cursor.lastrowid
        print(f"✅ 新規作家追加: {author_name} (author_id={author_id})")
        return author_id
    
    def _add_sentences(self, conn: sqlite3.Connection, work_id: int, 
                      author_id: int, sentences: List[str]) -> int:
        """センテンスデータの追加"""
        added_count = 0
        
        for i, sentence_text in enumerate(sentences):
            if len(sentence_text.strip()) < 5:  # 短すぎる文をスキップ
                continue
            
            # 前後の文脈を設定
            before_text = sentences[i-1] if i > 0 else ""
            after_text = sentences[i+1] if i < len(sentences)-1 else ""
            
            cursor = conn.execute("""
                INSERT INTO sentences (
                    sentence_text, work_id, author_id, before_text, after_text,
                    position_in_work, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                sentence_text.strip(),
                work_id,
                author_id,
                before_text.strip(),
                after_text.strip(),
                i + 1,
                datetime.now()
            ))
            
            added_count += 1
        
        return added_count
    
    def list_available_works(self) -> List[tuple]:
        """追加可能な有名作品リスト"""
        if not V3_AVAILABLE:
            return []
        
        # v3のAozoraSearcherから既知作品を取得
        known_works = list(self.searcher.known_works.keys())
        
        # v4データベースの既存作品と比較
        existing_works = set()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT a.name, w.title
                    FROM authors a
                    JOIN works w ON a.author_id = w.author_id
                """)
                for row in cursor.fetchall():
                    existing_works.add((row[0], row[1]))
        except:
            pass
        
        # 新規追加可能な作品のみ抽出
        available_works = [work for work in known_works if work not in existing_works]
        return available_works
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """v4データベースの統計情報"""
        stats = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 基本統計
                cursor = conn.execute("SELECT COUNT(*) FROM authors")
                stats['authors'] = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM works")
                stats['works'] = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM sentences")
                stats['sentences'] = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM places_master")
                stats['places'] = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM sentence_places")
                stats['sentence_places'] = cursor.fetchone()[0]
                
                # 最新作品
                cursor = conn.execute("""
                    SELECT a.name, w.title, w.sentence_count, w.created_at
                    FROM authors a
                    JOIN works w ON a.author_id = w.author_id
                    ORDER BY w.created_at DESC
                    LIMIT 5
                """)
                stats['recent_works'] = cursor.fetchall()
                
        except Exception as e:
            stats['error'] = str(e)
        
        return stats


def main():
    """メイン実行関数"""
    print("🗾 青空文庫→v4データベース新規作品追加")
    print("=" * 60)
    
    adder = AozoraToV4Adder()
    
    # 現在の統計表示
    stats = adder.get_database_statistics()
    print(f"\n📊 現在のv4データベース統計:")
    print(f"👥 作家数: {stats.get('authors', 0):,}")
    print(f"📚 作品数: {stats.get('works', 0):,}")
    print(f"📝 文数: {stats.get('sentences', 0):,}")
    print(f"🗺️ 地名数: {stats.get('places', 0):,}")
    
    # 追加可能作品リスト表示
    available_works = adder.list_available_works()
    print(f"\n📋 追加可能な有名作品: {len(available_works)}件")
    
    if available_works:
        print("\n🎯 推奨作品（最初の10件）:")
        for i, (author, title) in enumerate(available_works[:10], 1):
            print(f"  {i:2d}. {author} - {title}")
        
        # 実際に作品を追加（例：夏目漱石の「こころ」）
        print(f"\n🚀 作品追加テスト実行...")
        
        # 追加する作品を選択（最初の作品）
        if len(available_works) > 0:
            author_name, work_title = available_works[0]
            success = adder.add_new_work(author_name, work_title)
            
            if success:
                # 更新後の統計
                updated_stats = adder.get_database_statistics()
                print(f"\n📊 追加後の統計:")
                print(f"👥 作家数: {updated_stats.get('authors', 0):,}")
                print(f"📚 作品数: {updated_stats.get('works', 0):,}")
                print(f"📝 文数: {updated_stats.get('sentences', 0):,}")
            
            print(f"\n🎉 青空文庫→v4追加処理完了！")
    else:
        print("\n✅ 追加可能な新規作品がありません（全て登録済み）")


if __name__ == "__main__":
    main()