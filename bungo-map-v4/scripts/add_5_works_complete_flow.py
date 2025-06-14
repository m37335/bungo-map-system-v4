#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗾 青空文庫5作品追加→完全フロー実行

1. 青空文庫から5作品を取得・追加
2. v3システムでセンテンス分割
3. v3地名抽出システムで地名抽出
4. v3 AI Geocodingで座標取得

完全な文学地図データベース構築フロー
"""

import sys
import os
import sqlite3
import requests
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# v3パスを追加
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/bungo_map')

try:
    # v3の優秀なシステムをインポート
    from bungo_map.extractors.aozora_search import AozoraSearcher
    from bungo_map.extractors.aozora_extractor import AozoraExtractor
    from bungo_map.processors.aozora_content_processor import AozoraContentProcessor
    from bungo_map.extractors.simple_place_extractor import SimplePlaceExtractor
    from bungo_map.extractors.enhanced_place_extractor import EnhancedPlaceExtractor
    from bungo_map.ai.context_aware_geocoding import ContextAwareGeocodingService
    V3_AVAILABLE = True
    print("✅ v3統合システム読み込み成功")
except ImportError as e:
    print(f"⚠️ v3システム読み込み失敗: {e}")
    V3_AVAILABLE = False

class CompleteWorkflowExecutor:
    """青空文庫→完全フロー実行システム"""
    
    def __init__(self, db_path: str = '/app/bungo-map-v4/data/databases/bungo_v4.db'):
        self.db_path = db_path
        
        print("🔧 完全フロー実行システム初期化中...")
        
        if V3_AVAILABLE:
            # v3システム初期化
            self.searcher = AozoraSearcher()
            self.extractor = AozoraExtractor()
            self.processor = AozoraContentProcessor()
            self.simple_extractor = SimplePlaceExtractor()
            self.enhanced_extractor = EnhancedPlaceExtractor()
            self.ai_geocoding = ContextAwareGeocodingService()
            print("✅ v3統合システム初期化完了")
        else:
            print("❌ v3システム利用不可")
            sys.exit(1)
        
        # 追加予定の5作品
        self.target_works = [
            ('夏目漱石', 'こころ'),
            ('芥川龍之介', '羅生門'),
            ('太宰治', '走れメロス'),
            ('宮沢賢治', '注文の多い料理店'),
            ('樋口一葉', 'たけくらべ')
        ]
    
    def execute_complete_workflow(self):
        """完全フロー実行"""
        print("🚀 青空文庫→完全フロー実行開始")
        print("=" * 80)
        
        # フェーズ1: 作品追加
        print("\n📚 フェーズ1: 青空文庫作品追加")
        print("-" * 50)
        
        added_works = []
        for i, (author_name, work_title) in enumerate(self.target_works, 1):
            print(f"\n📖 {i}/5: {author_name} - {work_title}")
            work_id = self._add_single_work(author_name, work_title)
            if work_id:
                added_works.append((work_id, author_name, work_title))
            time.sleep(1)  # レート制限
        
        print(f"\n✅ フェーズ1完了: {len(added_works)}作品追加")
        
        # フェーズ2: 地名抽出
        print("\n🗺️ フェーズ2: 地名抽出実行")
        print("-" * 50)
        
        total_places = 0
        for work_id, author_name, work_title in added_works:
            print(f"\n🔍 地名抽出: {work_title}")
            places_count = self._extract_places_for_work(work_id)
            total_places += places_count
            print(f"  ✅ 抽出地名数: {places_count}")
        
        print(f"\n✅ フェーズ2完了: 総地名数 {total_places}")
        
        # フェーズ3: AI Geocoding
        print("\n🌍 フェーズ3: AI Geocoding実行")
        print("-" * 50)
        
        geocoded_count = self._execute_ai_geocoding_for_all()
        print(f"\n✅ フェーズ3完了: {geocoded_count}件の座標取得")
        
        # 最終統計
        self._show_final_statistics()
        
        print(f"\n🎉 完全フロー実行完了！")
    
    def _add_single_work(self, author_name: str, work_title: str) -> Optional[int]:
        """単一作品の追加"""
        try:
            # 1. 青空文庫URL検索
            aozora_url = self.searcher.search_work_url(author_name, work_title)
            if not aozora_url:
                print(f"  ❌ URL未発見")
                return None
            
            print(f"  🔗 URL: {aozora_url}")
            
            # 2. テキスト取得（簡易版）
            raw_content = self._fetch_text_content(aozora_url)
            if not raw_content or len(raw_content) < 100:
                print(f"  ❌ テキスト取得失敗")
                return None
            
            print(f"  📄 テキスト: {len(raw_content):,}文字")
            
            # 3. コンテンツ処理
            processed_result = self.processor.process_work_content(0, raw_content)
            if not processed_result['success']:
                print(f"  ❌ 処理失敗: {processed_result.get('error', 'Unknown')}")
                return None
            
            sentences = processed_result['sentences']
            main_content = processed_result['main_content']
            print(f"  📝 文分割: {len(sentences)}文")
            
            # 4. データベース追加
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
    
    def _fetch_text_content(self, url: str) -> str:
        """テキストコンテンツ取得（簡易版）"""
        try:
            # HTMLファイルのURLに変換
            if url.endswith('.html') and 'files' not in url:
                # カードページから実際のファイルURLを推測
                card_id = url.split('card')[-1].replace('.html', '')
                file_url = url.replace(f'card{card_id}.html', f'files/{card_id}_14560.html')
            else:
                file_url = url
            
            response = requests.get(file_url, timeout=30)
            content = response.content.decode('shift_jis', errors='ignore')
            return content
            
        except Exception as e:
            print(f"    ⚠️ テキスト取得エラー: {e}")
            return ""
    
    def _add_to_database(self, author_name: str, work_title: str, 
                        aozora_url: str, main_content: str, sentences: List[str]) -> Optional[int]:
        """データベースに追加"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 作家取得/作成
                author_id = self._get_or_create_author(conn, author_name)
                
                # 作品追加
                cursor = conn.execute("""
                    INSERT INTO works (title, author_id, aozora_url, content_length, sentence_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (work_title, author_id, aozora_url, len(main_content), len(sentences), datetime.now()))
                
                work_id = cursor.lastrowid
                
                # センテンス追加
                for i, sentence_text in enumerate(sentences):
                    if len(sentence_text.strip()) < 5:
                        continue
                    
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
                        before_text.strip()[:200],
                        after_text.strip()[:200],
                        i + 1,
                        datetime.now()
                    ))
                
                conn.commit()
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
            (author_name, datetime.now())
        )
        return cursor.lastrowid
    
    def _extract_places_for_work(self, work_id: int) -> int:
        """作品の地名抽出"""
        total_places = 0
        
        try:
            # センテンス取得
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT sentence_id, sentence_text, before_text, after_text
                    FROM sentences WHERE work_id = ?
                """, (work_id,))
                sentences = cursor.fetchall()
            
            # 地名抽出
            for sentence_id, sentence_text, before_text, after_text in sentences:
                # Simple抽出器
                simple_places = self.simple_extractor.extract_places_from_text(work_id, sentence_text)
                
                # Enhanced抽出器
                enhanced_places = self.enhanced_extractor.extract_places_from_work(work_id, sentence_text)
                
                # 全抽出結果
                all_places = simple_places + enhanced_places
                
                # places_masterとsentence_placesに追加
                with sqlite3.connect(self.db_path) as conn:
                    for place in all_places:
                        # places_masterに追加
                        cursor = conn.execute("""
                            INSERT OR IGNORE INTO places_master (place_name, canonical_name, place_type, confidence)
                            VALUES (?, ?, ?, ?)
                        """, (place.place_name, place.place_name, '地名', place.confidence))
                        
                        place_id = cursor.lastrowid or conn.execute(
                            "SELECT place_id FROM places_master WHERE place_name = ?", 
                            (place.place_name,)
                        ).fetchone()[0]
                        
                        # sentence_placesに追加
                        conn.execute("""
                            INSERT INTO sentence_places (
                                sentence_id, place_id, extraction_method, confidence,
                                context_before, context_after, matched_text, created_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            sentence_id, place_id, place.extraction_method, place.confidence,
                            before_text, after_text, place.place_name, datetime.now()
                        ))
                        
                        total_places += 1
                    
                    conn.commit()
        
        except Exception as e:
            print(f"    ⚠️ 地名抽出エラー: {e}")
        
        return total_places
    
    def _execute_ai_geocoding_for_all(self) -> int:
        """全地名のAI Geocoding"""
        geocoded_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 未処理地名取得
                cursor = conn.execute("""
                    SELECT place_id, place_name FROM places_master 
                    WHERE latitude IS NULL OR longitude IS NULL
                """)
                places = cursor.fetchall()
                
                print(f"  🎯 Geocoding対象: {len(places)}件")
                
                for place_id, place_name in places:
                    try:
                        # センテンス情報取得
                        cursor = conn.execute("""
                            SELECT s.sentence_text, sp.context_before, sp.context_after
                            FROM sentence_places sp
                            JOIN sentences s ON sp.sentence_id = s.sentence_id
                            WHERE sp.place_id = ? LIMIT 1
                        """, (place_id,))
                        
                        context = cursor.fetchone()
                        if context:
                            sentence_text, context_before, context_after = context
                        else:
                            sentence_text = context_before = context_after = ""
                        
                        # AI Geocoding実行
                        result = self.ai_geocoding.geocode_place_sync(
                            place_name, sentence_text, context_before, context_after
                        )
                        
                        if result and result.latitude is not None:
                            # 座標更新
                            conn.execute("""
                                UPDATE places_master 
                                SET latitude = ?, longitude = ?, 
                                    verification_status = 'verified'
                                WHERE place_id = ?
                            """, (result.latitude, result.longitude, place_id))
                            
                            geocoded_count += 1
                            print(f"    🌍 {place_name}: ({result.latitude:.4f}, {result.longitude:.4f})")
                        
                        time.sleep(0.1)  # API制限
                        
                    except Exception as e:
                        print(f"    ⚠️ {place_name}: {e}")
                        continue
                
                conn.commit()
        
        except Exception as e:
            print(f"  ❌ Geocodingエラー: {e}")
        
        return geocoded_count
    
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
            
            cursor = conn.execute("SELECT COUNT(*) FROM places_master WHERE latitude IS NOT NULL")
            geocoded_count = cursor.fetchone()[0]
            
            # 最新作品
            cursor = conn.execute("""
                SELECT a.name, w.title, w.sentence_count
                FROM authors a
                JOIN works w ON a.author_id = w.author_id
                ORDER BY w.created_at DESC
                LIMIT 5
            """)
            recent_works = cursor.fetchall()
        
        print(f"\n📊 完全フロー実行後の統計")
        print("=" * 60)
        print(f"👥 作家数: {authors_count:,}")
        print(f"📚 作品数: {works_count:,}")
        print(f"📝 センテンス数: {sentences_count:,}")
        print(f"🗺️ 地名数: {places_count:,}")
        print(f"🔗 文-地名関係数: {sentence_places_count:,}")
        print(f"🌍 Geocoding完了: {geocoded_count:,}")
        
        if places_count > 0:
            success_rate = (geocoded_count / places_count) * 100
            print(f"📈 Geocoding成功率: {success_rate:.1f}%")
        
        print(f"\n📖 追加された作品:")
        for author, title, sentences in recent_works:
            print(f"  • {author} - {title} ({sentences:,}文)")


def main():
    """メイン実行関数"""
    print("🗾 青空文庫5作品→完全フロー実行")
    print("=" * 80)
    
    executor = CompleteWorkflowExecutor()
    executor.execute_complete_workflow()


if __name__ == "__main__":
    main() 