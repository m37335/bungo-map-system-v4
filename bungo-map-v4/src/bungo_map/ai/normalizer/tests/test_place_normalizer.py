#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名正規化システムのテスト
"""

import unittest
from unittest.mock import patch, MagicMock
from typing import Dict, List
from ..place_normalizer import PlaceNormalizer, NormalizerConfig

class TestPlaceNormalizer(unittest.TestCase):
    """地名正規化システムのテスト"""
    
    def setUp(self):
        """テストの準備"""
        self.config = NormalizerConfig(
            api_key='test_key',
            model='gpt-4',
            temperature=0.0,
            max_tokens=100,
            retry_count=3,
            retry_delay=0.1,
            batch_size=10
        )
        self.normalizer = PlaceNormalizer(self.config)
        
        # テスト用の地名データ
        self.test_place = {
            'name': '東京都',
            'confidence': 0.9,
            'latitude': 35.6895,
            'longitude': 139.6917,
            'context': '東京は日本の首都です。'
        }
    
    @patch('openai.ChatCompletion.create')
    def test_normalize_place(self, mock_create):
        """地名正規化のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='東京'))
        ]
        mock_create.return_value = mock_response
        
        # 正規化実行
        normalized = self.normalizer._normalize_place(self.test_place)
        
        # 結果の検証
        self.assertIsNotNone(normalized)
        self.assertEqual(normalized['name'], '東京')
        self.assertEqual(normalized['original_name'], '東京都')
        self.assertEqual(normalized['normalization_confidence'], 0.9)
        
        # API呼び出しの検証
        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args['model'], 'gpt-4')
        self.assertEqual(call_args['temperature'], 0.0)
        self.assertEqual(call_args['max_tokens'], 100)
    
    @patch('openai.ChatCompletion.create')
    def test_normalize_places(self, mock_create):
        """一括正規化のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='東京'))
        ]
        mock_create.return_value = mock_response
        
        # テストデータ
        places = [
            self.test_place,
            {'name': '大阪府', 'confidence': 0.9},
            {'name': '福岡県', 'confidence': 0.9}
        ]
        
        # 正規化実行
        normalized_places = self.normalizer.normalize_places(places)
        
        # 結果の検証
        self.assertEqual(len(normalized_places), 3)
        self.assertEqual(normalized_places[0]['name'], '東京')
        self.assertEqual(normalized_places[1]['name'], '東京')
        self.assertEqual(normalized_places[2]['name'], '東京')
        
        # 統計情報の検証
        stats = self.normalizer.get_stats()
        self.assertEqual(stats['total_places'], 3)
        self.assertEqual(stats['normalized'], 3)
        self.assertEqual(stats['failed'], 0)
        self.assertEqual(stats['skipped'], 0)
        self.assertEqual(stats['api_calls'], 3)
    
    @patch('openai.ChatCompletion.create')
    def test_normalize_place_with_error(self, mock_create):
        """エラー処理のテスト"""
        # モックの設定（エラーを発生させる）
        mock_create.side_effect = Exception('API Error')
        
        # 正規化実行
        normalized = self.normalizer._normalize_place(self.test_place)
        
        # 結果の検証（エラー時は元のデータを返す）
        self.assertIsNotNone(normalized)
        self.assertEqual(normalized, self.test_place)
        
        # API呼び出しの検証
        self.assertEqual(mock_create.call_count, 3)  # リトライ回数分呼び出される

if __name__ == '__main__':
    unittest.main() 