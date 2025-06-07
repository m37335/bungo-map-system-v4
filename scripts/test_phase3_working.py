#!/usr/bin/env python3
"""
文豪地図システム v3.0 Phase 3 実働テスト
実際に動作する機能のみテスト
"""

import sys
import asyncio
from pathlib import Path

# bungo_project_v3をパスに追加
project_root = Path("bungo_project_v3")
sys.path.insert(0, str(project_root))


def test_aozora_client():
    """青空文庫クライアントテスト"""
    print("📚 青空文庫クライアント実働テスト")
    print("="*40)
    
    try:
        from bungo_map.extraction.aozora_client import AozoraClient
        
        client = AozoraClient()
        
        # 利用可能作品確認
        works = client.list_available_works()
        print(f"   📋 利用可能作品: {works}")
        
        # テキスト取得テスト
        test_works = ["坊っちゃん", "羅生門", "走れメロス"]
        
        for title in test_works:
            text = client.get_work_text(title, "テスト作者")
            if text:
                hash_value = client.calculate_content_hash(text)
                print(f"   📖 {title}: {len(text)} 文字, ハッシュ: {hash_value[:10]}...")
            else:
                print(f"   ❌ {title}: テキスト取得失敗")
        
        print("   ✅ 青空文庫クライアント動作確認")
        return True
        
    except Exception as e:
        print(f"   ❌ 青空文庫クライアントエラー: {e}")
        return False


async def test_geocoding_service():
    """ジオコーディングサービステスト"""
    print("\n🗺️ ジオコーディングサービス実働テスト")
    print("="*40)
    
    try:
        from bungo_map.geo.geocoding_service import GeocodingService
        
        geo_service = GeocodingService()
        
        # テスト地名
        test_places = [
            "東京", "京都", "松山", "道後温泉", 
            "江戸", "羅生門", "朱雀大路", "シラクス"
        ]
        
        successful_count = 0
        
        print("   🗺️ 地名ジオコーディングテスト:")
        for place_name in test_places:
            result = await geo_service.geocode_place(place_name)
            if result:
                print(f"      ✅ {place_name}: ({result.latitude:.4f}, {result.longitude:.4f}) [{result.source}]")
                successful_count += 1
            else:
                print(f"      ❌ {place_name}: 座標取得失敗")
        
        success_rate = successful_count / len(test_places)
        print(f"\n   📊 ジオコーディング成功率: {success_rate*100:.1f}% ({successful_count}/{len(test_places)})")
        
        if success_rate >= 0.8:
            print("   ✅ ジオコーディングサービス動作確認")
            return True
        else:
            print("   ⚠️ ジオコーディング成功率が低い")
            return False
        
    except Exception as e:
        print(f"   ❌ ジオコーディングサービスエラー: {e}")
        return False


def test_place_normalizer():
    """地名正規化テスト"""
    print("\n📍 地名正規化実働テスト")
    print("="*30)
    
    try:
        from bungo_map.quality.place_normalizer import PlaceNormalizer
        
        normalizer = PlaceNormalizer()
        
        # 正規化テストケース
        test_cases = [
            ("松山市", "松山"),
            ("江戸", "東京"), 
            ("平安京", "京都"),
            ("大坂", "大阪"),
            ("羅生門", "羅生門"),  # そのまま
        ]
        
        success_count = 0
        
        print("   📌 地名正規化テスト:")
        for original, expected in test_cases:
            try:
                normalized, confidence = normalizer.normalize_place_name(original)
                match = "✅" if normalized == expected else "⚠️"
                print(f"      {match} {original} → {normalized} (期待: {expected}, 信頼度: {confidence:.2f})")
                if normalized == expected:
                    success_count += 1
            except Exception as e:
                print(f"      ❌ {original}: 正規化エラー: {e}")
        
        success_rate = success_count / len(test_cases)
        print(f"\n   📊 正規化成功率: {success_rate*100:.1f}% ({success_count}/{len(test_cases)})")
        
        if success_rate >= 0.6:
            print("   ✅ 地名正規化システム動作確認")
            return True
        else:
            print("   ⚠️ 地名正規化成功率が低い")
            return False
        
    except Exception as e:
        print(f"   ❌ 地名正規化エラー: {e}")
        return False


def test_integration_pipeline():
    """統合パイプラインテスト"""
    print("\n🔄 統合パイプライン実働テスト")
    print("="*40)
    
    try:
        from bungo_map.extraction.aozora_client import AozoraClient
        from bungo_map.geo.geocoding_service import GeocodingService
        
        # 1. テキスト取得
        client = AozoraClient()
        text = client.get_work_text("坊っちゃん", "夏目漱石")
        print(f"   📖 テキスト取得: {len(text)} 文字")
        
        # 2. 簡単な地名抽出（正規表現版）
        import re
        place_pattern = r'(東京|京都|大阪|松山|道後温泉|小倉|新橋|江戸|平安京|羅生門|朱雀大路|洛中)'
        
        found_places = re.findall(place_pattern, text)
        unique_places = list(set(found_places))
        print(f"   📍 抽出地名: {unique_places}")
        
        # 3. ジオコーディング
        geo_service = GeocodingService()
        geocoded_results = []
        
        print("   🗺️ ジオコーディング実行:")
        for place in unique_places[:5]:  # 最大5件
            result = geo_service.geocode_place_sync(place)
            if result:
                geocoded_results.append(result)
                print(f"      ✅ {place}: ({result.latitude:.4f}, {result.longitude:.4f})")
        
        print(f"\n   📊 パイプライン結果:")
        print(f"      - 入力テキスト: {len(text)} 文字")
        print(f"      - 抽出地名: {len(unique_places)} 件")
        print(f"      - 座標取得: {len(geocoded_results)} 件")
        
        if len(geocoded_results) > 0:
            print("   ✅ 統合パイプライン動作確認")
            return True
        else:
            print("   ❌ 統合パイプライン失敗")
            return False
        
    except Exception as e:
        print(f"   ❌ 統合パイプラインエラー: {e}")
        return False


async def main():
    """Phase 3実働テスト実行"""
    print("🚀 文豪地図システム v3.0 Phase 3 実働テスト")
    print("="*60)
    
    results = []
    
    # 各コンポーネントテスト
    results.append(test_aozora_client())
    results.append(await test_geocoding_service())
    results.append(test_place_normalizer())
    results.append(test_integration_pipeline())
    
    # 結果サマリー
    print("\n" + "="*60)
    print("📋 Phase 3実働テスト結果")
    print("="*60)
    
    success_count = sum(results)
    total_tests = len(results)
    success_rate = success_count / total_tests
    
    test_names = [
        "青空文庫クライアント",
        "ジオコーディングサービス", 
        "地名正規化システム",
        "統合パイプライン"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 合格" if result else "❌ 不合格"
        print(f"   {status} {name}")
    
    print(f"\n📊 総合成功率: {success_rate*100:.1f}% ({success_count}/{total_tests})")
    
    if success_rate >= 0.75:
        print("\n🎉 Phase 3基本機能は動作しています！")
        print("   実用的な文豪地図システムとして機能確認完了")
    elif success_rate >= 0.5:
        print("\n⚠️ Phase 3は部分的に動作しています")
        print("   一部機能に問題がありますが、基本機能は利用可能")
    else:
        print("\n❌ Phase 3に重大な問題があります")
        print("   システム修正が必要です")


if __name__ == "__main__":
    asyncio.run(main()) 