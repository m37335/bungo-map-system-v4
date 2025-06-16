#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bungo Map System v4.0 Schema Manager

データベーススキーマの作成・管理・バージョン管理
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional, Dict, List, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SchemaManager:
    """v4.0データベーススキーマ管理"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        print(f"[DEBUG] SchemaManager.__init__ db_path = {self.db_path}")
        self.schema_path = Path(__file__).parent / "schema.sql"
        logger.info(f"🔧 スキーママネージャー初期化: DBパス = {os.path.abspath(self.db_path)}")
        self._init_schema()
        logger.info("✅ スキーママネージャー初期化完了")
    
    def _init_schema(self):
        """スキーマ初期化"""
        with sqlite3.connect(self.db_path) as conn:
            # 既存のテーブルを削除
            conn.execute("DROP TABLE IF EXISTS sentence_places")
            conn.execute("DROP TABLE IF EXISTS places_master")
            conn.execute("DROP TABLE IF EXISTS sentences")
            conn.execute("DROP TABLE IF EXISTS works")
            conn.execute("DROP TABLE IF EXISTS authors")
            conn.commit()
            
            # 1. 作者テーブル
            conn.execute("""
                CREATE TABLE authors (
                    author_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author_name TEXT UNIQUE NOT NULL,
                    author_name_kana TEXT,
                    birth_year INTEGER,
                    death_year INTEGER,
                    birth_place TEXT,
                    death_place TEXT,
                    period TEXT, -- 明治・大正・昭和・平成
                    major_works TEXT, -- JSON配列形式
                    wikipedia_url TEXT,
                    description TEXT,
                    portrait_url TEXT,
                    
                    -- 統計情報
                    works_count INTEGER DEFAULT 0,
                    total_sentences INTEGER DEFAULT 0,
                    
                    -- メタデータ
                    source_system TEXT DEFAULT 'v4.0',
                    verification_status TEXT DEFAULT 'pending' CHECK(verification_status IN ('pending', 'verified', 'rejected')),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 2. 作品テーブル
            conn.execute("""
                CREATE TABLE works (
                    work_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_title TEXT NOT NULL,
                    author_id INTEGER NOT NULL,
                    publication_year INTEGER,
                    genre TEXT, -- 小説、随筆、詩、戯曲
                    aozora_url TEXT,
                    file_path TEXT,
                    content_length INTEGER DEFAULT 0,
                    sentence_count INTEGER DEFAULT 0,
                    place_count INTEGER DEFAULT 0,
                    
                    -- 青空文庫情報
                    aozora_work_id TEXT,
                    card_id TEXT,
                    copyright_status TEXT,
                    input_person TEXT,
                    proof_person TEXT,
                    
                    -- メタデータ
                    source_system TEXT DEFAULT 'v4.0',
                    processing_status TEXT DEFAULT 'pending' CHECK(processing_status IN ('pending', 'processing', 'completed', 'error')),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE CASCADE
                )
            """)
            
            # 3. センテンステーブル
            conn.execute("""
                CREATE TABLE sentences (
                    sentence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sentence_text TEXT NOT NULL,
                    work_id INTEGER NOT NULL,
                    author_id INTEGER NOT NULL,
                    before_text TEXT,
                    after_text TEXT,
                    source_info TEXT,
                    chapter TEXT,
                    page_number INTEGER,
                    position_in_work INTEGER,
                    sentence_length INTEGER DEFAULT 0,
                    
                    -- 品質情報
                    quality_score REAL DEFAULT 0.0,
                    place_count INTEGER DEFAULT 0,
                    
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE,
                    FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE CASCADE
                )
            """)
            
            # 4. 地名マスターテーブル
            conn.execute("""
                CREATE TABLE places_master (
                    place_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    place_name TEXT UNIQUE NOT NULL,
                    canonical_name TEXT NOT NULL,
                    aliases TEXT, -- JSON配列: ["京都府","京都","みやこ"]
                    latitude REAL,
                    longitude REAL,
                    place_type TEXT CHECK(place_type IN ('都道府県', '市区町村', '有名地名', '郡', '歴史地名', '外国', '架空地名')),
                    confidence REAL DEFAULT 0.0 CHECK(confidence >= 0.0 AND confidence <= 1.0),
                    description TEXT,
                    wikipedia_url TEXT,
                    image_url TEXT,
                    
                    -- 地理情報
                    country TEXT DEFAULT '日本',
                    prefecture TEXT,
                    municipality TEXT,
                    district TEXT,
                    
                    -- 統計情報
                    mention_count INTEGER DEFAULT 0,
                    author_count INTEGER DEFAULT 0,
                    work_count INTEGER DEFAULT 0,
                    
                    -- メタデータ
                    source_system TEXT DEFAULT 'v4.0',
                    verification_status TEXT DEFAULT 'pending' CHECK(verification_status IN ('pending', 'verified', 'rejected')),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 5. センテンス-地名関連テーブル
            conn.execute("""
                CREATE TABLE sentence_places (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sentence_id INTEGER NOT NULL,
                    place_id INTEGER NOT NULL,
                    
                    -- 抽出情報
                    extraction_method TEXT NOT NULL,
                    confidence REAL DEFAULT 0.0 CHECK(confidence >= 0.0 AND confidence <= 1.0),
                    position_in_sentence INTEGER,
                    
                    -- 文脈情報
                    context_before TEXT,
                    context_after TEXT,
                    matched_text TEXT,
                    
                    -- 品質管理
                    verification_status TEXT DEFAULT 'auto' CHECK(verification_status IN ('auto', 'manual_verified', 'manual_rejected')),
                    quality_score REAL DEFAULT 0.0,
                    relevance_score REAL DEFAULT 0.0,
                    
                    -- メタデータ
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (sentence_id) REFERENCES sentences(sentence_id) ON DELETE CASCADE,
                    FOREIGN KEY (place_id) REFERENCES places_master(place_id) ON DELETE CASCADE,
                    UNIQUE(sentence_id, place_id)
                )
            """)
            
            # インデックス作成
            self._create_indexes(conn)
            
            # トリガー作成
            self._create_triggers(conn)
            
            conn.commit()
    
    def _create_indexes(self, conn: sqlite3.Connection):
        """インデックス作成"""
        # 作者テーブル
        conn.execute("CREATE INDEX IF NOT EXISTS idx_authors_name ON authors(author_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_authors_birth_year ON authors(birth_year)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_authors_death_year ON authors(death_year)")
        
        # 作品テーブル
        conn.execute("CREATE INDEX IF NOT EXISTS idx_works_title ON works(work_title)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_works_author ON works(author_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_works_year ON works(publication_year)")
        
        # センテンステーブル
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sentences_work ON sentences(work_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sentences_author ON sentences(author_id)")
        
        # 地名マスターテーブル
        conn.execute("CREATE INDEX IF NOT EXISTS idx_places_name ON places_master(place_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_places_coordinates ON places_master(latitude, longitude)")
        
        # センテンス-地名関連テーブル
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sentence_places_place ON sentence_places(place_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sentence_places_sentence ON sentence_places(sentence_id)")
    
    def create_indexes(self):
        """インデックス作成（外部用）"""
        with sqlite3.connect(self.db_path) as conn:
            self._create_indexes(conn)
            conn.commit()
    
    def create_triggers(self):
        """トリガー作成（外部用）"""
        with sqlite3.connect(self.db_path) as conn:
            self._create_triggers(conn)
            conn.commit()
    
    def _create_triggers(self, conn: sqlite3.Connection):
        """トリガー作成"""
        # updated_at自動更新トリガー
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_authors_timestamp 
            AFTER UPDATE ON authors
            BEGIN
                UPDATE authors SET updated_at = CURRENT_TIMESTAMP WHERE author_id = NEW.author_id;
            END
        """)
        
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_works_timestamp 
            AFTER UPDATE ON works
            BEGIN
                UPDATE works SET updated_at = CURRENT_TIMESTAMP WHERE work_id = NEW.work_id;
            END
        """)
        
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_sentences_timestamp 
            AFTER UPDATE ON sentences
            BEGIN
                UPDATE sentences SET updated_at = CURRENT_TIMESTAMP WHERE sentence_id = NEW.sentence_id;
            END
        """)
        
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_places_master_timestamp 
            AFTER UPDATE ON places_master
            BEGIN
                UPDATE places_master SET updated_at = CURRENT_TIMESTAMP WHERE place_id = NEW.place_id;
            END
        """)
        
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_sentence_places_timestamp 
            AFTER UPDATE ON sentence_places
            BEGIN
                UPDATE sentence_places SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        """)
        
        # 統計カウンタ更新トリガー
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_place_mention_count 
            AFTER INSERT ON sentence_places
            BEGIN
                UPDATE places_master 
                SET mention_count = mention_count + 1 
                WHERE place_id = NEW.place_id;
            END
        """)
        
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_sentence_place_count 
            AFTER INSERT ON sentence_places
            BEGIN
                UPDATE sentences 
                SET place_count = place_count + 1 
                WHERE sentence_id = NEW.sentence_id;
            END
        """)
    
    def initialize_schema(self) -> bool:
        """スキーマの初期化（テスト用）"""
        try:
            # スキーマファイル読み込み
            if not self.schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
            
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # データベース作成・実行
            with sqlite3.connect(self.db_path) as conn:
                # 複数文実行
                conn.executescript(schema_sql)
                conn.commit()
            
            return True
            
        except Exception as e:
            print(f"❌ スキーマ初期化エラー: {e}")
            return False
    
    def create_v4_database(self) -> bool:
        """v4.0データベースを新規作成"""
        try:
            # スキーマファイル読み込み
            if not self.schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
            
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # データベース作成・実行
            with sqlite3.connect(self.db_path) as conn:
                # 複数文実行
                conn.executescript(schema_sql)
                conn.commit()
                
                # バージョン情報テーブル作成・挿入
                self._create_version_table(conn)
                
            print(f"✅ v4.0データベース作成完了: {self.db_path}")
            return True
            
        except Exception as e:
            print(f"❌ データベース作成エラー: {e}")
            return False
    
    def _create_version_table(self, conn: sqlite3.Connection):
        """バージョン管理テーブル作成"""
        version_sql = """
        CREATE TABLE IF NOT EXISTS schema_version (
            version TEXT PRIMARY KEY,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        );
        
        INSERT OR REPLACE INTO schema_version (version, description) 
        VALUES ('4.0.0', 'センテンス中心アーキテクチャ初期版');
        """
        conn.executescript(version_sql)
    
    def check_schema_version(self) -> Optional[str]:
        """現在のスキーマバージョンを確認"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1"
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.OperationalError:
            # テーブルが存在しない = v3.0以前
            return None
    
    def verify_schema(self):
        """スキーマ検証（ダミー: 常に成功）"""
        return True
    
    def get_schema_info(self) -> dict:
        """スキーマ情報を取得"""
        info = {
            'version': self.check_schema_version(),
            'db_path': self.db_path,
            'db_exists': os.path.exists(self.db_path),
            'tables': [],
            'views': [],
            'indexes': []
        }
        
        if not info['db_exists']:
            return info
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # テーブル一覧
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                info['tables'] = [row[0] for row in cursor.fetchall()]
                
                # ビュー一覧
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
                )
                info['views'] = [row[0] for row in cursor.fetchall()]
                
                # インデックス一覧
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
                info['indexes'] = [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def backup_database(self, backup_path: str) -> bool:
        """データベースバックアップ"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            print(f"✅ データベースバックアップ完了: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ バックアップエラー: {e}")
            return False
    
    def drop_v4_schema(self) -> bool:
        """v4.0スキーマを削除（開発用）"""
        v4_tables = ['sentences', 'places_master', 'sentence_places', 'schema_version']
        v4_views = ['place_sentences', 'sentence_places_view', 'statistics_summary']
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # ビュー削除
                for view in v4_views:
                    conn.execute(f"DROP VIEW IF EXISTS {view}")
                
                # テーブル削除
                for table in v4_tables:
                    conn.execute(f"DROP TABLE IF EXISTS {table}")
                
                conn.commit()
            
            print("✅ v4.0スキーマ削除完了")
            return True
            
        except Exception as e:
            print(f"❌ スキーマ削除エラー: {e}")
            return False
    
    def get_schema_version(self) -> str:
        """スキーマバージョン取得"""
        return "v4.0"
    
    def get_table_info(self) -> Dict[str, List[str]]:
        """テーブル情報取得"""
        with sqlite3.connect(self.db_path) as conn:
            tables = {}
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            for (table_name,) in cursor.fetchall():
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]
                tables[table_name] = columns
            return tables
    
    def get_index_info(self) -> Dict[str, List[str]]:
        """インデックス情報取得"""
        with sqlite3.connect(self.db_path) as conn:
            indexes = {}
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
            for (index_name,) in cursor.fetchall():
                cursor = conn.execute(f"PRAGMA index_info({index_name})")
                columns = [row[1] for row in cursor.fetchall()]
                indexes[index_name] = columns
            return indexes
    
    def get_trigger_info(self) -> List[str]:
        """トリガー情報取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
            return [row[0] for row in cursor.fetchall()] 