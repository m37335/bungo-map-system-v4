#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名抽出検証システムのテスト
"""

import unittest
from typing import Dict, List
from ..extraction_validator import ExtractionValidator, ValidatorConfig

class TestExtractionValidator(unittest.TestCase):
    """地名抽出検証システムのテスト"""
    
    def setUp(self):
        """テストの準備"""
        self.config = ValidatorConfig(
            min_confidence=0.7,
            min_accuracy=0.8,
            validate_coordinates=True,
            validate_context=True,
            validate_duplicates=True
        )
        self.validator = ExtractionValidator(self.config)
        
        # テスト用の地名データ
        self.valid_place = {
            'name': '東京',
            'confidence': 0.9,
            'latitude': 35.6895,
            'longitude': 139.6917,
            'context': '東京は日本の首都です。'
        }
        
        self.invalid_place = {
            'name': '無効な地名',
            'confidence': 0.5,
            'latitude': 0.0,
            'longitude': 0.0,
            'context': ''
        }
    
    def test_validate_basic(self):
        """基本的な検証のテスト"""
        # 有効な地名
        self.assertTrue(self.validator._validate_basic(self.valid_place))
        
        # 無効な地名（信頼度が低い）
        self.assertFalse(self.validator._validate_basic(self.invalid_place))
        
        # 必須フィールドが欠けている
        invalid_place = self.valid_place.copy()
        del invalid_place['name']
        self.assertFalse(self.validator._validate_basic(invalid_place))
    
    def test_validate_coordinates(self):
        """座標検証のテスト"""
        # 有効な座標
        self.assertTrue(self.validator._validate_coordinates(self.valid_place))
        
        # 無効な座標（日本国外）
        invalid_coords = self.valid_place.copy()
        invalid_coords.update({
            'latitude': 0.0,
            'longitude': 0.0
        })
        self.assertFalse(self.validator._validate_coordinates(invalid_coords))
        
        # 座標が欠けている
        no_coords = self.valid_place.copy()
        del no_coords['latitude']
        del no_coords['longitude']
        self.assertFalse(self.validator._validate_coordinates(no_coords))
    
    def test_validate_context(self):
        """文脈検証のテスト"""
        # 有効な文脈
        self.assertTrue(self.validator._validate_context(self.valid_place))
        
        # 無効な文脈（空）
        invalid_context = self.valid_place.copy()
        invalid_context['context'] = ''
        self.assertFalse(self.validator._validate_context(invalid_context))
        
        # 無効な文脈（地名が含まれていない）
        invalid_context = self.valid_place.copy()
        invalid_context['context'] = 'これは文脈です。'
        self.assertFalse(self.validator._validate_context(invalid_context))
    
    def test_validate_places(self):
        """一括検証のテスト"""
        places = [self.valid_place, self.invalid_place]
        valid_places, invalid_places = self.validator.validate_places(places)
        
        # 検証結果の確認
        self.assertEqual(len(valid_places), 1)
        self.assertEqual(len(invalid_places), 1)
        self.assertEqual(valid_places[0], self.valid_place)
        self.assertEqual(invalid_places[0], self.invalid_place)
        
        # 統計情報の確認
        stats = self.validator.get_stats()
        self.assertEqual(stats['total_places'], 2)
        self.assertEqual(stats['valid_places'], 1)
        self.assertEqual(stats['invalid_places'], 1)
    
    def test_validation_with_disabled_checks(self):
        """検証無効化のテスト"""
        # 座標検証を無効化
        config = ValidatorConfig(validate_coordinates=False)
        validator = ExtractionValidator(config)
        
        # 座標が無効でも検証が通る
        invalid_coords = self.valid_place.copy()
        invalid_coords.update({
            'latitude': 0.0,
            'longitude': 0.0
        })
        self.assertTrue(validator._validate_place(invalid_coords))
        
        # 文脈検証を無効化
        config = ValidatorConfig(validate_context=False)
        validator = ExtractionValidator(config)
        
        # 文脈が無効でも検証が通る
        invalid_context = self.valid_place.copy()
        invalid_context['context'] = ''
        self.assertTrue(validator._validate_place(invalid_context))

if __name__ == '__main__':
    unittest.main() 