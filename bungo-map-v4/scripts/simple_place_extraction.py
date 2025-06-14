#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗺️ 簡易地名抽出・AI Geocoding

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

try:
    # v3の優秀なモジュールをインポート
    from bungo_map.extractors.simple_place_extractor import SimplePlaceExtractor
    from bungo_map.extractors.enhanced_place_extractor import EnhancedPlaceExtractor
    from bungo_map.ai.context_aware_geocoding import ContextAwareGeocodingService
    V3_AVAILABLE = True
    print("✅ v3モジュール読み込み成功")
except ImportError as e:
    print(f"⚠️ v3モジュール読み込み失敗: {e}")
    V3_AVAILABLE = False

class SimplePlaceExtractionService:
    """簡易地名抽出・Geocodingサービス"""
    
    def __init__(self, db_path: str = '/app/data/bungo_production.db'):
        self.db_path = db_path
        
        print("🔧 簡易地名抽出システム初期化中...")
        
        if V3_AVAILABLE:
            self.simple_extractor = SimplePlaceExtractor()
            self.enhanced_extractor = EnhancedPlaceExtractor()
            self.ai_geocoding = ContextAwareGeocodingService()
            print("✅ v3地名抽出・Geocodingシステム初期化完了")
        else:
            print("⚠️ v3システム利用不可、簡易正規表現を使用")
        
        # データベース準備
        self._setup_database()
    
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
    
    def extract_all_places(self):
        """全センテンスから地名抽出実行"""
        print("🚀 全センテンス地名抽出開始")
        
        # 既存地名データクリア
        self._clear_place_data()
        
        # センテンス取得
        sentences = self._get_text_sentences()
        print(f"📝 処理対象センテンス: {len(sentences)}件")
        
        total_places = 0
        total_geocoded = 0
        
        for i, sentence in enumerate(sentences, 1):
            if i % 50 == 0:
                print(f"📝 進捗: {i}/{len(sentences)}")
            
            try:
                # 地名抽出
                if V3_AVAILABLE:
                    places = self._extract_places_v3(sentence)
                else:
                    places = self._extract_places_simple(sentence)
                
                total_places += len(places)
                
                # AI Geocoding（v3利用可能時のみ）
                if V3_AVAILABLE and places:
                    geocoded = self._execute_ai_geocoding(places)
                    total_geocoded += geocoded
                
            except Exception as e:
                print(f"⚠️ センテンス処理エラー (ID: {sentence['sentence_id']}): {e}")
                continue
        
        # 結果表示
        print(f"\n{'='*80}")
        print(f"🎉 地名抽出完了")
        print(f"📝 処理センテンス数: {len(sentences)}")
        print(f"🗺️ 抽出地名数: {total_places}")
        if V3_AVAILABLE:
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
    
    def _get_text_sentences(self) -> List[Dict[str, Any]]:
        """テキストセンテンス取得（HTML除外）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT sentence_id, work_id, sentence_text, before_text, after_text, position_in_work
                FROM sentences
                WHERE sentence_text NOT LIKE '%<html%'
                  AND sentence_text NOT LIKE '%<head%'
                  AND sentence_text NOT LIKE '%<meta%'
                  AND sentence_text NOT LIKE '%<body%'
                  AND sentence_text NOT LIKE '%<div%'
                  AND LENGTH(sentence_text) >= 10
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
    
    def _extract_places_v3(self, sentence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """v3システムで地名抽出"""
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
        unique_places = []
        seen = set()
        for place in all_extracted:
            key = (place.place_name, place.extraction_method)
            if key not in seen:
                seen.add(key)
                unique_places.append(place)
        
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
                    place.before_text or '',
                    place.after_text or '',
                    place.confidence,
                    place.extraction_method,
                    0
                ))
                
                # placesテーブルにも保存
                conn.execute('''
                    INSERT OR IGNORE INTO places 
                    (work_id, place_name, sentence, before_text, after_text,
                     confidence, extraction_method, geocoding_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    work_id,
                    place.place_name,
                    sentence_text,
                    place.before_text or '',
                    place.after_text or '',
                    place.confidence,
                    place.extraction_method,
                    'pending'
                ))
                
                extracted_places.append({
                    'place_name': place.place_name,
                    'sentence_text': sentence_text,
                    'before_text': sentence.get('before_text', ''),
                    'after_text': sentence.get('after_text', ''),
                    'confidence': place.confidence,
                    'extraction_method': place.extraction_method
                })
            
            conn.commit()
        
        return extracted_places
    
    def _extract_places_simple(self, sentence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """簡易正規表現で地名抽出"""
        sentence_text = sentence['sentence_text']
        sentence_id = sentence['sentence_id']
        work_id = sentence['work_id']
        
        # 簡易地名パターン
        place_patterns = [
            (r'[北海青森岩手宮城秋田山形福島茨城栃木群馬埼玉千葉東京神奈川新潟富山石川福井山梨長野岐阜静岡愛知三重滋賀京都大阪兵庫奈良和歌山鳥取島根岡山広島山口徳島香川愛媛高知福岡佐賀長崎熊本大分宮崎鹿児島沖縄][都道府県]', '都道府県', 0.9),
            (r'[一-龯]{2,6}[市区町村]', '市区町村', 0.8),
            (r'[一-龯]{2,4}[郡]', '郡', 0.7),
            (r'(?:東京|大阪|京都|名古屋|横浜|神戸|札幌|仙台|広島|福岡)', '主要都市', 0.9),
        ]
        
        extracted_places = []
        
        with sqlite3.connect(self.db_path) as conn:
            for pattern, category, confidence in place_patterns:
                matches = re.finditer(pattern, sentence_text)
                for match in matches:
                    place_name = match.group()
                    
                    # sentence_placesテーブルに保存
                    cursor = conn.execute('''
                        INSERT INTO sentence_places 
                        (sentence_id, place_name, context_before, context_after, 
                         confidence, extraction_method, position_in_sentence)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        sentence_id,
                        place_name,
                        sentence.get('before_text', ''),
                        sentence.get('after_text', ''),
                        confidence,
                        f'simple_{category}',
                        match.start()
                    ))
                    
                    # placesテーブルにも保存
                    conn.execute('''
                        INSERT OR IGNORE INTO places 
                        (work_id, place_name, sentence, before_text, after_text,
                         confidence, extraction_method, geocoding_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        work_id,
                        place_name,
                        sentence_text,
                        sentence.get('before_text', ''),
                        sentence.get('after_text', ''),
                        confidence,
                        f'simple_{category}',
                        'pending'
                    ))
                    
                    extracted_places.append({
                        'place_name': place_name,
                        'sentence_text': sentence_text,
                        'confidence': confidence,
                        'extraction_method': f'simple_{category}'
                    })
            
            conn.commit()
        
        return extracted_places
    
    def _execute_ai_geocoding(self, places: List[Dict[str, Any]]) -> int:
        """AI Geocoding実行"""
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
                        place_data.get('before_text', ''),
                        place_data.get('after_text', '')
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
            
            if V3_AVAILABLE:
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
    print("🗺️ 簡易地名抽出・AI Geocoding実行開始")
    print("=" * 80)
    
    service = SimplePlaceExtractionService()
    
    # 地名抽出実行
    service.extract_all_places()
    
    # 結果統計表示
    stats = service.get_statistics()
    
    print(f"\n{'='*80}")
    print(f"📊 地名抽出最終結果")
    print(f"{'='*80}")
    print(f"📝 センテンス数: {stats['sentences']:,}")
    print(f"🗺️ センテンス内地名数: {stats['sentence_places']:,}")
    print(f"📍 固有地名数: {stats['unique_places']:,}")
    
    if V3_AVAILABLE:
        print(f"🌍 Geocoding成功: {stats.get('geocoding_success', 0):,}")
        print(f"❌ Geocoding失敗: {stats.get('geocoding_failed', 0):,}")
        print(f"📊 Geocoding成功率: {stats.get('geocoding_success_rate', 0):.1f}%")
        print(f"✅ v3地名抽出・AI Geocoding統合完了！")
    else:
        print(f"✅ 簡易地名抽出完了！")


if __name__ == "__main__":
    main()