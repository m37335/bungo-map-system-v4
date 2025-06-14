import unittest
from unittest.mock import patch, MagicMock
from bungo_map.ai.analyzer.place_analyzer import PlaceAnalyzer, AnalysisConfig

class TestPlaceAnalyzer(unittest.TestCase):
    def setUp(self):
        self.config = AnalysisConfig()
        self.analyzer = PlaceAnalyzer(self.config)
        self.test_places = [
            {
                "id": 1,
                "name": "東京駅",
                "latitude": 35.681236,
                "longitude": 139.767125,
                "context": "東京駅で降りて、皇居に向かいました。",
                "type": "station/railway",
                "geocoding": {
                    "status": "OK",
                    "confidence": 0.9
                },
                "frequency": 5
            },
            {
                "id": 2,
                "name": "大阪城",
                "latitude": 34.687315,
                "longitude": 135.526237,
                "context": "大阪城を見学しました。",
                "type": "castle",
                "geocoding": {
                    "status": "OK",
                    "confidence": 0.8
                },
                "frequency": 2
            }
        ]
    
    def test_analyze_places(self):
        """場所データの分析テスト"""
        results = self.analyzer.analyze_places(self.test_places)
        
        self.assertEqual(results["total"], 2)
        self.assertEqual(results["valid_coordinates"], 2)
        self.assertEqual(results["valid_context"], 2)
        self.assertEqual(results["valid_type"], 2)
        self.assertEqual(results["valid_geocoding"], 2)
        self.assertEqual(results["frequency_issues"], 1)
        
    def test_validate_coordinates(self):
        """座標の妥当性検証テスト"""
        # 有効な座標
        self.assertTrue(self.analyzer._validate_coordinates(self.test_places[0]))
        
        # 無効な座標
        invalid_place = self.test_places[0].copy()
        invalid_place["latitude"] = 200  # 範囲外
        self.assertFalse(self.analyzer._validate_coordinates(invalid_place))
        
        # 座標なし
        no_coords_place = self.test_places[0].copy()
        del no_coords_place["latitude"]
        self.assertFalse(self.analyzer._validate_coordinates(no_coords_place))
    
    def test_analyze_context(self):
        """文脈分析テスト"""
        # 有効な文脈
        self.assertTrue(self.analyzer._analyze_context(self.test_places[0]))
        
        # 短すぎる文脈
        short_context = self.test_places[0].copy()
        short_context["context"] = "短い"
        self.assertFalse(self.analyzer._analyze_context(short_context))
        
        # 文脈なし
        no_context = self.test_places[0].copy()
        del no_context["context"]
        self.assertFalse(self.analyzer._analyze_context(no_context))
    
    def test_analyze_type(self):
        """場所タイプ分析テスト"""
        # 有効なタイプ
        self.assertTrue(self.analyzer._analyze_type(self.test_places[0]))
        
        # 詳細度が低いタイプ
        simple_type = self.test_places[0].copy()
        simple_type["type"] = "place"
        self.assertFalse(self.analyzer._analyze_type(simple_type))
        
        # タイプなし
        no_type = self.test_places[0].copy()
        del no_type["type"]
        self.assertFalse(self.analyzer._analyze_type(no_type))
    
    def test_analyze_geocoding(self):
        """ジオコーディング分析テスト"""
        # 有効なジオコーディング
        self.assertTrue(self.analyzer._analyze_geocoding(self.test_places[0]))
        
        # 信頼度が低い
        low_confidence = self.test_places[0].copy()
        low_confidence["geocoding"]["confidence"] = 0.5
        self.assertFalse(self.analyzer._analyze_geocoding(low_confidence))
        
        # ステータスがエラー
        error_status = self.test_places[0].copy()
        error_status["geocoding"]["status"] = "ERROR"
        self.assertFalse(self.analyzer._analyze_geocoding(error_status))
    
    def test_analyze_frequency(self):
        """出現頻度分析テスト"""
        # 頻度が高い
        self.assertFalse(self.analyzer._analyze_frequency(self.test_places[0]))
        
        # 頻度が低い
        self.assertTrue(self.analyzer._analyze_frequency(self.test_places[1]))
        
        # 頻度なし
        no_frequency = self.test_places[0].copy()
        del no_frequency["frequency"]
        self.assertTrue(self.analyzer._analyze_frequency(no_frequency))
    
    def test_generate_report(self):
        """レポート生成テスト"""
        results = self.analyzer.analyze_places(self.test_places)
        report = self.analyzer.generate_report(results)
        
        self.assertIn("score", report)
        self.assertIn("summary", report)
        self.assertIn("recommendations", report)
        self.assertIsInstance(report["score"], float)
        self.assertIsInstance(report["recommendations"], list)
        
    def test_empty_places(self):
        """空のデータセットテスト"""
        results = self.analyzer.analyze_places([])
        report = self.analyzer.generate_report(results)
        
        self.assertEqual(report["score"], 0)
        self.assertEqual(report["summary"], "分析対象のデータがありません")
        self.assertEqual(report["recommendations"], [])