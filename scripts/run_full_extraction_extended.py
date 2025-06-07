#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪ゆかり地図システム v3.0 - 拡張版完全データ抽出パイプライン
青空文庫の主要文豪作品からGiNZA+正規表現による大規模地名抽出を実行
"""

import time
import json
from datetime import datetime
from bungo_map.core.database import BungoDB
from bungo_map.extractors.aozora_extractor import AozoraExtractor
from bungo_map.extractors.ginza_place_extractor import GinzaPlaceExtractor
from bungo_map.extractors.simple_place_extractor import SimplePlaceExtractor


def get_extended_works_list():
    """拡張版作品リスト - 主要文豪15名、約30作品"""
    return [
        # 夏目漱石 (6作品)
        {
            "author_name": "夏目漱石",
            "title": "坊っちゃん",
            "text_url": "https://www.aozora.gr.jp/cards/000148/files/752_14964.html"
        },
        {
            "author_name": "夏目漱石", 
            "title": "吾輩は猫である",
            "text_url": "https://www.aozora.gr.jp/cards/000148/files/789_14547.html"
        },
        {
            "author_name": "夏目漱石",
            "title": "こころ",
            "text_url": "https://www.aozora.gr.jp/cards/000148/files/773_14560.html"
        },
        {
            "author_name": "夏目漱石",
            "title": "三四郎",
            "text_url": "https://www.aozora.gr.jp/cards/000148/files/794_14946.html"
        },
        {
            "author_name": "夏目漱石",
            "title": "それから",
            "text_url": "https://www.aozora.gr.jp/cards/000148/files/783_14954.html"
        },
        {
            "author_name": "夏目漱石",
            "title": "門",
            "text_url": "https://www.aozora.gr.jp/cards/000148/files/784_14965.html"
        },
        
        # 芥川龍之介 (5作品)
        {
            "author_name": "芥川龍之介",
            "title": "羅生門",
            "text_url": "https://www.aozora.gr.jp/cards/000879/files/127_15260.html"
        },
        {
            "author_name": "芥川龍之介",
            "title": "鼻",
            "text_url": "https://www.aozora.gr.jp/cards/000879/files/92_15261.html"
        },
        {
            "author_name": "芥川龍之介",
            "title": "蜘蛛の糸",
            "text_url": "https://www.aozora.gr.jp/cards/000879/files/92_15183.html"
        },
        {
            "author_name": "芥川龍之介",
            "title": "地獄変",
            "text_url": "https://www.aozora.gr.jp/cards/000879/files/127_15183.html"
        },
        {
            "author_name": "芥川龍之介",
            "title": "河童",
            "text_url": "https://www.aozora.gr.jp/cards/000879/files/69_15191.html"
        },
        
        # 太宰治 (4作品)
        {
            "author_name": "太宰治",
            "title": "走れメロス",
            "text_url": "https://www.aozora.gr.jp/cards/000035/files/1567_14913.html"
        },
        {
            "author_name": "太宰治",
            "title": "人間失格",
            "text_url": "https://www.aozora.gr.jp/cards/000035/files/301_14912.html"
        },
        {
            "author_name": "太宰治",
            "title": "津軽",
            "text_url": "https://www.aozora.gr.jp/cards/000035/files/2280_15100.html"
        },
        {
            "author_name": "太宰治",
            "title": "斜陽",
            "text_url": "https://www.aozora.gr.jp/cards/000035/files/1565_8559.html"
        },
        
        # 樋口一葉 (2作品)
        {
            "author_name": "樋口一葉",
            "title": "たけくらべ",
            "text_url": "https://www.aozora.gr.jp/cards/000064/files/392_19874.html"
        },
        {
            "author_name": "樋口一葉",
            "title": "にごりえ",
            "text_url": "https://www.aozora.gr.jp/cards/000064/files/393_19877.html"
        },
        
        # 石川啄木 (2作品)
        {
            "author_name": "石川啄木",
            "title": "一握の砂",
            "text_url": "https://www.aozora.gr.jp/cards/000153/files/1235_19874.html"
        },
        {
            "author_name": "石川啄木",
            "title": "悲しき玩具",
            "text_url": "https://www.aozora.gr.jp/cards/000153/files/1236_19875.html"
        },
        
        # 森鴎外 (3作品)
        {
            "author_name": "森鴎外",
            "title": "舞姫",
            "text_url": "https://www.aozora.gr.jp/cards/000129/files/695_19725.html"
        },
        {
            "author_name": "森鴎外",
            "title": "高瀬舟",
            "text_url": "https://www.aozora.gr.jp/cards/000129/files/645_19728.html"
        },
        {
            "author_name": "森鴎外",
            "title": "山椒大夫",
            "text_url": "https://www.aozora.gr.jp/cards/000129/files/682_19729.html"
        },
        
        # 宮沢賢治 (3作品)
        {
            "author_name": "宮沢賢治",
            "title": "銀河鉄道の夜",
            "text_url": "https://www.aozora.gr.jp/cards/000081/files/456_15050.html"
        },
        {
            "author_name": "宮沢賢治",
            "title": "風の又三郎",
            "text_url": "https://www.aozora.gr.jp/cards/000081/files/1920_18876.html"
        },
        {
            "author_name": "宮沢賢治",
            "title": "注文の多い料理店",
            "text_url": "https://www.aozora.gr.jp/cards/000081/files/43754_17659.html"
        },
        
        # 与謝野晶子 (1作品)
        {
            "author_name": "与謝野晶子",
            "title": "みだれ髪",
            "text_url": "https://www.aozora.gr.jp/cards/000885/files/14808_19230.html"
        },
        
        # 正岡子規 (1作品)
        {
            "author_name": "正岡子規",
            "title": "病床六尺",
            "text_url": "https://www.aozora.gr.jp/cards/000305/files/1557_19231.html"
        },
        
        # 小泉八雲 (1作品)
        {
            "author_name": "小泉八雲",
            "title": "怪談",
            "text_url": "https://www.aozora.gr.jp/cards/000258/files/42320_30332.html"
        }
    ]


def run_extended_extraction():
    """拡張版完全データ抽出パイプラインの実行"""
    print("🚀 文豪ゆかり地図システム v3.0 - 拡張版データ抽出開始")
    print("=" * 80)
    
    start_time = time.time()
    
    # 1. データベース初期化
    print("\n📊 1. データベース初期化")
    print("-" * 50)
    db = BungoDB()
    print("✅ データベース接続完了")
    
    # 2. 抽出システム初期化
    print("\n🔍 2. 拡張抽出システム初期化")
    print("-" * 50)
    
    aozora_extractor = AozoraExtractor()
    ginza_extractor = GinzaPlaceExtractor() 
    simple_extractor = SimplePlaceExtractor()
    
    print("✅ 全抽出器初期化完了")
    
    # 3. 拡張作品リストからの地名抽出実行
    print("\n🏞️ 3. 拡張作品リスト地名抽出実行")
    print("-" * 50)
    
    extended_works = get_extended_works_list()
    total_places = 0
    total_ginza = 0
    total_simple = 0
    failed_works = []
    
    print(f"📚 対象作品数: {len(extended_works)}作品")
    print()
    
    for idx, work_info in enumerate(extended_works, 1):
        print(f"📚 [{idx:2d}/{len(extended_works)}] {work_info['author_name']} - {work_info['title']}")
        print("   " + "-" * 60)
        
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
            print(f"   📥 テキスト取得中... {work_info['text_url']}")
            text = aozora_extractor.download_and_extract_text(work_info['text_url'])
            
            if not text:
                print("   ❌ テキスト取得失敗")
                failed_works.append(work_info['title'])
                continue
            
            text_length = len(text)
            print(f"   📄 テキスト長: {text_length:,}文字")
            
            # テキストサイズに応じて処理範囲を調整
            if text_length > 100000:  # 100KB超の場合
                ginza_text = text[:50000]  # GiNZAは50KBまで
                print(f"   🔬 GiNZA処理範囲: {len(ginza_text):,}文字 (制限適用)")
            else:
                ginza_text = text
                print(f"   🔬 GiNZA処理範囲: {len(ginza_text):,}文字 (全文)")
            
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
                    print(f"     ⚠️ GiNZA地名保存エラー: {place.place_name}")
            
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
                    print(f"     ⚠️ 正規表現地名保存エラー: {place.place_name}")
            
            total_saved = ginza_saved + simple_saved
            print(f"   💾 DB保存: {total_saved:2d}個 (GiNZA: {ginza_saved}, 正規表現: {simple_saved})")
            
            total_places += total_saved
            total_ginza += ginza_saved
            total_simple += simple_saved
            
            # 経過表示
            if idx % 5 == 0:
                elapsed = time.time() - start_time
                remaining = (elapsed / idx) * (len(extended_works) - idx)
                print(f"   📊 進捗: {idx}/{len(extended_works)} ({idx/len(extended_works)*100:.1f}%)")
                print(f"   ⏱️ 経過時間: {elapsed:.1f}秒, 残り予想: {remaining:.1f}秒")
            
            print()
            
        except Exception as e:
            print(f"   ❌ 作品処理エラー: {e}")
            failed_works.append(work_info['title'])
            print()
            continue
    
    # 4. 結果サマリー
    print("\n🎯 4. 拡張版実行結果サマリー")
    print("=" * 80)
    
    # 最終統計
    authors_count = db.get_authors_count()
    works_count = db.get_works_count()
    places_count = db.get_places_count()
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"📊 データベース最終状況:")
    print(f"   📚 作者: {authors_count:2d}件")
    print(f"   📖 作品: {works_count:2d}件")
    print(f"   🏞️ 地名: {places_count:3d}件")
    print(f"   ⏱️ 実行時間: {execution_time:.1f}秒")
    print()
    
    print(f"📈 抽出詳細:")
    print(f"   🔬 GiNZA総抽出: {total_ginza:3d}件")
    print(f"   📝 正規表現総抽出: {total_simple:3d}件")
    print(f"   📊 成功率: {(len(extended_works) - len(failed_works))/len(extended_works)*100:.1f}%")
    print()
    
    if failed_works:
        print(f"❌ 失敗作品 ({len(failed_works)}件):")
        for work in failed_works:
            print(f"   • {work}")
        print()
    
    # 統計データをJSONで保存
    stats = {
        "execution_date": datetime.now().isoformat(),
        "execution_time_seconds": execution_time,
        "total_authors": authors_count,
        "total_works": works_count,
        "total_places": places_count,
        "ginza_extractions": total_ginza,
        "regex_extractions": total_simple,
        "success_rate": (len(extended_works) - len(failed_works))/len(extended_works),
        "failed_works": failed_works
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"output/extended_extraction_stats_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"🎉 拡張版完全データ抽出パイプライン完了！")
    print(f"📄 統計データ: output/extended_extraction_stats_{timestamp}.json")
    print("=" * 80)
    
    # 地名抽出結果のサンプル表示
    print(f"\n📍 抽出地名サンプル (最新15件):")
    print("-" * 50)
    
    recent_places = db.get_recent_places(limit=15)
    for place in recent_places:
        print(f"   • {place['place_name']} ({place['extraction_method']}) - 信頼度: {place['confidence']:.2f}")
        print(f"     📚 {place['work_title']} / 📝 {place['author_name']}")
        print(f"     💬 {place['sentence'][:50]}...")
        print()


if __name__ == "__main__":
    run_extended_extraction()