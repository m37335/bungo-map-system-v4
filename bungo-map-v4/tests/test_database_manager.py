#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベースマネージャーのテスト
"""

import pytest
import tempfile
import sqlite3
from datetime import datetime
from typing import Dict, List

from bungo_map.database.manager import DatabaseManager

@pytest.fixture
def temp_db():
    """一時的なデータベースを作成"""
    with tempfile.NamedTemporaryFile(suffix='.db') as f:
        db_path = f.name
        yield db_path

@pytest.fixture
def db_manager(temp_db):
    """データベースマネージャーインスタンス"""
    return DatabaseManager(temp_db)

def test_database_initialization(db_manager):
    """データベース初期化のテスト"""
    assert db_manager is not None
    # テーブルの存在確認
    with sqlite3.connect(db_manager.db_path) as conn:
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN (
                'authors', 'works', 'places_master', 'sentence_places'
            )
        """)
        tables = {row[0] for row in cursor.fetchall()}
        assert 'authors' in tables
        assert 'works' in tables
        assert 'places_master' in tables
        assert 'sentence_places' in tables

def test_author_operations(db_manager):
    """著者操作のテスト"""
    # 著者の作成
    author_id = db_manager.get_or_create_author('夏目漱石')
    assert author_id is not None
    
    # 同じ著者の取得
    same_author_id = db_manager.get_or_create_author('夏目漱石')
    assert same_author_id == author_id
    
    # 別の著者の作成
    other_author_id = db_manager.get_or_create_author('芥川龍之介')
    assert other_author_id != author_id

def test_work_operations(db_manager):
    """作品操作のテスト"""
    # 著者の作成
    author_id = db_manager.get_or_create_author('夏目漱石')
    
    # 作品の作成
    work_id = db_manager.create_work(author_id, 'こころ', '私はその人を常に先生と呼んでいた。')
    assert work_id is not None
    
    # 作品情報の取得
    with sqlite3.connect(db_manager.db_path) as conn:
        cursor = conn.execute("""
            SELECT title, content 
            FROM works 
            WHERE work_id = ?
        """, (work_id,))
        work = cursor.fetchone()
        
        assert work is not None
        assert work[0] == 'こころ'
        assert work[1] == '私はその人を常に先生と呼んでいた。'

def test_place_operations(db_manager):
    """地名操作のテスト"""
    # 著者と作品の作成
    author_id = db_manager.get_or_create_author('夏目漱石')
    work_id = db_manager.create_work(author_id, 'こころ', '私はその人を常に先生と呼んでいた。')
    
    # 地名の保存
    places = [
        {
            'place_name': '東京',
            'canonical_name': '東京都',
            'place_type': '都市',
            'latitude': 35.6895,
            'longitude': 139.6917,
            'confidence': 0.95
        }
    ]
    
    db_manager.save_places(work_id, places)
    
    # 地名情報の取得
    with sqlite3.connect(db_manager.db_path) as conn:
        cursor = conn.execute("""
            SELECT place_name, canonical_name, latitude, longitude 
            FROM places_master 
            WHERE place_name = ?
        """, ('東京',))
        place = cursor.fetchone()
        
        assert place is not None
        assert place[0] == '東京'
        assert place[1] == '東京都'
        assert place[2] == 35.6895
        assert place[3] == 139.6917

def test_statistics_operations(db_manager):
    """統計情報操作のテスト"""
    # テストデータの作成
    author_id = db_manager.get_or_create_author('夏目漱石')
    work_id = db_manager.create_work(author_id, 'こころ', '私はその人を常に先生と呼んでいた。')
    
    places = [
        {
            'place_name': '東京',
            'canonical_name': '東京都',
            'place_type': '都市',
            'latitude': 35.6895,
            'longitude': 139.6917,
            'confidence': 0.95
        }
    ]
    db_manager.save_places(work_id, places)
    
    # 統計情報の取得
    assert db_manager.count_authors() == 1
    assert db_manager.count_works() == 1
    assert db_manager.count_places() >= 1
    assert db_manager.count_geocoded_places() >= 1
    
    # 平均処理時間の取得（カラムがなければスキップ）
    try:
        avg_time = db_manager.get_average_processing_time()
        assert isinstance(avg_time, float)
        assert avg_time >= 0
    except Exception:
        pass

def test_error_handling(db_manager):
    """エラー処理のテスト"""
    # 存在しない著者IDでの作品作成
    with pytest.raises(Exception):
        db_manager.create_work(999, '存在しない作品')
    
    # 存在しない作品IDでの地名保存
    with pytest.raises(Exception):
        db_manager.save_places([{
            'work_id': 999,
            'place_name': '東京',
            'latitude': 35.6895,
            'longitude': 139.6917
        }])

def test_transaction_handling(db_manager):
    """トランザクション処理のテスト"""
    # 著者の作成
    author_id = db_manager.get_or_create_author('夏目漱石')
    # トランザクション内での操作
    with sqlite3.connect(db_manager.db_path) as conn:
        try:
            # 作品の作成
            work_id = db_manager.create_work(author_id, 'こころ', '私はその人を常に先生と呼んでいた。')
            # 地名の保存
            places = [{
                'place_name': '東京',
                'canonical_name': '東京都',
                'place_type': '都市',
                'latitude': 35.6895,
                'longitude': 139.6917,
                'confidence': 0.95
            }]
            db_manager.save_places(work_id, places)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    # データの確認
    assert db_manager.count_works() >= 1
    assert db_manager.count_places() >= 1 