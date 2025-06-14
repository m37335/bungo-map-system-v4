"""
地名クリーナーのテストモジュール
"""

import pytest
from unittest.mock import patch, MagicMock
from bungo_map.ai.cleaners.place_cleaner import PlaceCleaner, PlaceCleaningResult

@pytest.fixture
def mock_openai_response():
    """OpenAI APIのモックレスポンス"""
    return MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content="東京都新宿区"
                )
            )
        ]
    )

@pytest.fixture
def place_cleaner():
    """PlaceCleanerのインスタンス"""
    return PlaceCleaner(api_key="test_key")

def test_place_cleaner_initialization():
    """PlaceCleanerの初期化テスト"""
    cleaner = PlaceCleaner(api_key="test_key")
    assert cleaner is not None
    assert cleaner.logger is not None
    assert cleaner.console is not None

def test_place_cleaner_initialization_without_api_key():
    """APIキーなしでの初期化テスト"""
    with pytest.raises(ValueError):
        PlaceCleaner()

@patch('openai.ChatCompletion.create')
def test_clean_place_name(mock_create, place_cleaner, mock_openai_response):
    """地名クリーニングのテスト"""
    mock_create.return_value = mock_openai_response
    
    result = place_cleaner.clean_place_name("新宿区")
    
    assert isinstance(result, PlaceCleaningResult)
    assert result.original_name == "新宿区"
    assert result.cleaned_name == "東京都新宿区"
    assert result.confidence == 0.95
    assert result.cleaning_type == "normalization"
    assert "model" in result.metadata

@patch('openai.ChatCompletion.create')
def test_batch_clean_places(mock_create, place_cleaner, mock_openai_response):
    """一括地名クリーニングのテスト"""
    mock_create.return_value = mock_openai_response
    
    place_names = ["新宿区", "渋谷区", "千代田区"]
    results = place_cleaner.batch_clean_places(place_names)
    
    assert len(results) == 3
    for result in results:
        assert isinstance(result, PlaceCleaningResult)
        assert result.cleaned_name == "東京都新宿区"
        assert result.confidence == 0.95

@patch('openai.ChatCompletion.create')
def test_clean_place_name_error_handling(mock_create, place_cleaner):
    """エラーハンドリングのテスト"""
    mock_create.side_effect = Exception("API Error")
    
    with pytest.raises(Exception) as exc_info:
        place_cleaner.clean_place_name("新宿区")
    
    assert "API Error" in str(exc_info.value)

@patch('openai.ChatCompletion.create')
def test_batch_clean_places_error_handling(mock_create, place_cleaner):
    """一括処理でのエラーハンドリングのテスト"""
    mock_create.side_effect = Exception("API Error")
    
    place_names = ["新宿区", "渋谷区"]
    results = place_cleaner.batch_clean_places(place_names)
    
    assert len(results) == 2
    for result in results:
        assert result.confidence == 0.0
        assert result.cleaning_type == "error"
        assert "error" in result.metadata 