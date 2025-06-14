"""
Bungo Map System v4.0 Schema Manager

データベーススキーマの作成・管理・バージョン管理
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional


class SchemaManager:
    """v4.0データベーススキーマ管理"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.schema_path = Path(__file__).parent / "schema.sql"
    
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
    
    def verify_v4_schema(self) -> bool:
        """v4.0スキーマが正常か確認"""
        required_tables = [
            'sentences',
            'places_master', 
            'sentence_places',
            'schema_version'
        ]
        
        required_views = [
            'place_sentences',
            'sentence_places_view',
            'statistics_summary'
        ]
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # テーブル存在確認
                for table in required_tables:
                    cursor = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (table,)
                    )
                    if not cursor.fetchone():
                        print(f"❌ 必要テーブルが見つかりません: {table}")
                        return False
                
                # ビュー存在確認
                for view in required_views:
                    cursor = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='view' AND name=?",
                        (view,)
                    )
                    if not cursor.fetchone():
                        print(f"❌ 必要ビューが見つかりません: {view}")
                        return False
                
                print("✅ v4.0スキーマ確認完了")
                return True
                
        except Exception as e:
            print(f"❌ スキーマ確認エラー: {e}")
            return False
    
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