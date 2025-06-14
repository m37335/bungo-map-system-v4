"""
Bungo Map System v3.0 to v4.0 Migration

v3.0の地名中心アーキテクチャからv4.0のセンテンス中心アーキテクチャへの移行
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime


class V3ToV4Migrator:
    """v3.0からv4.0への移行クラス"""
    
    def __init__(self, v3_db_path: str, v4_db_path: str):
        self.v3_db_path = v3_db_path
        self.v4_db_path = v4_db_path
        
    def migrate(self) -> bool:
        """移行実行"""
        print("🚀 v3.0 → v4.0 移行開始...")
        
        try:
            # 1. v3.0データ読み込み
            v3_data = self._load_v3_data()
            print(f"📊 v3.0データ読み込み完了: {len(v3_data)}件")
            
            # 2. センテンス・地名の分析・正規化
            sentences, places_master = self._analyze_and_normalize(v3_data)
            print(f"📝 センテンス: {len(sentences)}件、地名マスター: {len(places_master)}件")
            
            # 3. v4.0データベースへの移行
            self._migrate_to_v4(sentences, places_master)
            print("✅ v4.0移行完了")
            
            return True
            
        except Exception as e:
            print(f"❌ 移行エラー: {e}")
            return False
    
    def migrate_limited(self, limit: int) -> bool:
        """制限付き移行実行"""
        print(f"🚀 v3.0 → v4.0 制限付き移行開始 (最大{limit}件)...")
        
        try:
            # 1. v3.0データ読み込み（制限付き）
            v3_data = self._load_v3_data_limited(limit)
            print(f"📊 v3.0データ読み込み完了: {len(v3_data)}件")
            
            # 2. センテンス・地名の分析・正規化
            sentences, places_master = self._analyze_and_normalize(v3_data)
            print(f"📝 センテンス: {len(sentences)}件、地名マスター: {len(places_master)}件")
            
            # 3. v4.0データベースへの移行
            self._migrate_to_v4(sentences, places_master)
            print("✅ v4.0制限付き移行完了")
            
            return True
            
        except Exception as e:
            print(f"❌ 移行エラー: {e}")
            return False
    
    def _load_v3_data(self) -> List[Dict[str, Any]]:
        """v3.0データベースからデータ読み込み"""
        data = []
        
        with sqlite3.connect(self.v3_db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT p.*, w.title as work_title, a.name as author_name
                FROM places p
                LEFT JOIN works w ON p.work_id = w.work_id
                LEFT JOIN authors a ON p.author_id = a.author_id
                WHERE p.sentence IS NOT NULL AND p.sentence != ''
                ORDER BY p.work_id, p.place_id
            """)
            
            for row in cursor.fetchall():
                data.append(dict(row))
        
        return data
    
    def _load_v3_data_limited(self, limit: int) -> List[Dict[str, Any]]:
        """v3.0データベースからデータ読み込み（制限付き）"""
        data = []
        
        with sqlite3.connect(self.v3_db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT p.*, w.title as work_title, a.name as author_name
                FROM places p
                LEFT JOIN works w ON p.work_id = w.work_id
                LEFT JOIN authors a ON p.author_id = a.author_id
                WHERE p.sentence IS NOT NULL AND p.sentence != ''
                ORDER BY p.work_id, p.place_id
                LIMIT ?
            """, (limit,))
            
            for row in cursor.fetchall():
                data.append(dict(row))
        
        return data
    
    def _analyze_and_normalize(self, v3_data: List[Dict]) -> tuple:
        """v3.0データの分析・正規化"""
        sentences_map = {}  # sentence_text -> sentence_info
        places_master_map = {}  # canonical_name -> place_info
        
        for item in v3_data:
            sentence_text = item['sentence']
            place_name = item['place_name']
            
            # センテンス正規化
            normalized_sentence = self._normalize_sentence(sentence_text)
            
            if normalized_sentence not in sentences_map:
                sentences_map[normalized_sentence] = {
                    'sentence_text': sentence_text,
                    'work_id': item['work_id'],
                    'author_id': item['author_id'],
                    'before_text': item.get('before_text', ''),
                    'after_text': item.get('after_text', ''),
                    'places': [],
                    'source_info': f"v3移行: {item.get('work_title', '')}"
                }
            
            # 地名正規化・マスター化
            canonical_name = self._normalize_place_name(place_name)
            
            if canonical_name not in places_master_map:
                places_master_map[canonical_name] = {
                    'place_name': place_name,
                    'canonical_name': canonical_name,
                    'aliases': [place_name] if place_name != canonical_name else [],
                    'latitude': item.get('lat'),
                    'longitude': item.get('lng'),
                    'place_type': self._determine_place_type(item.get('extraction_method', '')),
                    'confidence': item.get('confidence', 0.0),
                    'source_system': 'v3.0',
                    'extraction_methods': [item.get('extraction_method', '')]
                }
            else:
                # 別名追加
                existing = places_master_map[canonical_name]
                if place_name not in existing['aliases'] and place_name != existing['place_name']:
                    existing['aliases'].append(place_name)
                
                # 抽出手法追加
                method = item.get('extraction_method', '')
                if method and method not in existing['extraction_methods']:
                    existing['extraction_methods'].append(method)
                
                # 座標情報更新（より信頼度の高いものを優先）
                if item.get('lat') and item.get('lng'):
                    if (not existing['latitude'] or 
                        item.get('confidence', 0.0) > existing['confidence']):
                        existing['latitude'] = item.get('lat')
                        existing['longitude'] = item.get('lng')
                        existing['confidence'] = item.get('confidence', 0.0)
            
            # センテンス-地名関連追加
            sentences_map[normalized_sentence]['places'].append({
                'place_name': place_name,
                'canonical_name': canonical_name,
                'extraction_method': item.get('extraction_method', ''),
                'confidence': item.get('confidence', 0.0),
                'matched_text': place_name
            })
        
        return list(sentences_map.values()), list(places_master_map.values())
    
    def _migrate_to_v4(self, sentences: List[Dict], places_master: List[Dict]):
        """v4.0データベースへの移行実行"""
        with sqlite3.connect(self.v4_db_path) as conn:
            # 1. 地名マスター挿入
            place_id_map = {}  # canonical_name -> place_id
            
            for place in places_master:
                cursor = conn.execute("""
                    INSERT INTO places_master (
                        place_name, canonical_name, aliases, latitude, longitude,
                        place_type, confidence, source_system, verification_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    place['place_name'],
                    place['canonical_name'],
                    json.dumps(place['aliases'], ensure_ascii=False),
                    place['latitude'],
                    place['longitude'],
                    place['place_type'],
                    place['confidence'],
                    place['source_system'],
                    'verified'  # v3.0からの移行は検証済みとする
                ))
                
                place_id_map[place['canonical_name']] = cursor.lastrowid
            
            # 2. センテンス挿入
            for sentence in sentences:
                cursor = conn.execute("""
                    INSERT INTO sentences (
                        sentence_text, work_id, author_id, before_text, after_text, source_info
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    sentence['sentence_text'],
                    sentence['work_id'],
                    sentence['author_id'],
                    sentence['before_text'],
                    sentence['after_text'],
                    sentence['source_info']
                ))
                
                sentence_id = cursor.lastrowid
                
                # 3. センテンス-地名関連挿入
                for place_info in sentence['places']:
                    canonical_name = place_info['canonical_name']
                    place_id = place_id_map.get(canonical_name)
                    
                    if place_id:
                        conn.execute("""
                            INSERT INTO sentence_places (
                                sentence_id, place_id, extraction_method, confidence,
                                matched_text, verification_status
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            sentence_id,
                            place_id,
                            place_info['extraction_method'],
                            place_info['confidence'],
                            place_info['matched_text'],
                            'migrated'
                        ))
            
            conn.commit()
    
    def _normalize_sentence(self, sentence: str) -> str:
        """センテンス正規化"""
        if not sentence:
            return ""
        
        # 空白・改行の統一
        normalized = sentence.strip()
        normalized = normalized.replace('\n', ' ').replace('\r', ' ')
        normalized = ' '.join(normalized.split())  # 連続空白を1つに
        
        return normalized
    
    def _normalize_place_name(self, place_name: str) -> str:
        """地名正規化"""
        if not place_name:
            return ""
        
        normalized = place_name.strip()
        
        # よくある表記揺れ統一
        normalized = normalized.replace('ヶ', 'が')
        normalized = normalized.replace('ケ', 'が')
        normalized = normalized.replace('　', ' ')
        
        return normalized
    
    def _determine_place_type(self, extraction_method: str) -> str:
        """抽出手法から地名タイプを決定"""
        if 'regex_都道府県' in extraction_method:
            return '都道府県'
        elif 'regex_市区町村' in extraction_method:
            return '市区町村'
        elif 'regex_郡' in extraction_method:
            return '郡'
        elif 'regex_有名地名' in extraction_method:
            return '有名地名'
        else:
            return '有名地名'  # デフォルト
    
    def get_migration_summary(self) -> Dict[str, Any]:
        """移行結果サマリー"""
        try:
            with sqlite3.connect(self.v4_db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # 統計取得
                cursor = conn.execute("SELECT * FROM statistics_summary")
                stats = dict(cursor.fetchone()) if cursor.fetchone() else {}
                
                # v3.0由来データ
                cursor = conn.execute(
                    "SELECT COUNT(*) as count FROM places_master WHERE source_system = 'v3.0'"
                )
                v3_places = cursor.fetchone()['count']
                
                cursor = conn.execute(
                    "SELECT COUNT(*) as count FROM sentence_places WHERE verification_status = 'migrated'"
                )
                v3_relations = cursor.fetchone()['count']
                
                return {
                    'total_sentences': stats.get('total_sentences', 0),
                    'total_places': stats.get('total_places', 0),
                    'total_relations': stats.get('total_relations', 0),
                    'v3_migrated_places': v3_places,
                    'v3_migrated_relations': v3_relations,
                    'migration_date': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {'error': str(e)} 