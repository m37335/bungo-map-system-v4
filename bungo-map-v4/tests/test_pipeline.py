#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
メインパイプラインのテスト
"""

import pytest
from pathlib import Path
import tempfile
import json
from typing import Dict, List

from bungo_map.core.pipeline import MainPipeline, PipelineResult
from bungo_map.database.manager import DatabaseManager

@pytest.fixture
def temp_db():
    """一時的なデータベースを作成"""
    with tempfile.NamedTemporaryFile(suffix='.db') as f:
        db_path = f.name
        yield db_path

@pytest.fixture
def sample_works():
    """サンプル作品データ"""
    return [
        {
            'author': '夏目漱石',
            'title': 'こころ',
            'content': '私はその人を常に先生と呼んでいた。だからここでもただ先生と書くだけで本名は打ち明けない。'
        },
        {
            'author': '芥川龍之介',
            'title': '羅生門',
            'content': 'ある日の暮方の事である。一人の下人が、羅生門の下で雨やみを待っていた。'
        }
    ]

@pytest.fixture
def pipeline(temp_db):
    """パイプラインインスタンス"""
    return MainPipeline(temp_db)

def test_pipeline_initialization(pipeline):
    """パイプラインの初期化テスト"""
    assert pipeline is not None
    assert isinstance(pipeline.db, DatabaseManager)

def test_process_single_work(pipeline, sample_works):
    """単一作品の処理テスト"""
    work = sample_works[0]
    result = pipeline.process_work(work['author'], work['title'])
    
    assert isinstance(result, PipelineResult)
    assert result.success
    assert result.work_id is not None
    assert result.author_id is not None
    assert isinstance(result.extracted_places, list)
    assert result.processing_time > 0

def test_process_batch(pipeline, sample_works):
    """複数作品の一括処理テスト"""
    results = pipeline.process_batch(sample_works)
    
    assert len(results) == len(sample_works)
    assert all(isinstance(r, PipelineResult) for r in results)
    assert sum(1 for r in results if r.success) > 0

def test_error_handling(pipeline):
    """エラー処理のテスト"""
    # 存在しない作品の処理
    result = pipeline.process_work('存在しない作家', '存在しない作品')
    
    assert not result.success
    assert result.error_message is not None
    assert result.work_id is None
    assert result.author_id is None
    assert result.extracted_places is None

def test_statistics(pipeline, sample_works):
    """統計情報のテスト"""
    # 作品を処理
    pipeline.process_batch(sample_works)
    
    # 統計情報を取得
    stats = pipeline.get_statistics()
    
    assert isinstance(stats, dict)
    assert 'authors' in stats
    assert 'works' in stats
    assert 'places' in stats
    assert 'geocoded_places' in stats
    assert 'processing_time' in stats
    
    assert stats['authors'] >= len(sample_works)
    assert stats['works'] >= len(sample_works)
    assert stats['places'] >= 0
    assert stats['geocoded_places'] >= 0
    assert stats['processing_time'] >= 0

def test_database_integrity(pipeline, sample_works):
    """データベース整合性のテスト"""
    # 作品を処理
    pipeline.process_batch(sample_works)
    
    # データベースの内容を確認
    with pipeline.db.get_connection() as conn:
        # 著者テーブル
        cursor = conn.execute("SELECT COUNT(*) FROM authors")
        author_count = cursor.fetchone()[0]
        assert author_count >= len(sample_works)
        
        # 作品テーブル
        cursor = conn.execute("SELECT COUNT(*) FROM works")
        work_count = cursor.fetchone()[0]
        assert work_count >= len(sample_works)
        
        # 地名テーブル
        cursor = conn.execute("SELECT COUNT(*) FROM places_master")
        place_count = cursor.fetchone()[0]
        assert place_count >= 0
        
        # 文-地名関連テーブル
        cursor = conn.execute("SELECT COUNT(*) FROM sentence_places")
        relation_count = cursor.fetchone()[0]
        assert relation_count >= 0

def test_place_extraction_quality(pipeline, sample_works):
    """地名抽出の品質テスト"""
    work = sample_works[0]
    result = pipeline.process_work(work['author'], work['title'])
    
    assert result.success
    assert len(result.extracted_places) > 0
    
    # 抽出された地名の品質チェック
    for place in result.extracted_places:
        assert 'place_name' in place
        assert 'confidence' in place
        assert 0 <= place['confidence'] <= 1
        assert 'context_before' in place
        assert 'context_after' in place

def test_geocoding_quality(pipeline, sample_works):
    """ジオコーディングの品質テスト"""
    work = sample_works[0]
    result = pipeline.process_work(work['author'], work['title'])
    
    assert result.success
    
    # ジオコーディングされた地名の品質チェック
    geocoded_places = [p for p in result.extracted_places 
                      if 'latitude' in p and 'longitude' in p]
    
    for place in geocoded_places:
        assert -90 <= place['latitude'] <= 90
        assert -180 <= place['longitude'] <= 180
        assert 'confidence' in place
        assert 0 <= place['confidence'] <= 1 