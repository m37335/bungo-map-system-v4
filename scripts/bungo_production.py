#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪ゆかり地図システム v3.0 - 本番データ抽出実行
主要文豪12名・30作品による大規模地名抽出
"""

import time
import json
from datetime import datetime
from bungo_map.core.database import BungoDB
from bungo_map.extractors.aozora_extractor import AozoraExtractor
from bungo_map.extractors.ginza_place_extractor import GinzaPlaceExtractor
from bungo_map.extractors.simple_place_extractor import SimplePlaceExtractor


def main():
    """本番実行メイン関数"""
    print("🚀 文豪ゆかり地図システム v3.0 - 本番実行開始")
    print("=" * 80)
    
    start_time = time.time()
    
    # データベース・抽出器初期化
    print("\n📊 1. システム初期化")
    print("-" * 50)
    
    db = BungoDB()
    aozora_extractor = AozoraExtractor()
    ginza_extractor = GinzaPlaceExtractor() 
    simple_extractor = SimplePlaceExtractor()
    
    print("✅ データベース接続完了")
    print("✅ 青空文庫抽出器初期化完了")
    print("✅ GiNZA地名抽出器初期化完了")
    print("✅ 正規表現地名抽出器初期化完了")
    
    # 拡張作品リスト取得
    print("\n📚 2. 拡張作品リスト取得")
    print("-" * 50)
    
    works = aozora_extractor.get_extended_works()
    unique_authors = set(w['author_name'] for w in works)
    
    print(f"📚 対象作品数: {len(works)}作品")
    print(f"📝 対象作者数: {len(unique_authors)}名")
    print()
    print("📝 対象作者一覧:")
    for i, author in enumerate(sorted(unique_authors), 1):
        author_works_count = sum(1 for w in works if w['author_name'] == author)
        print(f"   {i:2d}. {author} ({author_works_count}作品)")
    print()
    
    # 統計変数
    total_ginza = 0
    total_simple = 0
    total_saved = 0
    failed_works = []
    successful_works = []
    
    # 各作品を処理
    print("🏞️ 3. 本番地名抽出実行")
    print("-" * 50)
    
    for idx, work_info in enumerate(works, 1):
        print(f"📚 [{idx:2d}/{len(works)}] {work_info['author_name']} - {work_info['title']}")
        
        try:
            # 作者・作品登録
            author_id = db.upsert_author(work_info['author_name'])
            work_id = db.upsert_work(
                author_id=author_id, 
                title=work_info['title'], 
                wiki_url=work_info['text_url']
            )
            
            # テキスト取得
            print(f"   📥 テキスト取得中...")
            text = aozora_extractor.download_and_extract_text(work_info['text_url'])
            
            if not text:
                print("   ❌ テキスト取得失敗")
                failed_works.append({
                    'title': work_info['title'],
                    'author': work_info['author_name'],
                    'error': 'テキスト取得失敗'
                })
                continue
            
            text_length = len(text)
            print(f"   📄 テキスト長: {text_length:,}文字")
            
            # テキストサイズに応じてGiNZA処理範囲を調整
            if text_length > 100000:  # 100KB超の場合
                ginza_text = text[:50000]  # GiNZAは50KBまで
                print(f"   🔬 GiNZA処理範囲: {len(ginza_text):,}文字 (制限適用)")
            else:
                ginza_text = text
                print(f"   🔬 GiNZA処理範囲: {len(ginza_text):,}文字 (全文)")
            
            # 地名抽出実行
            print(f"   🔍 地名抽出実行中...")
            
            # GiNZA地名抽出
            ginza_places = ginza_extractor.extract_places_from_text(
                work_id=work_id, 
                text=ginza_text, 
                aozora_url=work_info['text_url']
            )
            
            # 正規表現地名抽出（全テキスト）
            simple_places = simple_extractor.extract_places_from_text(
                work_id=work_id, 
                text=text,
                aozora_url=work_info['text_url']
            )
            
            ginza_count = len(ginza_places)
            simple_count = len(simple_places)
            
            print(f"   🔬 GiNZA抽出: {ginza_count:2d}個")
            print(f"   📝 正規表現抽出: {simple_count:2d}個")
            
            # データベース保存
            ginza_saved = 0
            simple_saved = 0
            
            # GiNZA地名を保存
            for place in ginza_places:
                try:
                    db.upsert_place(
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
                    print(f"     ⚠️ GiNZA地名保存エラー: {place.place_name}")
            
            # 正規表現地名を保存
            for place in simple_places:
                try:
                    db.upsert_place(
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
                    print(f"     ⚠️ 正規表現地名保存エラー: {place.place_name}")
            
            work_total_saved = ginza_saved + simple_saved
            print(f"   💾 DB保存: {work_total_saved:2d}個 (GiNZA: {ginza_saved}, 正規表現: {simple_saved})")
            
            # 統計更新
            total_ginza += ginza_saved
            total_simple += simple_saved
            total_saved += work_total_saved
            
            successful_works.append({
                'title': work_info['title'],
                'author': work_info['author_name'],
                'text_length': text_length,
                'ginza_places': ginza_saved,
                'simple_places': simple_saved,
                'total_places': work_total_saved
            })
            
            # 進捗表示
            if idx % 5 == 0:
                elapsed = time.time() - start_time
                remaining_estimate = (elapsed / idx) * (len(works) - idx)
                print(f"   📊 進捗: {idx}/{len(works)} ({idx/len(works)*100:.1f}%)")
                print(f"   ⏱️ 経過: {elapsed:.1f}秒, 残り予想: {remaining_estimate:.1f}秒")
            
            print()
            
        except Exception as e:
            print(f"   ❌ 作品処理エラー: {e}")
            failed_works.append({
                'title': work_info['title'],
                'author': work_info['author_name'],
                'error': str(e)
            })
            print()
            continue
    
    # 最終結果
    end_time = time.time()
    execution_time = end_time - start_time
    
    print("🎯 4. 本番実行結果サマリー")
    print("=" * 80)
    
    # データベース最終状況
    authors_count = db.get_authors_count()
    works_count = db.get_works_count()
    places_count = db.get_places_count()
    
    success_rate = (len(successful_works) / len(works)) * 100
    
    print(f"📊 最終データベース状況:")
    print(f"   📚 作者: {authors_count:2d}件")
    print(f"   📖 作品: {works_count:2d}件")
    print(f"   🏞️ 地名: {places_count:3d}件")
    print(f"   ⏱️ 実行時間: {execution_time:.1f}秒")
    print()
    
    print(f"📈 抽出詳細統計:")
    print(f"   🔬 GiNZA総抽出: {total_ginza:3d}件")
    print(f"   📝 正規表現総抽出: {total_simple:3d}件")
    print(f"   💾 総保存件数: {total_saved:3d}件")
    print(f"   📊 成功率: {success_rate:.1f}% ({len(successful_works)}/{len(works)})")
    print()
    
    # 成功・失敗作品の詳細
    if successful_works:
        print(f"✅ 成功作品 ({len(successful_works)}件):")
        for work in successful_works[:10]:  # 上位10件表示
            print(f"   • {work['title']} / {work['author']} - {work['total_places']}地名")
        if len(successful_works) > 10:
            print(f"   ... 他{len(successful_works) - 10}件")
        print()
    
    if failed_works:
        print(f"❌ 失敗作品 ({len(failed_works)}件):")
        for work in failed_works:
            print(f"   • {work['title']} / {work['author']} - {work['error']}")
        print()
    
    # 統計データをJSONで保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stats = {
        "execution_info": {
            "execution_date": datetime.now().isoformat(),
            "execution_time_seconds": round(execution_time, 2),
            "version": "v3.0 Production"
        },
        "database_stats": {
            "total_authors": authors_count,
            "total_works": works_count,
            "total_places": places_count
        },
        "extraction_stats": {
            "ginza_extractions": total_ginza,
            "regex_extractions": total_simple,
            "total_saved": total_saved,
            "success_rate": round(success_rate, 2)
        },
        "successful_works": successful_works,
        "failed_works": failed_works
    }
    
    # 出力ディレクトリの確認
    import os
    os.makedirs("output", exist_ok=True)
    
    with open(f"output/production_stats_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"📄 詳細統計データ: output/production_stats_{timestamp}.json")
    print()
    
    # 地名抽出結果のサンプル表示
    print(f"📍 最新抽出地名サンプル (20件):")
    print("-" * 60)
    
    recent_places = db.get_recent_places(limit=20)
    for i, place in enumerate(recent_places, 1):
        method_short = place['extraction_method'][:6]
        print(f"{i:2d}. {place['place_name']} ({method_short}) - 信頼度: {place['confidence']:.2f}")
        print(f"    📚 {place['work_title']} / 📝 {place['author_name']}")
        print(f"    💬 {place['sentence'][:45]}...")
        print()
    
    print(f"🎉 文豪ゆかり地図システム v3.0 本番実行完了！")
    print("=" * 80)


if __name__ == "__main__":
    main() 