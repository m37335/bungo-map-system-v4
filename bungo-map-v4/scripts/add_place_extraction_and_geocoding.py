#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗺️ 地名抽出・AI Geocoding追加実行

既存のsentencesテーブルから地名抽出し、
v3のAI文脈判断型Geocodingで座標取得を実行
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
from bungo_map.extractors.simple_place_extractor import SimplePlaceExtractor
from bungo_map.extractors.enhanced_place_extractor import EnhancedPlaceExtractor
from bungo_map.ai.context_aware_geocoding import ContextAwareGeocodingService

class PlaceExtractionAndGeocodingService:
    """地名抽出・Geocodingサービス"""
    
    def __init__(self, db_path: str = '/app/data/bungo_production.db'):
        self.db_path = db_path
        
        # v3の優秀なコンポーネント初期化
        print("🔧 地名抽出・Geocodingシステム初期化中...")
        self.simple_extractor = SimplePlaceExtractor()
        self.enhanced_extractor = EnhancedPlaceExtractor()
        self.ai_geocoding = ContextAwareGeocodingService()
        
        # データベース準備
        self._setup_database()
        print("✅ 地名抽出・Geocodingシステム初期化完了")
    
    def _setup_database(self):
        """データベーステーブル準備"""
        print("🗃️ データベーステーブル準備中...")
        
        with sqlite3.connect(self.db_path) as conn:
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
    
    def extract_and_geocode_all(self):
        """全センテンスから地名抽出・Geocoding実行"""
        print("🚀 全センテンス地名抽出・Geocoding開始")
        
        # 既存地名データクリア
        self._clear_place_data()
        
        # センテンス取得
        sentences = self._get_sentences()
        print(f"📝 処理対象センテンス: {len(sentences)}件")
        
        total_places = 0
        total_geocoded = 0
        
        for i, sentence in enumerate(sentences, 1):
            if i % 10 == 0:
                print(f"📝 進捗: {i}/{len(sentences)}")
            
            # HTMLタグをスキップ
            if self._is_html_content(sentence['sentence_text']):
                continue
            
            # 短すぎる文をスキップ
            if len(sentence['sentence_text'].strip()) < 10:
                continue
            
            try:
                # 地名抽出
                places = self._extract_places_from_sentence(sentence)
                total_places += len(places)
                
                # AI Geocoding
                geocoded = self._execute_ai_geocoding_for_places(places)
                total_geocoded += geocoded
                
            except Exception as e:
                print(f"⚠️ センテンス処理エラー (ID: {sentence['sentence_id']}): {e}")
                continue
        
        # 結果表示
        print(f"\n{'='*80}")
        print(f"🎉 地名抽出・Geocoding完了")
        print(f"📝 処理センテンス数: {len(sentences)}")
        print(f"🗺️ 抽出地名数: {total_places}")
        print(f"🌍 Geocoding成功: {total_geocoded}")
        if total_places > 0:
            print(f"📊 Geocoding成功率: {(total_geocoded/total_places*100):.1f}%")
    
    def _clear_place_data(self):
        """既存地名データクリア"""
        print("🗑️ 既存地名データクリア中...")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM sentence_places')
            conn.execute('DELETE FROM places WHERE work_id IS NOT NULL')
            conn.execute('DELETE FROM sqlite_sequence WHERE name IN ("sentence_places")')
            conn.commit()
            print("✅ 地名データクリア完了")
    
    def _get_sentences(self) -> List[Dict[str, Any]]:
        """全センテンス取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT sentence_id, work_id, sentence_text, before_text, after_text, position_in_work
                FROM sentences
                ORDER BY work_id, position_in_work
            ''')
            
            sentences = []
            for row in cursor.fetchall():
                sentences.append({
                    'sentence_id': row[0],
                    'work_id': row[1],
                    'sentence_text': row[2],
                    'before_text': row[3],
                    'after_text': row[4],
                    'position_in_work': row[5]
                })
            
            return sentences
    
    def _is_html_content(self, text: str) -> bool:
        """HTMLコンテンツ判定"""
        html_patterns = [
            r'<html',
            r'<head>',
            r'<meta',
            r'<title>',
            r'<body>',
            r'<div',
            r'<p>',
            r'<script',
            r'<style',
            r'<link'
        ]
        
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in html_patterns)
    
    def _extract_places_from_sentence(self, sentence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """センテンスから地名抽出"""
        sentence_text = sentence['sentence_text']
        sentence_id = sentence['sentence_id']
        work_id = sentence['work_id']
        
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
        
        extracted_places = []
        
        with sqlite3.connect(self.db_path) as conn:
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
                
                extracted_places.append({
                    'place_id': place_id,
                    'place_name': place.place_name,
                    'sentence_text': sentence_text,
                    'before_text': sentence.get('before_text', ''),
                    'after_text': sentence.get('after_text', ''),
                    'confidence': place.confidence,
                    'extraction_method': place.extraction_method
                })
            
            conn.commit()
        
        return extracted_places
    
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
    
    def _execute_ai_geocoding_for_places(self, places: List[Dict[str, Any]]) -> int:
        """地名リストのAI Geocoding実行"""
        if not places:
            return 0
        
        geocoded_count = 0
        
        # 地名ごとに一意に処理
        unique_places = {}
        for place in places:
            place_name = place['place_name']
            if place_name not in unique_places:
                unique_places[place_name] = place
        
        with sqlite3.connect(self.db_path) as conn:
            for place_name, place_data in unique_places.items():
                try:
                    # v3のAI文脈判断型Geocodingを使用
                    result = self.ai_geocoding.geocode_place_sync(
                        place_name,
                        place_data['sentence_text'],
                        place_data['before_text'] or '',
                        place_data['after_text'] or ''
                    )
                    
                    if result and result.latitude is not None:
                        # 成功：座標更新
                        conn.execute('''
                            UPDATE places 
                            SET latitude = ?, longitude = ?, 
                                geocoding_source = ?, geocoding_confidence = ?,
                                geocoding_status = 'success'
                            WHERE place_name = ? AND geocoding_status = 'pending'
                        ''', (
                            result.latitude,
                            result.longitude,
                            result.source,
                            result.confidence,
                            place_name
                        ))
                        
                        geocoded_count += 1
                        print(f"  🌍 {place_name}: ({result.latitude:.4f}, {result.longitude:.4f}) [{result.source}]")
                        
                    else:
                        # 失敗：ステータス更新
                        conn.execute('''
                            UPDATE places 
                            SET geocoding_status = 'failed'
                            WHERE place_name = ? AND geocoding_status = 'pending'
                        ''', (place_name,))
                
                except Exception as e:
                    print(f"  ⚠️ {place_name}: Geocodingエラー - {e}")
                    
                # API負荷軽減
                time.sleep(0.1)
            
            conn.commit()
        
        return geocoded_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計取得"""
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
            
            # Geocoding統計
            cursor = conn.execute('SELECT COUNT(*) FROM places WHERE latitude IS NOT NULL')
            stats['geocoded_places'] = cursor.fetchone()[0]
            
            cursor = conn.execute('SELECT COUNT(*) FROM places WHERE geocoding_status = "success"')
            stats['geocoding_success'] = cursor.fetchone()[0]
            
            cursor = conn.execute('SELECT COUNT(*) FROM places WHERE geocoding_status = "failed"')
            stats['geocoding_failed'] = cursor.fetchone()[0]
            
            # 成功率計算
            total_places = stats['unique_places']
            if total_places > 0:
                stats['geocoding_success_rate'] = (stats['geocoding_success'] / total_places) * 100
            else:
                stats['geocoding_success_rate'] = 0
            
            return stats


def main():
    """メイン実行関数"""
    print("🗺️ 地名抽出・AI Geocoding追加実行開始")
    print("=" * 80)
    
    service = PlaceExtractionAndGeocodingService()
    
    # 地名抽出・Geocoding実行
    service.extract_and_geocode_all()
    
    # 結果統計表示
    stats = service.get_statistics()
    
    print(f"\n{'='*80}")
    print(f"📊 地名抽出・AI Geocoding最終結果")
    print(f"{'='*80}")
    print(f"📝 センテンス数: {stats['sentences']:,}")
    print(f"🗺️ センテンス内地名数: {stats['sentence_places']:,}")
    print(f"📍 固有地名数: {stats['unique_places']:,}")
    print(f"🌍 Geocoding成功: {stats['geocoding_success']:,}")
    print(f"❌ Geocoding失敗: {stats['geocoding_failed']:,}")
    print(f"📊 Geocoding成功率: {stats['geocoding_success_rate']:.1f}%")
    print(f"✅ v3地名抽出・AI Geocoding統合完了！")


if __name__ == "__main__":
    main()