#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名クリーニングシステムのテスト
"""

import unittest
from typing import Dict, List
from bungo_map.ai.cleaners.place_cleaner import PlaceCleaner, CleanerConfig

class TestPlaceCleaner(unittest.TestCase):
    """地名クリーニングテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.cleaner = PlaceCleaner()
        self.test_places = [
            {
                'name': '東京都新宿区',
                'confidence': 0.9,
                'latitude': 35.6938,
                'longitude': 139.7034
            },
            {
                'name': '臺北市',
                'confidence': 0.8,
                'latitude': 35.6895,
                'longitude': 139.6917
            },
            {
                'name': '廣島市',
                'confidence': 0.7,
                'latitude': 34.3853,
                'longitude': 132.4553
            },
            {
                'name': '無効地名',
                'confidence': 0.3,
                'latitude': 0,
                'longitude': 0
            }
        ]
    
    def test_basic_cleaning(self):
        """基本的なクリーニングテスト"""
        cleaned = self.cleaner.clean_places(self.test_places)
        
        # 低信頼度の地名が除去されていることを確認
        self.assertEqual(len(cleaned), 3)
        
        # 漢字正規化が行われていることを確認
        self.assertEqual(cleaned[1]['name'], '台北市')
        self.assertEqual(cleaned[2]['name'], '広島市')
    
    def test_coordinate_validation(self):
        """座標検証テスト"""
        invalid_places = [
            {
                'name': '無効座標1',
                'confidence': 0.9,
                'latitude': 200,  # 無効な緯度
                'longitude': 139.7034
            },
            {
                'name': '無効座標2',
                'confidence': 0.9,
                'latitude': 35.6938,
                'longitude': 200  # 無効な経度
            }
        ]
        
        cleaned = self.cleaner.clean_places(invalid_places)
        self.assertEqual(len(cleaned), 0)
    
    def test_duplicate_removal(self):
        """重複除去テスト"""
        duplicate_places = [
            {
                'name': '東京',
                'confidence': 0.9,
                'latitude': 35.6938,
                'longitude': 139.7034
            },
            {
                'name': '東京',
                'confidence': 0.9,
                'latitude': 35.6938,
                'longitude': 139.7034
            }
        ]
        
        cleaned = self.cleaner.clean_places(duplicate_places)
        self.assertEqual(len(cleaned), 1)
    
    def test_stats_tracking(self):
        """統計情報の追跡テスト"""
        self.cleaner.clean_places(self.test_places)
        stats = self.cleaner.get_stats()
        
        self.assertEqual(stats['total_processed'], 4)
        self.assertEqual(stats['cleaned'], 3)
        self.assertEqual(stats['removed'], 1)
        self.assertEqual(stats['normalized'], 3)  # 漢字正規化された地名の数

if __name__ == '__main__':
    unittest.main()
