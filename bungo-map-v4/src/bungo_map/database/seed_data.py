#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テストデータ投入スクリプト
"""

import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from ..core.config import Config

logger = logging.getLogger(__name__)

class TestDataSeeder:
    """テストデータ投入クラス"""
    
    def __init__(self, db_path: str = None):
        self.config = Config()
        self.db_path = db_path or self.config.get_database_path()
    
    def seed_test_data(self) -> bool:
        """テストデータを投入"""
        try:
            logger.info("🌱 テストデータの投入を開始します")
            
            with sqlite3.connect(self.db_path) as conn:
                # 作者データの投入
                self._seed_authors(conn)
                
                # 作品データの投入
                self._seed_works(conn)
                
                # センテンスデータの投入
                self._seed_sentences(conn)
                
                # 地名マスターデータの投入
                self._seed_places_master(conn)
                
                # センテンス-地名関連データの投入
                self._seed_sentence_places(conn)
            
            logger.info("✅ テストデータの投入が完了しました")
            return True
            
        except Exception as e:
            logger.error(f"❌ テストデータ投入エラー: {e}")
            return False
    
    def _seed_authors(self, conn: sqlite3.Connection):
        """作者データの投入"""
        authors = [
            {
                'name': '夏目漱石',
                'wiki_title': '夏目漱石',
                'description': '明治時代の小説家',
                'wikidata_qid': 'Q160566',
                'birth_year': 1867,
                'death_year': 1916,
                'portrait_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Natsume_Soseki.jpg/200px-Natsume_Soseki.jpg',
                'updated_at': datetime.now().isoformat()
            },
            {
                'name': '芥川龍之介',
                'wiki_title': '芥川龍之介',
                'description': '大正時代の小説家',
                'wikidata_qid': 'Q160566',
                'birth_year': 1892,
                'death_year': 1927,
                'portrait_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Ryunosuke_Akutagawa.jpg/200px-Ryunosuke_Akutagawa.jpg',
                'updated_at': datetime.now().isoformat()
            }
        ]
        
        cursor = conn.cursor()
        for author in authors:
            cursor.execute("""
                INSERT INTO authors (
                    name, wiki_title, description, wikidata_qid,
                    birth_year, death_year, portrait_url, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                author['name'], author['wiki_title'], author['description'],
                author['wikidata_qid'], author['birth_year'], author['death_year'],
                author['portrait_url'], author['updated_at']
            ))
        
        conn.commit()
        logger.info(f"✅ {len(authors)}件の作者データを投入しました")
    
    def _seed_works(self, conn: sqlite3.Connection):
        """作品データの投入"""
        works = [
            {
                'author_id': 1,
                'title': '坊っちゃん',
                'aozora_url': 'https://www.aozora.gr.jp/cards/000148/files/752_14964.html',
                'updated_at': datetime.now().isoformat()
            },
            {
                'author_id': 1,
                'title': '吾輩は猫である',
                'aozora_url': 'https://www.aozora.gr.jp/cards/000148/files/789_14547.html',
                'updated_at': datetime.now().isoformat()
            },
            {
                'author_id': 2,
                'title': '羅生門',
                'aozora_url': 'https://www.aozora.gr.jp/cards/000879/files/127_15260.html',
                'updated_at': datetime.now().isoformat()
            }
        ]
        
        cursor = conn.cursor()
        for work in works:
            cursor.execute("""
                INSERT INTO works (
                    author_id, title, aozora_url, updated_at
                ) VALUES (?, ?, ?, ?)
            """, (
                work['author_id'], work['title'],
                work['aozora_url'], work['updated_at']
            ))
        
        conn.commit()
        logger.info(f"✅ {len(works)}件の作品データを投入しました")
    
    def _seed_sentences(self, conn: sqlite3.Connection):
        """センテンスデータの投入"""
        sentences = [
            {
                'work_id': 1,
                'sentence_text': '親譲りの無鉄砲で小供の時から損ばかりしている。',
                'before_text': '',
                'after_text': '小学校に居る時分学校の二階から飛び降りて一週間ほど腰を抜かした事がある。',
                'position_in_work': 1,
                'updated_at': datetime.now().isoformat()
            },
            {
                'work_id': 2,
                'sentence_text': '吾輩は猫である。名前はまだ無い。',
                'before_text': '',
                'after_text': 'どこで生れたかとんと見当がつかぬ。',
                'position_in_work': 1,
                'updated_at': datetime.now().isoformat()
            },
            {
                'work_id': 3,
                'sentence_text': 'ある日の暮方の事である。一人の下人が、羅生門の下で雨やみを待っていた。',
                'before_text': '',
                'after_text': '広い門の下には、この男のほかに誰もいない。',
                'position_in_work': 1,
                'updated_at': datetime.now().isoformat()
            }
        ]
        
        cursor = conn.cursor()
        for sentence in sentences:
            cursor.execute("""
                INSERT INTO sentences (
                    work_id, sentence_text, before_text, after_text,
                    position_in_work, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                sentence['work_id'], sentence['sentence_text'],
                sentence['before_text'], sentence['after_text'],
                sentence['position_in_work'], sentence['updated_at']
            ))
        
        conn.commit()
        logger.info(f"✅ {len(sentences)}件のセンテンスデータを投入しました")
    
    def _seed_places_master(self, conn: sqlite3.Connection):
        """地名マスターデータの投入"""
        places = [
            {
                'place_name': '東京',
                'canonical_name': '東京都',
                'place_type': 'prefecture',
                'prefecture': '東京都',
                'lat': 35.6762,
                'lng': 139.6503,
                'confidence': 1.0,
                'mention_count': 0,
                'updated_at': datetime.now().isoformat()
            },
            {
                'place_name': '京都',
                'canonical_name': '京都市',
                'place_type': 'city',
                'prefecture': '京都府',
                'lat': 35.0116,
                'lng': 135.7681,
                'confidence': 1.0,
                'mention_count': 0,
                'updated_at': datetime.now().isoformat()
            }
        ]
        
        cursor = conn.cursor()
        for place in places:
            cursor.execute("""
                INSERT INTO places_master (
                    place_name, canonical_name, place_type, prefecture,
                    lat, lng, confidence, mention_count, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                place['place_name'], place['canonical_name'],
                place['place_type'], place['prefecture'],
                place['lat'], place['lng'], place['confidence'],
                place['mention_count'], place['updated_at']
            ))
        
        conn.commit()
        logger.info(f"✅ {len(places)}件の地名マスターデータを投入しました")
    
    def _seed_sentence_places(self, conn: sqlite3.Connection):
        """センテンス-地名関連データの投入"""
        sentence_places = [
            {
                'sentence_id': 1,
                'place_id': 1,
                'extraction_method': 'manual',
                'confidence': 1.0,
                'updated_at': datetime.now().isoformat()
            },
            {
                'sentence_id': 2,
                'place_id': 1,
                'extraction_method': 'manual',
                'confidence': 1.0,
                'updated_at': datetime.now().isoformat()
            }
        ]
        
        cursor = conn.cursor()
        for sp in sentence_places:
            cursor.execute("""
                INSERT INTO sentence_places (
                    sentence_id, place_id, extraction_method,
                    confidence, updated_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                sp['sentence_id'], sp['place_id'],
                sp['extraction_method'], sp['confidence'],
                sp['updated_at']
            ))
        
        conn.commit()
        logger.info(f"✅ {len(sentence_places)}件のセンテンス-地名関連データを投入しました")

def main():
    """メイン関数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    seeder = TestDataSeeder()
    
    if seeder.seed_test_data():
        logger.info("🎉 テストデータの投入が成功しました")
    else:
        logger.error("❌ テストデータの投入に失敗しました")

if __name__ == "__main__":
    main() 