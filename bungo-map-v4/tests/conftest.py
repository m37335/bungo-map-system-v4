import os
import pytest
from bungo_map.database.manager import DatabaseManager
from bungo_map.database.schema_manager import SchemaManager
from dotenv import load_dotenv

# .envファイルを自動読み込み
load_dotenv(dotenv_path='/app/bungo-map-v4/.env')

@pytest.fixture(scope="session")
def test_db():
    """テスト用データベースのセッションスコープフィクスチャ"""
    # テスト用DBファイルのパス
    db_path = os.path.join(os.path.dirname(__file__), "test.db")
    
    # 既存のDBファイルがあれば削除
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # DBマネージャーの初期化
    db_manager = DatabaseManager(db_path)
    
    # スキーマの初期化
    schema_manager = SchemaManager(db_path)
    schema_manager.initialize_schema()
    
    return db_manager

@pytest.fixture(scope="function")
def db_session(test_db):
    """テストセッション用のデータベースフィクスチャ"""
    yield test_db
    # テスト後にデータベースをクリーンアップ
    with test_db.get_connection() as conn:
        conn.execute("DELETE FROM sentence_places")
        conn.execute("DELETE FROM sentences")
        conn.execute("DELETE FROM places_master")
        conn.execute("DELETE FROM normalizations")
        conn.execute("DELETE FROM users")
        conn.commit()

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """テスト環境のセットアップ"""
    # テスト用の環境変数を設定
    os.environ["OPENAI_API_KEY"] = "test-api-key"
    
    yield
    
    # テスト終了後のクリーンアップ
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"] 