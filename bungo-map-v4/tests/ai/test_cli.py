"""
AI機能CLIコマンドのテストモジュール
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from bungo_map.ai.cli import ai
from bungo_map.database.models import PlaceMaster

@pytest.fixture
def runner():
    """CLIランナーのフィクスチャ"""
    return CliRunner()

@pytest.fixture
def mock_place_cleaner(db_session):
    """モックPlaceCleanerのフィクスチャ"""
    with patch('bungo_map.ai.cli.PlaceCleaner') as mock:
        cleaner = MagicMock()
        cleaner.db = db_session
        mock.return_value = cleaner
        yield cleaner

def test_analyze_command(runner, mock_place_cleaner):
    """analyzeコマンドのテスト"""
    # テストデータの準備
    place = PlaceMaster(
        place_name="新宿区",
        canonical_name="東京都新宿区",
        place_type="市区町村",
        confidence=0.95
    )
    mock_place_cleaner.db.insert_place_master(place)

    result = runner.invoke(ai, ['analyze', '--data', '新宿区'])
    assert result.exit_code == 0
    assert "分析結果" in result.output

def test_normalize_command(runner, mock_place_cleaner):
    """normalizeコマンドのテスト"""
    # テストデータの準備
    place = PlaceMaster(
        place_name="新宿区",
        canonical_name="東京都新宿区",
        place_type="市区町村",
        confidence=0.95
    )
    mock_place_cleaner.db.insert_place_master(place)

    result = runner.invoke(ai, ['normalize', '--data', '新宿区'])
    assert result.exit_code == 0
    assert "正規化結果" in result.output

def test_batch_clean_command(runner, mock_place_cleaner, tmp_path):
    """batch-cleanコマンドのテスト"""
    # テストデータの準備
    place = PlaceMaster(
        place_name="新宿区",
        canonical_name="東京都新宿区",
        place_type="市区町村",
        confidence=0.95
    )
    mock_place_cleaner.db.insert_place_master(place)

    # テスト用の入力ファイルを作成
    input_file = tmp_path / "input.txt"
    input_file.write_text("新宿区\n渋谷区\n千代田区")

    # 出力ファイルのパス
    output_file = tmp_path / "output.txt"

    result = runner.invoke(ai, ['batch-clean', '--input', str(input_file), '--output', str(output_file)])
    assert result.exit_code == 0
    assert "バッチ処理完了" in result.output

def test_test_connection_command(runner):
    """test-connectionコマンドのテスト"""
    with patch('bungo_map.ai.cli.AIManager') as mock:
        manager = MagicMock()
        mock.return_value = manager
        result = runner.invoke(ai, ['test-connection'])
        assert result.exit_code == 0
        assert "接続テスト" in result.output

def test_analyze_command_error(runner):
    """analyzeコマンドのエラーテスト"""
    result = runner.invoke(ai, ['analyze'])
    assert result.exit_code != 0
    assert "Missing option '--data'" in result.output

def test_batch_clean_command_invalid_input(runner, tmp_path):
    """batch-cleanコマンドの無効な入力テスト"""
    # 存在しない入力ファイル
    result = runner.invoke(ai, ['batch-clean', '--input', 'nonexistent.txt', '--output', 'output.txt'])
    assert result.exit_code != 0
    assert "ファイルが見つかりません" in result.output 