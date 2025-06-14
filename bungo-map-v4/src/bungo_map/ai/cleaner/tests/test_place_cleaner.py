"""地名クリーニングシステムのテスト"""

import unittest
from typing import Dict, List

from bungo_map.ai.cleaner.place_cleaner import PlaceCleaner, CleanerConfig

class TestPlaceCleaner(unittest.TestCase):
    """地名クリーニングのテスト"""
    
    def setUp(self):
        """テストの準備"""
        self.config = CleanerConfig(
            min_confidence=0.7,
            min_accuracy=0.8,
            remove_duplicates=True,
            validate_coordinates=True,
            validate_context=True
        )
        self.cleaner = PlaceCleaner(self.config)
        
        # テスト用の地名データ
        self.test_places: List[Dict] = [
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
            },
            {
                'name': '無効座標',
                'confidence': 0.9,
                'accuracy': 0.9,
                'latitude': 0.0,
                'longitude': 0.0,
                'context': '無効な座標の地名です。'
            },
            {
                'name': '東京',  # 重複
                'confidence': 0.9,
                'accuracy': 0.9,
                'latitude': 35.6895,
                'longitude': 139.6917,
                'context': '重複する地名です。'
            },
            {
                'name': '無文脈',
                'confidence': 0.9,
                'accuracy': 0.9,
                'latitude': 35.6895,
                'longitude': 139.6917,
                'context': ''
            }
        ]
    
    def test_basic_cleaning(self):
        """基本的なクリーニングのテスト"""
        cleaned = self.cleaner.clean_places(self.test_places)
        
        # 低信頼度データが除去されていることを確認
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned[0]['name'], '東京')
        
        # 統計情報の確認
        self.assertEqual(self.cleaner.stats['total_places'], 5)
        self.assertEqual(self.cleaner.stats['removed_low_confidence'], 1)
        self.assertEqual(self.cleaner.stats['removed_invalid_coords'], 1)
        self.assertEqual(self.cleaner.stats['removed_duplicates'], 1)
        self.assertEqual(self.cleaner.stats['removed_invalid_context'], 1)
        self.assertEqual(self.cleaner.stats['cleaned_places'], 1)
    
    def test_coordinate_validation(self):
        """座標検証のテスト"""
        # 座標検証を無効化
        self.config.validate_coordinates = False
        cleaner = PlaceCleaner(self.config)
        
        cleaned = cleaner.clean_places(self.test_places)
        
        # 無効な座標のデータも残っていることを確認
        self.assertGreater(len(cleaned), 1)
        self.assertTrue(any(p['name'] == '無効座標' for p in cleaned))
    
    def test_duplicate_removal(self):
        """重複除去のテスト"""
        # 重複除去を無効化
        self.config.remove_duplicates = False
        cleaner = PlaceCleaner(self.config)
        
        cleaned = cleaner.clean_places(self.test_places)
        
        # 重複が残っていることを確認
        self.assertGreater(len(cleaned), 1)
        self.assertEqual(len([p for p in cleaned if p['name'] == '東京']), 2)
    
    def test_context_validation(self):
        """文脈検証のテスト"""
        # 文脈検証を無効化
        self.config.validate_context = False
        cleaner = PlaceCleaner(self.config)
        
        cleaned = cleaner.clean_places(self.test_places)
        
        # 無文脈のデータも残っていることを確認
        self.assertGreater(len(cleaned), 1)
        self.assertTrue(any(p['name'] == '無文脈' for p in cleaned))

if __name__ == '__main__':
    unittest.main() 