#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文脈を考慮したジオコーディングのテスト
"""

import unittest
from bungo_map.ai.geocoder.context_aware_geocoder import ContextAwareGeocoder, ContextAnalysisResult, EnhancedGeocodingResult

class TestContextAwareGeocoder(unittest.TestCase):
    """文脈を考慮したジオコーディングのテスト"""
    
    def setUp(self):
        """テストの準備"""
        self.geocoder = ContextAwareGeocoder()
    
    def test_place_name_detection(self):
        """地名判定のテスト"""
        # 地名として使われている場合
        result = self.geocoder._analyze_context_rule_based(
            "東京",
            "東京に行った",
            "昨日",
            "とても楽しかった"
        )
        self.assertTrue(result.is_place_name)
        self.assertGreater(result.confidence, 0.7)
        
        # 人名として使われている場合
        result = self.geocoder._analyze_context_rule_based(
            "柏",
            "柏さんは言った",
            "昨日",
            "とても楽しかった"
        )
        self.assertFalse(result.is_place_name)
        self.assertGreater(result.confidence, 0.7)
    
    def test_historical_context(self):
        """歴史的文脈のテスト"""
        # 古国名の判定
        result = self.geocoder._analyze_context_rule_based(
            "伊勢",
            "伊勢国を訪れた",
            "昔",
            "とても楽しかった"
        )
        self.assertTrue(result.is_place_name)
        self.assertEqual(result.place_type, "古国名")
        self.assertEqual(result.historical_context, "伊勢国、伊勢神宮")
    
    def test_detail_places(self):
        """詳細地名データベースのテスト"""
        # 東京の詳細地名
        result = self.geocoder._search_detail_places("本郷")
        self.assertIsNotNone(result)
        self.assertEqual(result.prefecture, "東京都文京区")
        self.assertAlmostEqual(result.latitude, 35.7081, places=4)
        self.assertAlmostEqual(result.longitude, 139.7619, places=4)
        
        # 京都の詳細地名
        result = self.geocoder._search_detail_places("伏見")
        self.assertIsNotNone(result)
        self.assertEqual(result.prefecture, "京都府京都市伏見区")
        self.assertAlmostEqual(result.latitude, 34.9393, places=4)
        self.assertAlmostEqual(result.longitude, 135.7578, places=4)
        
        # 海外地名
        result = self.geocoder._search_detail_places("パリ")
        self.assertIsNotNone(result)
        self.assertEqual(result.prefecture, "フランス")
        self.assertAlmostEqual(result.latitude, 48.8566, places=4)
        self.assertAlmostEqual(result.longitude, 2.3522, places=4)
    
    def test_geocode_place(self):
        """ジオコーディングのテスト"""
        # 通常の地名
        result = self.geocoder.geocode_place(
            "東京",
            "東京に行った",
            "昨日",
            "とても楽しかった"
        )
        self.assertIsNotNone(result)
        self.assertTrue(result.context_analysis.is_place_name)
        
        # 曖昧地名
        result = self.geocoder.geocode_place(
            "柏",
            "柏さんは言った",
            "昨日",
            "とても楽しかった"
        )
        self.assertIsNone(result)  # 人名と判定されるため
        
        # 古典地名
        result = self.geocoder.geocode_place(
            "伊勢",
            "伊勢国を訪れた",
            "昔",
            "とても楽しかった"
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.context_analysis.place_type, "古国名")

if __name__ == "__main__":
    unittest.main() 