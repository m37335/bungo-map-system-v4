"""
バリデーションCLIコマンドのテストモジュール
"""

import pytest
from click.testing import CliRunner
from bungo_map.cli.validate_cli import cli
from bungo_map.database.models import PlaceMaster

@pytest.fixture
def runner():
    """CLIランナーのフィクスチャ"""
    return CliRunner()

def test_validate_data_basic(runner, db_session):
    """基本的なデータ検証コマンドのテスト"""
    # テストデータの準備
    place = PlaceMaster(
        place_name="新宿区",
        canonical_name="東京都新宿区",
        place_type="市区町村",
        confidence=0.95
    )
    db_session.insert_place_master(place)

    result = runner.invoke(cli, ['validate-data', '--db-path', ':memory:'])
    assert result.exit_code == 0
    assert "データ検証を開始" in result.output

def test_validate_data_with_options(runner, db_session):
    """オプション付きのデータ検証コマンドのテスト"""
    # テストデータの準備
    place = PlaceMaster(
        place_name="新宿区",
        canonical_name="東京都新宿区",
        place_type="市区町村",
        confidence=0.95
    )
    db_session.insert_place_master(place)

    result = runner.invoke(cli, [
        'validate-data',
        '--db-path', ':memory:',
        '--strict',
        '--output', 'validation_report.json'
    ])
    assert result.exit_code == 0
    assert "データ検証を開始" in result.output

def test_validate_schema(runner):
    """スキーマ検証コマンドのテスト"""
    result = runner.invoke(cli, ['validate-schema', '--db-path', ':memory:'])
    assert result.exit_code == 0
    assert "スキーマは有効です" in result.output

def test_validate_consistency(runner, db_session):
    """データ一貫性検証コマンドのテスト"""
    # テストデータの準備
    place = PlaceMaster(
        place_name="新宿区",
        canonical_name="東京都新宿区",
        place_type="市区町村",
        confidence=0.95
    )
    db_session.insert_place_master(place)

    result = runner.invoke(cli, ['validate-consistency', '--db-path', ':memory:'])
    assert result.exit_code == 0
    assert "一貫性チェック完了" in result.output

def test_validate_data_with_invalid_input(runner):
    """無効な入力でのデータ検証コマンドのテスト"""
    result = runner.invoke(cli, ['validate-data', '--db-path', 'nonexistent.db'])
    assert result.exit_code != 0
    assert "データベースに接続できません" in result.output

@pytest.mark.skip(reason="カスタムルールファイルが必要")
def test_validate_data_with_custom_rules(runner):
    """カスタムルール付きのデータ検証コマンドのテスト"""
    result = runner.invoke(cli, [
        'validate-data',
        '--db-path', ':memory:',
        '--rules', 'custom_rules.json'
    ])
    assert result.exit_code == 0
    assert "カスタムルールで検証" in result.output 