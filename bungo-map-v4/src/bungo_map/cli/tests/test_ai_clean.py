"""ai cleanコマンドのテスト"""

import json
import os
import tempfile
import unittest
from pathlib import Path

import click
from click.testing import CliRunner

from ..ai_clean import clean

class TestAiClean(unittest.TestCase):
    """ai cleanコマンドのテスト"""
    
    def setUp(self):
        """テストの準備"""
        self.runner = CliRunner()
        
        # テスト用の地名データ
        self.test_places = [
            {
                'name': '東京',
                'confidence': 0.9,
                'accuracy': 0.95,
                'latitude': 35.6895,
                'longitude': 139.6917,
                'context': '東京は日本の首都です。'
            },
            {
                'name': '低信頼度',
                'confidence': 0.5,
                'accuracy': 0.6,
                'latitude': 35.6895,
                'longitude': 139.6917,
                'context': '低信頼度の地名です。'
            }
        ]
    
    def test_basic_cleaning(self):
        """基本的なクリーニングのテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 入力ファイルの作成
            input_file = Path(tmpdir) / 'input.json'
            with open(input_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_places, f, ensure_ascii=False)
            
            # 出力ファイルのパス
            output_file = Path(tmpdir) / 'output.json'
            
            # コマンドの実行
            result = self.runner.invoke(clean, [
                str(input_file),
                '--output', str(output_file)
            ])
            
            # 結果の確認
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(output_file.exists())
            
            # 出力ファイルの内容確認
            with open(output_file, 'r', encoding='utf-8') as f:
                cleaned = json.load(f)
            
            self.assertEqual(len(cleaned), 1)
            self.assertEqual(cleaned[0]['name'], '東京')
    
    def test_custom_thresholds(self):
        """カスタム閾値のテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 入力ファイルの作成
            input_file = Path(tmpdir) / 'input.json'
            with open(input_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_places, f, ensure_ascii=False)
            
            # 出力ファイルのパス
            output_file = Path(tmpdir) / 'output.json'
            
            # コマンドの実行（閾値を下げる）
            result = self.runner.invoke(clean, [
                str(input_file),
                '--output', str(output_file),
                '--min-confidence', '0.4',
                '--min-accuracy', '0.5'
            ])
            
            # 結果の確認
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(output_file.exists())
            
            # 出力ファイルの内容確認
            with open(output_file, 'r', encoding='utf-8') as f:
                cleaned = json.load(f)
            
            self.assertEqual(len(cleaned), 2)  # 両方の地名が残っている
    
    def test_validation_options(self):
        """検証オプションのテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 入力ファイルの作成
            input_file = Path(tmpdir) / 'input.json'
            with open(input_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_places, f, ensure_ascii=False)
            
            # 出力ファイルのパス
            output_file = Path(tmpdir) / 'output.json'
            
            # コマンドの実行（検証を無効化）
            result = self.runner.invoke(clean, [
                str(input_file),
                '--output', str(output_file),
                '--no-coordinates',
                '--no-context'
            ])
            
            # 結果の確認
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(output_file.exists())
            
            # 出力ファイルの内容確認
            with open(output_file, 'r', encoding='utf-8') as f:
                cleaned = json.load(f)
            
            self.assertEqual(len(cleaned), 1)  # 信頼度による除去のみ

if __name__ == '__main__':
    unittest.main() 