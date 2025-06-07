#!/usr/bin/env python3
"""
文豪地図システム v3.0 Phase 3 シンプルテスト
基本機能の動作確認
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent / "bungo_project_v3"
sys.path.insert(0, str(project_root))

def test_phase3_basic():
    """Phase 3基本機能テスト"""
    print("🚀 Phase 3 シンプルテスト開始")
    print("="*50)
    
    try:
        # 1. 青空文庫クライアントテスト
        print("\n📚 青空文庫クライアントテスト")
        from bungo_map.extraction.aozora_client import AozoraClient
        
        client = AozoraClient()
        
        # テキスト取得テスト
        text = client.get_work_text("坊っちゃん", "夏目漱石")
        if text:
            print(f"   ✅ テキスト取得成功: {len(text)} 文字")
            print(f"   📝 最初の100文字: {text[:100]}...")
        else:
            print("   ❌ テキスト取得失敗")
        
        # 2. ジオコーディングサービステスト  
        print("\n🌍 ジオコーディングサービステスト")
        from bungo_map.geo.geocoding_service import GeocodingService
        
        import asyncio
        
        async def test_geocoding():
            geo_service = GeocodingService()
            
            test_places = ["東京", "京都", "松山"]
            
            for place in test_places:
                result = await geo_service.geocode_place(place)
                if result:
                    print(f"   ✅ {place}: ({result.latitude:.4f}, {result.longitude:.4f}) 信頼度:{result.confidence:.2f}")
                else:
                    print(f"   ❌ {place}: 座標取得失敗")
        
        asyncio.run(test_geocoding())
        
        # 3. 地名正規化テスト
        print("\n📍 地名正規化テスト")
        from bungo_map.quality.place_normalizer import PlaceNormalizer
        
        normalizer = PlaceNormalizer()
        test_places = ["松山市", "江戸", "羅生門", "平安京"]
        
        for place in test_places:
            normalized, confidence = normalizer.normalize_place_name(place)
            print(f"   📌 {place} → {normalized} (信頼度: {confidence:.2f})")
        
        print("\n✅ Phase 3基本機能テスト完了！")
        
    except ImportError as e:
        print(f"   ❌ インポートエラー: {e}")
        print("   必要なモジュールが見つかりません")
    except Exception as e:
        print(f"   ❌ テストエラー: {e}")

if __name__ == "__main__":
    test_phase3_basic() 