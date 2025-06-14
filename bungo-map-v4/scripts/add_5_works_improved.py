#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗾 青空文庫5作品追加→完全フロー実行（改良版）

青空文庫URLアクセス問題を修正し、適切なテキスト取得を実行
"""

import sys
import os
import sqlite3
import requests
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse

# v3パスを追加
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/bungo_map')

# v3システムをインポート
from bungo_map.extractors.aozora_search import AozoraSearcher
from bungo_map.extractors.aozora_extractor import AozoraExtractor
from bungo_map.processors.aozora_content_processor import AozoraContentProcessor
from bungo_map.extractors.simple_place_extractor import SimplePlaceExtractor

class ImprovedWorkflowExecutor:
    """改良版青空文庫→完全フロー実行システム"""
    
    def __init__(self, db_path: str = '/app/bungo-map-v4/data/databases/bungo_v4.db'):
        self.db_path = db_path
        
        print("🔧 改良版完全フロー実行システム初期化中...")
        
        # v3システム初期化
        self.searcher = AozoraSearcher()
        self.extractor = AozoraExtractor()
        self.processor = AozoraContentProcessor()
        self.simple_extractor = SimplePlaceExtractor()
        print("✅ v3統合システム初期化完了")
        
        # 追加予定の5作品（実証済みURL付き）
        self.target_works = [
            ('夏目漱石', 'こころ', 'https://www.aozora.gr.jp/cards/000148/files/773_14560.html'),
            ('芥川龍之介', '羅生門', 'https://www.aozora.gr.jp/cards/000879/files/127_15260.html'),
            ('太宰治', '走れメロス', 'https://www.aozora.gr.jp/cards/000035/files/1567_14913.html'),
            ('宮沢賢治', '注文の多い料理店', 'https://www.aozora.gr.jp/cards/000081/files/43754_17659.html'),
            ('樋口一葉', 'たけくらべ', 'https://www.aozora.gr.jp/cards/000064/files/893_14763.html')
        ]
    
    def execute_complete_workflow(self):
        """完全フロー実行"""
        print("🚀 改良版青空文庫→完全フロー実行開始")
        print("=" * 80)
        
        # フェーズ1: 作品追加
        print("\n📚 フェーズ1: 青空文庫作品追加（改良版）")
        print("-" * 50)
        
        added_works = []
        for i, (author_name, work_title, aozora_url) in enumerate(self.target_works, 1):
            print(f"\n📖 {i}/5: {author_name} - {work_title}")
            work_id = self._add_single_work_improved(author_name, work_title, aozora_url)
            if work_id:
                added_works.append((work_id, author_name, work_title))
            time.sleep(1)  # レート制限
        
        print(f"\n✅ フェーズ1完了: {len(added_works)}作品追加")
        
        # フェーズ2: 地名抽出
        print("\n🗺️ フェーズ2: 地名抽出実行（改良版）")
        print("-" * 50)
        
        total_places = 0
        for work_id, author_name, work_title in added_works:
            print(f"\n🔍 地名抽出: {work_title}")
            places_count = self._extract_places_for_work_improved(work_id)
            total_places += places_count
            print(f"  ✅ 抽出地名数: {places_count}")
        
        print(f"\n✅ フェーズ2完了: 総地名数 {total_places}")
        
        # 最終統計
        self._show_final_statistics()
        
        print(f"\n🎉 改良版完全フロー実行完了！")
    
    def _add_single_work_improved(self, author_name: str, work_title: str, aozora_url: str) -> Optional[int]:
        """単一作品の追加（改良版）"""
        try:
            print(f"  🔗 直接ファイルURL: {aozora_url}")
            
            # 1. 実際のテキストファイルを直接取得
            raw_content = self._fetch_text_content_improved(aozora_url)
            if not raw_content or len(raw_content) < 100:
                print(f"  ❌ テキスト取得失敗: {len(raw_content) if raw_content else 0}文字")
                return None
            
            print(f"  📄 テキスト取得成功: {len(raw_content):,}文字")
            
            # 2. コンテンツ処理
            processed_result = self.processor.process_work_content(0, raw_content)
            if not processed_result['success']:
                print(f"  ❌ 処理失敗: {processed_result.get('error', 'Unknown')}")
                return None
            
            sentences = processed_result['sentences']
            main_content = processed_result['main_content']
            print(f"  📝 文分割: {len(sentences)}文（本文: {len(main_content):,}文字）")
            
            # 3. データベース追加
            work_id = self._add_to_database(
                author_name, work_title, aozora_url, main_content, sentences
            )
            
            if work_id:
                print(f"  ✅ 追加完了: work_id={work_id}")
                return work_id
            else:
                print(f"  ❌ DB追加失敗")
                return None
                
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            return None
    
    def _fetch_text_content_improved(self, url: str) -> str:
        """改良版テキストコンテンツ取得"""
        try:
            print(f"    🌐 アクセス中: {url}")
            
            # User-Agentを設定
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 文字エンコーディング判定
            if 'charset=shift_jis' in response.headers.get('content-type', ''):
                content = response.content.decode('shift_jis', errors='ignore')
            elif 'charset=utf-8' in response.headers.get('content-type', ''):
                content = response.content.decode('utf-8', errors='ignore')
            else:
                # 自動判定
                try:
                    content = response.content.decode('shift_jis', errors='ignore')
                except:
                    content = response.content.decode('utf-8', errors='ignore')
            
            print(f"    ✅ 取得成功: {len(content):,}文字")
            return content
            
        except Exception as e:
            print(f"    ❌ テキスト取得エラー: {e}")
            return ""
    
    def _add_to_database(self, author_name: str, work_title: str, 
                        aozora_url: str, main_content: str, sentences: List[str]) -> Optional[int]:
        """データベースに追加"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 作家取得/作成
                author_id = self._get_or_create_author(conn, author_name)
                
                # 重複確認
                cursor = conn.execute(
                    "SELECT work_id FROM works WHERE title = ? AND author_id = ?",
                    (work_title, author_id)
                )
                existing = cursor.fetchone()
                if existing:
                    print(f"    ⚠️ 既存作品: work_id={existing[0]}")
                    return existing[0]
                
                # 作品追加
                cursor = conn.execute("""
                    INSERT INTO works (title, author_id, aozora_url, content_length, sentence_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (work_title, author_id, aozora_url, len(main_content), len(sentences), datetime.now().isoformat()))
                
                work_id = cursor.lastrowid
                
                # センテンス追加
                valid_sentences = 0
                for i, sentence_text in enumerate(sentences):
                    cleaned_sentence = sentence_text.strip()
                    if len(cleaned_sentence) < 5:
                        continue
                    
                    before_text = sentences[i-1].strip()[:200] if i > 0 else ""
                    after_text = sentences[i+1].strip()[:200] if i < len(sentences)-1 else ""
                    
                    conn.execute("""
                        INSERT INTO sentences (
                            sentence_text, work_id, author_id, before_text, after_text,
                            position_in_work, created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        cleaned_sentence,
                        work_id,
                        author_id,
                        before_text,
                        after_text,
                        i + 1,
                        datetime.now().isoformat()
                    ))
                    valid_sentences += 1
                
                conn.commit()
                print(f"    📊 有効センテンス: {valid_sentences}/{len(sentences)}")
                return work_id
                
        except Exception as e:
            print(f"    ⚠️ DB追加エラー: {e}")
            return None
    
    def _get_or_create_author(self, conn: sqlite3.Connection, author_name: str) -> int:
        """作家取得/作成"""
        cursor = conn.execute("SELECT author_id FROM authors WHERE name = ?", (author_name,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        cursor = conn.execute(
            "INSERT INTO authors (name, created_at) VALUES (?, ?)",
            (author_name, datetime.now().isoformat())
        )
        return cursor.lastrowid
    
    def _extract_places_for_work_improved(self, work_id: int) -> int:
        """作品の地名抽出（改良版）"""
        total_places = 0
        
        try:
            # センテンス取得
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT sentence_id, sentence_text, before_text, after_text
                    FROM sentences WHERE work_id = ?
                    ORDER BY position_in_work
                """, (work_id,))
                sentences = cursor.fetchall()
                
                print(f"    📝 処理対象: {len(sentences)}文")
            
            if not sentences:
                print(f"    ⚠️ センテンスが見つかりません")
                return 0
            
            # 地名抽出（改良版）
            for sentence_id, sentence_text, before_text, after_text in sentences:
                if not sentence_text or len(sentence_text.strip()) < 5:
                    continue
                
                try:
                    # Simple抽出器で地名抽出
                    simple_places = self.simple_extractor.extract_places_from_text(work_id, sentence_text)
                    
                    # places_masterとsentence_placesに追加
                    with sqlite3.connect(self.db_path) as conn:
                        for place in simple_places:
                            try:
                                # places_masterに追加
                                cursor = conn.execute("""
                                    INSERT OR IGNORE INTO places_master (place_name, canonical_name, place_type, confidence)
                                    VALUES (?, ?, ?, ?)
                                """, (place.place_name, place.place_name, '地名', getattr(place, 'confidence', 0.8)))
                                
                                # place_id取得
                                cursor = conn.execute(
                                    "SELECT place_id FROM places_master WHERE place_name = ?", 
                                    (place.place_name,)
                                )
                                result = cursor.fetchone()
                                if not result:
                                    continue
                                place_id = result[0]
                                
                                # sentence_placesに追加
                                conn.execute("""
                                    INSERT INTO sentence_places (
                                        sentence_id, place_id, extraction_method, confidence,
                                        context_before, context_after, matched_text, created_at
                                    )
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    sentence_id, place_id, 
                                    getattr(place, 'extraction_method', 'simple'), 
                                    getattr(place, 'confidence', 0.8),
                                    before_text, after_text, place.place_name, 
                                    datetime.now().isoformat()
                                ))
                                
                                total_places += 1
                                print(f"    🗺️ 地名発見: {place.place_name}")
                                
                            except Exception as e:
                                print(f"    ⚠️ 地名追加エラー: {place.place_name} - {e}")
                                continue
                        
                        conn.commit()
                
                except Exception as e:
                    print(f"    ⚠️ センテンス処理エラー: {e}")
                    continue
        
        except Exception as e:
            print(f"    ❌ 地名抽出エラー: {e}")
        
        return total_places
    
    def _show_final_statistics(self):
        """最終統計表示"""
        with sqlite3.connect(self.db_path) as conn:
            # 基本統計
            cursor = conn.execute("SELECT COUNT(*) FROM authors")
            authors_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM works")
            works_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM sentences")
            sentences_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM places_master")
            places_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM sentence_places")
            sentence_places_count = cursor.fetchone()[0]
            
            # 最新作品
            cursor = conn.execute("""
                SELECT a.name, w.title, w.sentence_count, w.content_length
                FROM authors a
                JOIN works w ON a.author_id = w.author_id
                ORDER BY w.created_at DESC
                LIMIT 5
            """)
            recent_works = cursor.fetchall()
            
            # 地名別統計
            cursor = conn.execute("""
                SELECT pm.place_name, COUNT(sp.sentence_id) as count
                FROM places_master pm
                LEFT JOIN sentence_places sp ON pm.place_id = sp.place_id
                GROUP BY pm.place_name
                ORDER BY count DESC
                LIMIT 10
            """)
            top_places = cursor.fetchall()
        
        print(f"\n📊 改良版完全フロー実行後の統計")
        print("=" * 60)
        print(f"👥 作家数: {authors_count:,}")
        print(f"📚 作品数: {works_count:,}")
        print(f"📝 センテンス数: {sentences_count:,}")
        print(f"🗺️ 地名数: {places_count:,}")
        print(f"🔗 文-地名関係数: {sentence_places_count:,}")
        
        print(f"\n📖 追加された作品:")
        for author, title, sentences, content_length in recent_works:
            print(f"  • {author} - {title} ({sentences:,}文, {content_length:,}文字)")
        
        if top_places:
            print(f"\n🗺️ 頻出地名TOP10:")
            for place_name, count in top_places:
                print(f"  • {place_name}: {count}回")


def main():
    """メイン実行関数"""
    print("🗾 改良版青空文庫5作品→完全フロー実行")
    print("=" * 80)
    
    executor = ImprovedWorkflowExecutor()
    executor.execute_complete_workflow()


if __name__ == "__main__":
    main() 