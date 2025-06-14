"""
AI機能CLIコマンドのテストモジュール
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from bungo_map.ai.cli import ai
from src.ai.cleaners.place_cleaner import PlaceCleaningResult

@pytest.fixture
def runner():
    """CLIテストランナー"""
    return CliRunner()

@pytest.fixture
def mock_place_cleaner():
    """PlaceCleanerのモック"""
    with patch('bungo_map.ai.cli.PlaceCleaner') as mock:
        instance = mock.return_value
        instance.clean_place_name.return_value = PlaceCleaningResult(
            original_name="新宿区",
            cleaned_name="東京都新宿区",
            confidence=0.95,
            cleaning_type="normalization",
            metadata={"model": "gpt-4"}
        )
        yield instance

def test_analyze_command(runner, mock_place_cleaner):
    """analyzeコマンドのテスト"""
    result = runner.invoke(ai, ['analyze', '新宿区'])
    
    assert result.exit_code == 0
    assert "元の地名" in result.output
    assert "正規化地名" in result.output
    assert "信頼度" in result.output
    assert "処理タイプ" in result.output

def test_normalize_command(runner, mock_place_cleaner):
    """normalizeコマンドのテスト"""
    result = runner.invoke(ai, ['normalize', '新宿区'])
    
    assert result.exit_code == 0
    assert "元の地名: 新宿区" in result.output
    assert "正規化後: 東京都新宿区" in result.output

def test_batch_clean_command(runner, mock_place_cleaner, tmp_path):
    """batch-cleanコマンドのテスト"""
    # テスト用の入力ファイルを作成
    input_file = tmp_path / "input.txt"
    input_file.write_text("新宿区\n渋谷区\n千代田区")
    
    # 出力ファイルのパス
    output_file = tmp_path / "output.txt"
    
    # モックの設定
    mock_place_cleaner.batch_clean_places.return_value = [
        PlaceCleaningResult(
            original_name="新宿区",
            cleaned_name="東京都新宿区",
            confidence=0.95,
            cleaning_type="normalization",
            metadata={"model": "gpt-4"}
        ),
        PlaceCleaningResult(
            original_name="渋谷区",
            cleaned_name="東京都渋谷区",
            confidence=0.95,
            cleaning_type="normalization",
            metadata={"model": "gpt-4"}
        ),
        PlaceCleaningResult(
            original_name="千代田区",
            cleaned_name="東京都千代田区",
            confidence=0.95,
            cleaning_type="normalization",
            metadata={"model": "gpt-4"}
        )
    ]
    
    result = runner.invoke(ai, ['batch-clean', str(input_file), str(output_file)])
    
    assert result.exit_code == 0
    assert "クリーニング完了" in result.output
    
    # 出力ファイルの内容を確認
    assert output_file.exists()
    content = output_file.read_text()
    assert "新宿区" in content
    assert "東京都新宿区" in content

def test_test_connection_command(runner, mock_place_cleaner):
    """test-connectionコマンドのテスト"""
    result = runner.invoke(ai, ['test-connection'])
    
    assert result.exit_code == 0
    assert "API接続テスト成功" in result.output

def test_analyze_command_error(runner, mock_place_cleaner):
    """analyzeコマンドのエラーハンドリングテスト"""
    mock_place_cleaner.clean_place_name.side_effect = Exception("API Error")
    
    result = runner.invoke(ai, ['analyze', '新宿区'])
    
    assert result.exit_code != 0
    assert "エラーが発生しました" in result.output

def test_batch_clean_command_invalid_input(runner, mock_place_cleaner, tmp_path):
    """batch-cleanコマンドの無効な入力テスト"""
    # 存在しない入力ファイル
    input_file = tmp_path / "nonexistent.txt"
    output_file = tmp_path / "output.txt"
    
    result = runner.invoke(ai, ['batch-clean', str(input_file), str(output_file)])
    
    assert result.exit_code != 0
    assert "Error" in result.output 