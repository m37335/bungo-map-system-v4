#!/usr/bin/env python3
"""
文豪地図システム v3.0 Phase 2 統合テスト
3階層正規化DB + 地名正規化 + 品質管理機能のテスト
"""

import sys
import os
import asyncio
import sqlite3
import json
import tempfile
from pathlib import Path
from typing import Dict, List

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from bungo_map.database.db_manager import DatabaseManager, Author, Work, CanonicalPlace, PlaceContext
from bungo_map.quality.place_normalizer import PlaceNormalizer
from bungo_map.config.config_manager import get_config_manager


class Phase2IntegrationTest:
    """Phase 2統合テスト"""
    
    def __init__(self):
        # テスト用一時データベース
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db_manager = DatabaseManager(db_path=self.temp_db.name)
        self.place_normalizer = PlaceNormalizer()
        
        # テストデータ
        self.test_authors = [
            {"name": "夏目漱石", "priority": "high"},
            {"name": "芥川龍之介", "priority": "high"},
            {"name": "太宰治", "priority": "high"}
        ]
        
        self.test_works = [
            {"author": "夏目漱石", "title": "坊っちゃん"},
            {"author": "芥川龍之介", "title": "羅生門"},
            {"author": "太宰治", "title": "走れメロス"}
        ]
        
        self.test_places = [
            "松山", "松山市", "愛媛県松山市",  # 階層重複
            "東京", "江戸", "東京市",          # 歴史的変遷
            "京都", "平安京", "京都市",        # 歴史的変遷
            "羅生門", "朱雀大路", "洛中"       # 古典地名
        ]
    
    def run_all_tests(self):
        """全テストを実行"""
        print("🚀 Phase 2統合テスト開始")
        print("=" * 60)
        
        try:
            # テスト1: データベース3階層正規化
            self.test_database_schema()
            
            # テスト2: 作者・作品・地名の関係性
            self.test_data_relationships()
            
            # テスト3: 地名正規化機能
            self.test_place_normalization()
            
            # テスト4: 重複検出・統合
            self.test_duplicate_detection()
            
            # テスト5: 統合ビュー・検索機能
            self.test_unified_views()
            
            # テスト6: GeoJSONエクスポート
            self.test_geojson_export()
            
            # テスト7: データ品質レポート
            self.test_quality_reporting()
            
            print("\n✅ 全テスト完了！")
            self.print_final_statistics()
            
        except Exception as e:
            print(f"\n❌ テストエラー: {e}")
            raise
        
        finally:
            self.cleanup()
    
    def test_database_schema(self):
        """テスト1: 3階層正規化スキーマ"""
        print("\n📋 テスト1: データベーススキーマ検証")
        
        # テーブル存在確認
        required_tables = [
            'authors', 'works', 'canonical_places', 
            'place_aliases', 'place_contexts', 'data_quality_logs'
        ]
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
        
        for table in required_tables:
            assert table in existing_tables, f"テーブル {table} が存在しません"
        
        # ビュー存在確認
        required_views = ['bungo_unified_view', 'author_place_stats', 'quality_report_view']
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='view'")
            existing_views = [row[0] for row in cursor.fetchall()]
        
        for view in required_views:
            assert view in existing_views, f"ビュー {view} が存在しません"
        
        print("   ✅ 全テーブル・ビューが正常に作成済み")
    
    def test_data_relationships(self):
        """テスト2: データの関係性テスト"""
        print("\n🔗 テスト2: データ関係性検証")
        
        # 作者データ挿入
        author_ids = {}
        for author_data in self.test_authors:
            author = Author(
                name=author_data["name"],
                priority=author_data["priority"]
            )
            author_id = self.db_manager.create_author(author)
            author_ids[author_data["name"]] = author_id
        
        print(f"   📝 作者 {len(author_ids)} 人登録")
        
        # 作品データ挿入
        work_ids = {}
        for work_data in self.test_works:
            author_id = author_ids[work_data["author"]]
            work = Work(
                author_id=author_id,
                title=work_data["title"]
            )
            work_id = self.db_manager.create_work(work)
            work_ids[work_data["title"]] = work_id
        
        print(f"   📚 作品 {len(work_ids)} 作品登録")
        
        # 地名・文脈データ挿入
        place_context_count = 0
        for i, place_name in enumerate(self.test_places):
            # 正規化地名作成
            place_id = self.db_manager.get_or_create_canonical_place(place_name)
            
            # 各作品に文脈を追加
            for work_title, work_id in work_ids.items():
                context = PlaceContext(
                    place_id=place_id,
                    work_id=work_id,
                    original_text=place_name,
                    sentence=f"テスト文: {place_name}が登場する文章です。",
                    extraction_method="test",
                    extraction_confidence=0.8
                )
                self.db_manager.create_place_context(context)
                place_context_count += 1
        
        print(f"   📍 地名文脈 {place_context_count} 件登録")
        
        # 関係性検証
        stats = self.db_manager.get_database_stats()
        expected_stats = {
            'authors': len(self.test_authors),
            'works': len(self.test_works),
            'place_contexts': place_context_count
        }
        
        for table, expected_count in expected_stats.items():
            actual_count = stats[table]
            assert actual_count == expected_count, f"{table}: 期待値{expected_count}, 実際{actual_count}"
        
        print("   ✅ データ関係性検証完了")
    
    def test_place_normalization(self):
        """テスト3: 地名正規化機能"""
        print("\n🎯 テスト3: 地名正規化検証")
        
        # 正規化テストケース
        test_cases = [
            ("松山市", "松山", 0.8),
            ("愛媛県松山市", "松山", 0.8),
            ("江戸", "東京", 0.95),
            ("平安京", "京都", 0.95),
            ("羅生門", "京都", 0.6),  # パターンマッチング
        ]
        
        for original, expected_normalized, min_confidence in test_cases:
            normalized, confidence = self.place_normalizer.normalize_place_name(original)
            
            print(f"   {original} → {normalized} (信頼度: {confidence:.2f})")
            
            assert normalized == expected_normalized, f"正規化エラー: {original} → {normalized} (期待: {expected_normalized})"
            assert confidence >= min_confidence, f"信頼度不足: {confidence} < {min_confidence}"
        
        print("   ✅ 地名正規化機能正常")
    
    def test_duplicate_detection(self):
        """テスト4: 重複検出機能"""
        print("\n🔍 テスト4: 重複検出検証")
        
        # 重複検出
        duplicate_groups = self.place_normalizer.detect_duplicates(self.test_places)
        
        print(f"   検出された重複グループ: {len(duplicate_groups)} 個")
        
        for group in duplicate_groups:
            print(f"   📌 {group.canonical_name}: {group.variants} (信頼度: {group.merge_confidence:.2f})")
            print(f"      推奨アクション: {group.suggested_action}")
        
        # 期待される重複グループ数の検証
        assert len(duplicate_groups) >= 2, "十分な重複グループが検出されていません"
        
        # 自動統合とマニュアル確認の分類検証
        auto_merge_count = len([g for g in duplicate_groups if g.suggested_action == "auto_merge"])
        manual_review_count = len([g for g in duplicate_groups if g.suggested_action == "manual_review"])
        
        print(f"   自動統合可能: {auto_merge_count}, 手動確認必要: {manual_review_count}")
        
        print("   ✅ 重複検出機能正常")
    
    def test_unified_views(self):
        """テスト5: 統合ビュー・検索機能"""
        print("\n🔎 テスト5: 統合ビュー・検索検証")
        
        # 統合検索テスト
        search_results = self.db_manager.search_unified_data(
            author_name="夏目",
            limit=10
        )
        
        print(f"   作者名検索「夏目」: {len(search_results)} 件")
        assert len(search_results) > 0, "作者名検索で結果が見つかりません"
        
        # 地名検索テスト
        place_search_results = self.db_manager.search_unified_data(
            place_name="松山",
            limit=10
        )
        
        print(f"   地名検索「松山」: {len(place_search_results)} 件")
        assert len(place_search_results) > 0, "地名検索で結果が見つかりません"
        
        # 作者統計テスト
        author_stats = self.db_manager.get_author_statistics()
        print(f"   作者統計: {len(author_stats)} 人")
        
        for stat in author_stats[:3]:  # 上位3人
            print(f"   📊 {stat['author_name']}: {stat['unique_places']} 地名, {stat['total_contexts']} 文脈")
        
        print("   ✅ 統合ビュー・検索機能正常")
    
    def test_geojson_export(self):
        """テスト6: GeoJSONエクスポート"""
        print("\n🗺️ テスト6: GeoJSONエクスポート検証")
        
        # サンプル座標データを追加
        sample_coordinates = {
            "東京": (35.6762, 139.6503),
            "京都": (35.0116, 135.7681),
            "松山": (33.8416, 132.7658)
        }
        
        with self.db_manager.get_connection() as conn:
            for place_name, (lat, lng) in sample_coordinates.items():
                conn.execute("""
                    UPDATE canonical_places 
                    SET latitude = ?, longitude = ?
                    WHERE canonical_name = ?
                """, (lat, lng, place_name))
        
        # GeoJSON生成
        geojson_data = self.db_manager.export_to_geojson()
        
        print(f"   GeoJSON地点数: {len(geojson_data['features'])} 箇所")
        
        # GeoJSON構造検証
        assert geojson_data["type"] == "FeatureCollection", "GeoJSON形式エラー"
        assert len(geojson_data["features"]) > 0, "地理座標データが不足"
        
        # 個別地点検証
        for feature in geojson_data["features"]:
            assert feature["type"] == "Feature", "Feature形式エラー"
            assert "geometry" in feature, "geometry情報なし"
            assert "properties" in feature, "properties情報なし"
            
            coords = feature["geometry"]["coordinates"]
            assert len(coords) == 2, "座標情報が不正"
            assert isinstance(coords[0], float) and isinstance(coords[1], float), "座標が数値でない"
        
        print("   ✅ GeoJSONエクスポート機能正常")
    
    def test_quality_reporting(self):
        """テスト7: データ品質レポート"""
        print("\n📊 テスト7: 品質レポート検証")
        
        # 品質レポート生成
        quality_report = self.place_normalizer.generate_quality_report(self.test_places)
        
        print("   📋 データ品質レポート:")
        for key, value in quality_report.items():
            print(f"      {key}: {value}")
        
        # 品質指標検証
        assert quality_report["total_places"] == len(self.test_places), "総地名数が不正"
        assert quality_report["duplicate_groups"] > 0, "重複グループが検出されていない"
        assert quality_report["normalization_applied"] > 0, "正規化が適用されていない"
        
        # データベース品質レポート
        db_quality_report = self.db_manager.get_quality_report()
        
        print(f"   📊 DB品質レポート: {len(db_quality_report)} 作品")
        
        for report in db_quality_report[:3]:  # 上位3作品
            print(f"      {report['work_title']}: {report['place_count']} 地名")
        
        print("   ✅ 品質レポート機能正常")
    
    def print_final_statistics(self):
        """最終統計を表示"""
        print("\n" + "="*60)
        print("📈 Phase 2実装成果まとめ")
        print("="*60)
        
        # データベース統計
        db_stats = self.db_manager.get_database_stats()
        print("\n🗄️ データベース統計:")
        for table, count in db_stats.items():
            print(f"   {table}: {count} 件")
        
        # 品質改善統計
        quality_report = self.place_normalizer.generate_quality_report(self.test_places)
        print(f"\n🎯 データ品質改善:")
        print(f"   重複除去対象: {quality_report['duplicates_detected']} 件")
        print(f"   正規化適用: {quality_report['normalization_applied']} 件")
        print(f"   品質改善率: {quality_report['quality_improvement_potential']}")
        
        # v2との比較
        print(f"\n🚀 v2.0からの主な改善:")
        print(f"   ✅ 3階層正規化DB: authors/works/places構造")
        print(f"   ✅ 地名正規化機能: 歴史的変遷・表記ゆれ対応")
        print(f"   ✅ 重複検出・自動統合機能")
        print(f"   ✅ 統合ビュー・高速検索")
        print(f"   ✅ 品質レポート・監視機能")
        print(f"   ✅ GeoJSON最適化エクスポート")
    
    def cleanup(self):
        """テスト後のクリーンアップ"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass


def main():
    """Phase 2統合テスト実行"""
    test_runner = Phase2IntegrationTest()
    test_runner.run_all_tests()


if __name__ == "__main__":
    main() 