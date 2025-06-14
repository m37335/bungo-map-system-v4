#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪ゆかり地図システム v4.0 - メインCLIテスト
"""

import os
import pytest
from click.testing import CliRunner
from bungo_map.cli.main import main

@pytest.fixture
def runner():
    """CLIテストランナー"""
    return CliRunner()

@pytest.fixture
def mock_env(monkeypatch):
    """環境変数のモック"""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_key')
    monkeypatch.setenv('GOOGLE_MAPS_API_KEY', 'test_key')

def test_main_help(runner):
    """ヘルプコマンドのテスト"""
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert '文豪ゆかり地図システム v4.0' in result.output

def test_collect_demo(runner, mock_env):
    """デモデータ収集のテスト"""
    result = runner.invoke(main, ['collect', '--demo'])
    assert result.exit_code == 0
    assert 'デモデータ収集完了' in result.output

def test_pipeline_basic(runner, mock_env):
    """基本パイプラインのテスト"""
    result = runner.invoke(main, ['pipeline', '--test-mode'])
    assert result.exit_code == 0
    assert 'パイプライン完了' in result.output

def test_geocoding_test(runner, mock_env):
    """Geocodingテストのテスト"""
    result = runner.invoke(main, ['test-geocoding', '--place-names', '東京,京都'])
    assert result.exit_code == 0
    assert 'AI文脈判断型Geocodingテスト' in result.output

def test_export_geojson(runner):
    """GeoJSONエクスポートのテスト"""
    result = runner.invoke(main, ['export', '--format', 'geojson', '--preview'])
    assert result.exit_code == 0
    assert 'GeoJSON' in result.output 