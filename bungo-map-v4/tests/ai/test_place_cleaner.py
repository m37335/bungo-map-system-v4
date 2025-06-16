"""
地名クリーナーのテストモジュール
"""

import pytest
from unittest.mock import patch, MagicMock
from bungo_map.ai.cleaners.place_cleaner import PlaceCleaner
from bungo_map.database.models import PlaceMaster

@pytest.fixture
def place_cleaner(db_session):
    """PlaceCleanerのフィクスチャ"""
    return PlaceCleaner(db=db_session)

def test_place_cleaner_initialization(place_cleaner):
    """PlaceCleanerの初期化テスト"""
    assert place_cleaner is not None
    assert place_cleaner.db is not None

def test_place_cleaner_initialization_without_api_key(db_session):
    """APIキーなしでの初期化テスト"""
    cleaner = PlaceCleaner(db=db_session, api_key=None)
    assert cleaner is not None
    assert cleaner.db is not None

def test_analyze_all_places(place_cleaner):
    """地名分析のテスト"""
    # テストデータの準備
    place = PlaceMaster(
        place_name="新宿区",
        canonical_name="東京都新宿区",
        place_type="行政区",
        confidence=0.95
    )
    place_cleaner.db.insert_place_master(place)

    results = place_cleaner.analyze_all_places(limit=1)
    assert len(results) > 0
    assert results[0]["original_name"] == "新宿区"

def test_apply_normalizations(place_cleaner):
    """正規化適用のテスト"""
    # テストデータの準備
    place = PlaceMaster(
        place_name="新宿区",
        canonical_name="東京都新宿区",
        place_type="行政区",
        confidence=0.95
    )
    place_cleaner.db.insert_place_master(place)

    results = place_cleaner.analyze_all_places(limit=1)
    assert len(results) > 0
    assert results[0]["normalized_name"] == "東京都新宿区"

def test_generate_cleaning_report(place_cleaner):
    """クリーニングレポート生成のテスト"""
    report = place_cleaner.generate_cleaning_report()
    assert isinstance(report, dict)
    assert "total_places" in report
    assert "cleaned_places" in report 