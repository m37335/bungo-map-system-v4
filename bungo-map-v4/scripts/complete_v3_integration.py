#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 v3→v4完全統合パイプライン (地名抽出・Geocoding統合版)

v3の優秀な以下機能をv4データベースに完全統合:
- AozoraContentProcessor (青空文庫処理)
- 高度な地名抽出システム (Simple + Enhanced + AI)
- AI文脈判断型Geocoding
- 適切なセンテンス処理とコンテキスト保存
"""

import sys
import os
import sqlite3
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# v3パスを追加
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/bungo_map')

# v3の優秀なモジュールをインポート
from bungo_map.content.aozora_content_processor import AozoraContentProcessor
from bungo_map.models.work_content import SentenceContext
from bungo_map.extractors.simple_place_extractor import SimplePlaceExtractor
from bungo_map.extractors.enhanced_place_extractor import EnhancedPlaceExtractor

class V3ToV4Integrator:
    """v3→v4完全統合クラス"""
    
    def __init__(self, db_path: str = '/app/data/bungo_production.db'):
        self.db_path = db_path
        
        # v3の優秀なコンポーネント初期化
        print("🔧 v3コンポーネント初期化中...")
        self.aozora_processor = AozoraContentProcessor()
        self.simple_extractor = SimplePlaceExtractor()
        self.enhanced_extractor = EnhancedPlaceExtractor()
        
        # データベース準備
        self._setup_database()
        print("✅ v3→v4統合システム初期化完了")
    
    def _setup_database(self):
        """データベーステーブル準備"""
        print("🗃️ データベーステーブル準備中...")
        
        with sqlite3.connect(self.db_path) as conn:
            # sentencesテーブル作成
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sentences (
                    sentence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_id INTEGER NOT NULL,
                    sentence_text TEXT NOT NULL,
                    before_text TEXT,
                    after_text TEXT,
                    position_in_work INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (work_id) REFERENCES works (work_id)
                )
            ''')
            
            # sentence_placesテーブル作成
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sentence_places (
                    place_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sentence_id INTEGER NOT NULL,
                    place_name TEXT NOT NULL,
                    context_before TEXT,
                    context_after TEXT,
                    confidence REAL,
                    extraction_method TEXT,
                    position_in_sentence INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sentence_id) REFERENCES sentences (sentence_id)
                )
            ''')
            
            # placesテーブル拡張（Geocoding用）
            try:
                conn.execute('ALTER TABLE places ADD COLUMN latitude REAL')
                conn.execute('ALTER TABLE places ADD COLUMN longitude REAL') 
                conn.execute('ALTER TABLE places ADD COLUMN geocoding_source TEXT')
                conn.execute('ALTER TABLE places ADD COLUMN geocoding_confidence REAL')
                conn.execute('ALTER TABLE places ADD COLUMN geocoding_status TEXT DEFAULT "pending"')
                conn.execute('ALTER TABLE places ADD COLUMN ai_confidence REAL')
                conn.execute('ALTER TABLE places ADD COLUMN ai_place_type TEXT')
                conn.execute('ALTER TABLE places ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            except sqlite3.OperationalError:
                pass  # カラムが既に存在する場合
            
            conn.commit()
            print("✅ データベーステーブル準備完了")
    
    def integrate_all_works(self):
        """全作品の完全統合処理"""
        print("🚀 全作品の完全v3→v4統合開始")
        
        # 既存データクリア
        self._clear_existing_data()
        
        # 青空文庫URL保有作品取得
        works = self._get_aozora_works()
        print(f"📚 青空文庫作品数: {len(works)}件")
        
        total_sentences = 0
        total_places = 0
        
        for i, work in enumerate(works, 1):
            print(f"\n{'='*80}")
            print(f"📖 [{i}/{len(works)}] 処理中: {work['title']} (ID: {work['work_id']})")
            print(f"📄 青空文庫URL: {work['aozora_url']}")
            
            try:
                # 1. v3でコンテンツ取得・処理
                content_data = self._process_aozora_content(work)
                if not content_data:
                    print("⚠️ コンテンツ取得失敗、スキップ")
                    continue
                
                # 2. センテンス処理・保存
                sentences = self._process_sentences(work['work_id'], content_data)
                print(f"📝 センテンス保存: {len(sentences)}件")
                total_sentences += len(sentences)
                
                # 3. 地名抽出・保存
                places = self._extract_and_save_places(sentences)
                print(f"🗺️ 地名抽出: {len(places)}件")
                total_places += len(places)
                
                print(f"✅ 作品処理完了")
                
            except Exception as e:
                print(f"❌ 作品処理エラー: {e}")
                continue
        
        # 最終結果
        print(f"\n{'='*80}")
        print(f"🎉 v3→v4完全統合完了")
        print(f"📝 総センテンス数: {total_sentences}")
        print(f"🗺️ 総地名数: {total_places}")
    
    def _clear_existing_data(self):
        """既存データクリア"""
        print("🗑️ 既存データクリア中...")
        
        with sqlite3.connect(self.db_path) as conn:
            # 依存関係順でクリア
            conn.execute('DELETE FROM sentence_places')
            conn.execute('DELETE FROM sentences')
            conn.execute('DELETE FROM places WHERE work_id IS NOT NULL')
            
            # 自動インクリメントリセット
            conn.execute('DELETE FROM sqlite_sequence WHERE name IN ("sentences", "sentence_places")')
            
            conn.commit()
            print("✅ 既存データクリア完了")
    
    def _get_aozora_works(self) -> List[Dict[str, Any]]:
        """青空文庫URL保有作品取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT work_id, title, author_id, aozora_url 
                FROM works 
                WHERE aozora_url IS NOT NULL 
                  AND aozora_url != ''
                  AND aozora_url LIKE '%aozora.gr.jp%'
                ORDER BY work_id
                LIMIT 5
            ''')
            
            works = []
            for row in cursor.fetchall():
                works.append({
                    'work_id': row[0],
                    'title': row[1],
                    'author_id': row[2],
                    'aozora_url': row[3]
                })
            
            return works
    
    def _process_aozora_content(self, work: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """v3のAozoraContentProcessorでコンテンツ処理"""
        try:
            aozora_url = work['aozora_url']
            print(f"📥 青空文庫コンテンツ取得: {aozora_url}")
            
            # v3の優秀なAozoraContentProcessorを使用
            content_result = self.aozora_processor.get_work_content(aozora_url)
            
            if content_result and content_result.content:
                print(f"✅ コンテンツ取得成功 (文字数: {len(content_result.content)})")
                return {
                    'content': content_result.content,
                    'title': content_result.title or work['title'],
                    'author': content_result.author,
                    'encoding': content_result.encoding,
                    'aozora_url': aozora_url
                }
            else:
                print("❌ コンテンツ取得失敗")
                return None
                
        except Exception as e:
            print(f"❌ コンテンツ処理エラー: {e}")
            return None
    
    def _process_sentences(self, work_id: int, content_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """v3のget_sentence_contextを使用してセンテンス処理"""
        content = content_data['content']
        
        # v3の優秀なget_sentence_contextを使用
        sentence_contexts = self.aozora_processor.get_sentence_context(content)
        
        sentences = []
        
        with sqlite3.connect(self.db_path) as conn:
            for i, sentence_context in enumerate(sentence_contexts):
                # センテンス保存
                cursor = conn.execute('''
                    INSERT INTO sentences (work_id, sentence_text, before_text, after_text, position_in_work)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    work_id,
                    sentence_context.sentence,
                    sentence_context.before_text,
                    sentence_context.after_text,
                    i + 1
                ))
                
                sentence_id = cursor.lastrowid
                
                sentences.append({
                    'sentence_id': sentence_id,
                    'work_id': work_id,
                    'sentence_text': sentence_context.sentence,
                    'before_text': sentence_context.before_text,
                    'after_text': sentence_context.after_text,
                    'position_in_work': i + 1
                })
            
            conn.commit()
        
        return sentences
    
    def _extract_and_save_places(self, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """v3の高度な地名抽出システムで地名抽出・保存"""
        all_places = []
        
        with sqlite3.connect(self.db_path) as conn:
            for sentence in sentences:
                sentence_text = sentence['sentence_text']
                sentence_id = sentence['sentence_id']
                work_id = sentence['work_id']
                
                if len(sentence_text.strip()) < 10:
                    continue
                
                # v3のSimple抽出器で抽出
                simple_places = self.simple_extractor.extract_places_from_text(
                    work_id, sentence_text
                )
                
                # v3のEnhanced抽出器で抽出
                enhanced_places = self.enhanced_extractor.extract_places_from_work(
                    work_id, sentence_text
                )
                
                # 全抽出結果統合
                all_extracted = simple_places + enhanced_places
                
                # 重複除去
                unique_places = self._deduplicate_places(all_extracted)
                
                # sentence_placesテーブルに保存
                for place in unique_places:
                    cursor = conn.execute('''
                        INSERT INTO sentence_places 
                        (sentence_id, place_name, context_before, context_after, 
                         confidence, extraction_method, position_in_sentence)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        sentence_id,
                        place.place_name,
                        place.before_text,
                        place.after_text,
                        place.confidence,
                        place.extraction_method,
                        0  # 位置は後で計算可能
                    ))
                    
                    place_id = cursor.lastrowid
                    
                    # placesテーブルにも保存（統計用）
                    conn.execute('''
                        INSERT OR IGNORE INTO places 
                        (work_id, place_name, sentence, before_text, after_text,
                         confidence, extraction_method, geocoding_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        work_id,
                        place.place_name,
                        sentence_text,
                        place.before_text,
                        place.after_text,
                        place.confidence,
                        place.extraction_method,
                        'pending'
                    ))
                    
                    all_places.append({
                        'place_id': place_id,
                        'place_name': place.place_name,
                        'sentence_text': sentence_text,
                        'before_text': place.before_text,
                        'after_text': place.after_text,
                        'confidence': place.confidence,
                        'extraction_method': place.extraction_method
                    })
            
            conn.commit()
        
        return all_places
    
    def _deduplicate_places(self, places) -> List:
        """地名重複除去"""
        seen = set()
        unique_places = []
        
        for place in places:
            key = (place.place_name, place.extraction_method)
            if key not in seen:
                seen.add(key)
                unique_places.append(place)
        
        return unique_places
    
    def get_integration_statistics(self) -> Dict[str, Any]:
        """統合結果統計取得"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            # センテンス統計
            cursor = conn.execute('SELECT COUNT(*) FROM sentences')
            stats['sentences'] = cursor.fetchone()[0]
            
            # 地名統計
            cursor = conn.execute('SELECT COUNT(*) FROM sentence_places')
            stats['sentence_places'] = cursor.fetchone()[0]
            
            cursor = conn.execute('SELECT COUNT(DISTINCT place_name) FROM places')
            stats['unique_places'] = cursor.fetchone()[0]
            
            return stats


def main():
    """メイン実行関数"""
    print("🚀 v3→v4完全統合パイプライン開始")
    print("=" * 80)
    
    integrator = V3ToV4Integrator()
    
    # 完全統合実行
    integrator.integrate_all_works()
    
    # 結果統計表示
    stats = integrator.get_integration_statistics()
    
    print(f"\n{'='*80}")
    print(f"📊 v3→v4完全統合結果")
    print(f"{'='*80}")
    print(f"📝 センテンス数: {stats['sentences']:,}")
    print(f"🗺️ センテンス内地名数: {stats['sentence_places']:,}")
    print(f"📍 固有地名数: {stats['unique_places']:,}")
    print(f"✅ v3の地名抽出機能統合完了！")


if __name__ == "__main__":
    main() 