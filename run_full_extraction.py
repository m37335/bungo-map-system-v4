#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪ゆかり地図システム - 完全データ拡充パイプライン
青空文庫テキストからGiNZA+正規表現による地名抽出を実行
"""

import time
from bungo_map.core.database import BungoDB
from bungo_map.extractors.aozora_extractor import AozoraExtractor
from bungo_map.extractors.ginza_place_extractor import GinzaPlaceExtractor
from bungo_map.extractors.simple_place_extractor import SimplePlaceExtractor


def run_full_extraction():
    """完全データ拡充パイプラインの実行"""
    print("🚀 文豪ゆかり地図システム - 完全データ拡充開始")
    print("=" * 70)
    
    start_time = time.time()
    
    # 1. データベース初期化
    print("\n📊 1. データベース初期化")
    print("-" * 40)
    db = BungoDB()
    print("✅ データベース接続完了")
    
    # 2. 青空文庫地名抽出システム初期化
    print("\n🔍 2. 青空文庫地名抽出システム初期化")
    print("-" * 40)
    
    aozora_extractor = AozoraExtractor()
    ginza_extractor = GinzaPlaceExtractor() 
    simple_extractor = SimplePlaceExtractor()
    
    print("✅ 全抽出器初期化完了")
    
    # 3. 青空文庫からの地名抽出実行
    print("\n🏞️ 3. 青空文庫地名抽出実行")
    print("-" * 40)
    
    # 拡張作品リストで地名抽出（本番実行）
    extended_works = aozora_extractor.get_extended_works()
    total_places = 0
    
    print(f"📚 対象作品数: {len(extended_works)}作品")
    unique_authors = set(w['author_name'] for w in extended_works)
    print(f"📝 対象作者数: {len(unique_authors)}名")
    
    for idx, work_info in enumerate(extended_works, 1):
        print(f"\n📚 {idx}. {work_info['author_name']} - {work_info['title']}")
        print("   " + "-" * 45)
        
        try:
            # 作者登録
            author_id = db.upsert_author(work_info['author_name'])
            
            # 作品登録
            work_id = db.upsert_work(
                author_id=author_id,
                title=work_info['title'],
                wiki_url=work_info.get('text_url', '')
            )
            
            # 青空文庫テキスト取得
            text = aozora_extractor.download_and_extract_text(work_info['text_url'])
            
            if not text:
                print("   ❌ テキスト取得失敗")
                continue
            
            print(f"   📄 テキスト長: {len(text):,}文字")
            
            # GiNZA地名抽出（テキストサイズ制限考慮）
            test_text = text[:30000]  # 30KB制限
            ginza_places = ginza_extractor.extract_places_from_text(
                work_id=work_id, 
                text=test_text, 
                aozora_url=work_info['text_url']
            )
            
            # 正規表現地名抽出（全テキスト）
            simple_places = simple_extractor.extract_places_from_text(
                work_id=work_id, 
                text=text,
                aozora_url=work_info['text_url']
            )
            
            print(f"   🔬 GiNZA抽出: {len(ginza_places)}個")
            print(f"   📝 正規表現抽出: {len(simple_places)}個")
            
            # データベースに地名保存
            ginza_saved = 0
            simple_saved = 0
            
            # GiNZA地名を保存
            for place in ginza_places:
                try:
                    place_id = db.upsert_place(
                        work_id=work_id,
                        place_name=place.place_name,
                        before_text=place.before_text,
                        sentence=place.sentence,
                        after_text=place.after_text,
                        aozora_url=place.aozora_url,
                        extraction_method=place.extraction_method,
                        confidence=place.confidence
                    )
                    ginza_saved += 1
                except Exception as e:
                    print(f"     ⚠️ GiNZA地名保存エラー: {place.place_name} - {e}")
            
            # 正規表現地名を保存
            for place in simple_places:
                try:
                    place_id = db.upsert_place(
                        work_id=work_id,
                        place_name=place.place_name,
                        before_text=place.before_text,
                        sentence=place.sentence,
                        after_text=place.after_text,
                        aozora_url=place.aozora_url,
                        extraction_method=place.extraction_method,
                        confidence=place.confidence
                    )
                    simple_saved += 1
                except Exception as e:
                    print(f"     ⚠️ 正規表現地名保存エラー: {place.place_name} - {e}")
            
            total_saved = ginza_saved + simple_saved
            print(f"   💾 DB保存: {total_saved}個 (GiNZA: {ginza_saved}, 正規表現: {simple_saved})")
            total_places += total_saved
            
        except Exception as e:
            print(f"   ❌ 作品処理エラー: {e}")
            continue
    
    # 4. 結果サマリー
    print("\n🎯 4. 実行結果サマリー")
    print("-" * 40)
    
    # 最終統計
    authors_count = db.get_authors_count()
    works_count = db.get_works_count()
    places_count = db.get_places_count()
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"📊 データベース最終状況:")
    print(f"   📚 作者: {authors_count}件")
    print(f"   📖 作品: {works_count}件")
    print(f"   🏞️ 地名: {places_count}件")
    print(f"   ⏱️ 実行時間: {execution_time:.1f}秒")
    
    print(f"\n🎉 完全データ拡充パイプライン完了！")
    print("=" * 70)
    
    # 地名抽出結果のサンプル表示
    print(f"\n📍 抽出地名サンプル (最新10件):")
    print("-" * 40)
    
    recent_places = db.get_recent_places(limit=10)
    for place in recent_places:
        print(f"   • {place['place_name']} ({place['extraction_method']}) - 信頼度: {place['confidence']:.2f}")
        print(f"     作品: {place['work_title']} / 作者: {place['author_name']}")
        print(f"     文脈: {place['sentence'][:60]}...")
        print()


if __name__ == "__main__":
    run_full_extraction() 