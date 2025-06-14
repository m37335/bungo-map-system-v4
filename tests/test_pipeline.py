#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bungo Map System v4.0 パイプラインテスト
"""

import pytest
from unittest.mock import MagicMock, patch
from bungo_map.cli.full_pipeline import FullPipeline
from bungo_map.database.database import Database
from bungo_map.geocoding.geocoding_service import GeocodingService


@pytest.fixture
def mock_db():
    """モックデータベース"""
    db = MagicMock(spec=Database)
    db.get_work.return_value = {
        'id': 1,
        'title': 'テスト作品',
        'content': '東京と京都に行った。'
    }
    db.get_unprocessed_works.return_value = [
        {'id': 1, 'title': 'テスト作品1'},
        {'id': 2, 'title': 'テスト作品2'}
    ]
    return db


@pytest.fixture
def mock_geocoding():
    """モックジオコーディングサービス"""
    service = MagicMock(spec=GeocodingService)
    service.geocode.return_value = MagicMock(
        success=True,
        location={'lat': 35.6895, 'lng': 139.6917},
        confidence=0.9
    )
    return service


@pytest.fixture
def mock_extractor():
    """モック抽出パイプライン"""
    with patch('bungo_map.extractors.extraction_pipeline.ExtractionPipeline') as mock:
        instance = mock.return_value
        instance.extract_places.return_value = [
            {
                'place_name': '東京',
                'sentence': '東京と京都に行った。',
                'position': {'start': 0, 'end': 2}
            },
            {
                'place_name': '京都',
                'sentence': '東京と京都に行った。',
                'position': {'start': 3, 'end': 5}
            }
        ]
        yield mock


@pytest.fixture
def pipeline(mock_db, mock_geocoding, mock_extractor):
    """パイプラインインスタンス"""
    return FullPipeline(mock_db, mock_geocoding)


def test_pipeline_initialization(pipeline):
    """パイプライン初期化テスト"""
    assert pipeline.db is not None
    assert pipeline.geocoding_service is not None
    assert pipeline.extraction_pipeline is not None


def test_reset_places_data(pipeline):
    """placesテーブルリセットテスト"""
    pipeline.reset_places_data()
    pipeline.db.reset_places_table.assert_called_once()


def test_extract_places_from_work(pipeline, mock_extractor):
    """作品からの地名抽出テスト"""
    places = pipeline.extract_places_from_work(1)
    assert len(places) == 2
    assert places[0]['place_name'] == '東京'
    assert places[1]['place_name'] == '京都'


def test_geocode_places(pipeline, mock_geocoding):
    """地名のジオコーディングテスト"""
    places = [
        {'place_name': '東京'},
        {'place_name': '京都'}
    ]
    result = pipeline.geocode_places(places)
    assert len(result) == 2
    assert all('location' in place for place in result)
    assert all('confidence' in place for place in result)


def test_run_quality_management(pipeline):
    """品質管理テスト"""
    result = pipeline.run_quality_management()
    assert 'stats' in result
    assert 'quality_issues' in result


def test_full_pipeline_execution(pipeline, mock_extractor, mock_geocoding):
    """完全パイプライン実行のテスト"""
    result = pipeline.process_all_works()
    assert 'status' in result
    assert result['status'] == 'success'
    assert result['total_works'] == 2
    assert len(result['results']) == 2 