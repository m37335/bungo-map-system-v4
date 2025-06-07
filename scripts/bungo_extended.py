#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪ゆかり地図システム v3.0 - 拡張版本番実行
主要文豪10名・25作品による大規模地名抽出
"""

import time
import json
from datetime import datetime
from bungo_map.core.database import BungoDB
from bungo_map.extractors.aozora_extractor import AozoraExtractor
from bungo_map.extractors.ginza_place_extractor import GinzaPlaceExtractor
from bungo_map.extractors.simple_place_extractor import SimplePlaceExtractor


def get_production_works():
    """本番用作品リスト - 主要文豪10名・25作品"""
    return [
        # 夏目漱石 (6作品)
        {"author_name": "夏目漱石", "title": "坊っちゃん", "text_url": "https://www.aozora.gr.jp/cards/000148/files/752_14964.html"},
        {"author_name": "夏目漱石", "title": "吾輩は猫である", "text_url": "https://www.aozora.gr.jp/cards/000148/files/789_14547.html"},
        {"author_name": "夏目漱石", "title": "こころ", "text_url": "https://www.aozora.gr.jp/cards/000148/files/773_14560.html"},
        {"author_name": "夏目漱石", "title": "三四郎", "text_url": "https://www.aozora.gr.jp/cards/000148/files/794_14946.html"},
        {"author_name": "夏目漱石", "title": "それから", "text_url": "https://www.aozora.gr.jp/cards/000148/files/783_14954.html"},
        {"author_name": "夏目漱石", "title": "門", "text_url": "https://www.aozora.gr.jp/cards/000148/files/784_14965.html"},
        
        # 芥川龍之介 (4作品)
        {"author_name": "芥川龍之介", "title": "羅生門", "text_url": "https://www.aozora.gr.jp/cards/000879/files/127_15260.html"},
        {"author_name": "芥川龍之介", "title": "鼻", "text_url": "https://www.aozora.gr.jp/cards/000879/files/92_15261.html"},
        {"author_name": "芥川龍之介", "title": "蜘蛛の糸", "text_url": "https://www.aozora.gr.jp/cards/000879/files/92_15183.html"},
        {"author_name": "芥川龍之介", "title": "地獄変", "text_url": "https://www.aozora.gr.jp/cards/000879/files/127_15183.html"},
        
        # 太宰治 (4作品)
        {"author_name": "太宰治", "title": "走れメロス", "text_url": "https://www.aozora.gr.jp/cards/000035/files/1567_14913.html"},
        {"author_name": "太宰治", "title": "人間失格", "text_url": "https://www.aozora.gr.jp/cards/000035/files/301_14912.html"},
        {"author_name": "太宰治", "title": "津軽", "text_url": "https://www.aozora.gr.jp/cards/000035/files/2280_15100.html"},
        {"author_name": "太宰治", "title": "斜陽", "text_url": "https://www.aozora.gr.jp/cards/000035/files/1565_8559.html"},
        
        # 樋口一葉 (2作品)
        {"author_name": "樋口一葉", "title": "たけくらべ", "text_url": "https://www.aozora.gr.jp/cards/000064/files/392_19874.html"},
        {"author_name": "樋口一葉", "title": "にごりえ", "text_url": "https://www.aozora.gr.jp/cards/000064/files/393_19877.html"},
        
        # 森鴎外 (3作品)
        {"author_name": "森鴎外", "title": "舞姫", "text_url": "https://www.aozora.gr.jp/cards/000129/files/695_19725.html"},
        {"author_name": "森鴎外", "title": "高瀬舟", "text_url": "https://www.aozora.gr.jp/cards/000129/files/645_19728.html"},
        {"author_name": "森鴎外", "title": "山椒大夫", "text_url": "https://www.aozora.gr.jp/cards/000129/files/682_19729.html"},
        
        # 宮沢賢治 (3作品)
        {"author_name": "宮沢賢治", "title": "銀河鉄道の夜", "text_url": "https://www.aozora.gr.jp/cards/000081/files/456_15050.html"},
        {"author_name": "宮沢賢治", "title": "風の又三郎", "text_url": "https://www.aozora.gr.jp/cards/000081/files/1920_18876.html"},
        {"author_name": "宮沢賢治", "title": "注文の多い料理店", "text_url": "https://www.aozora.gr.jp/cards/000081/files/43754_17659.html"},
        
        # 石川啄木 (2作品)
        {"author_name": "石川啄木", "title": "一握の砂", "text_url": "https://www.aozora.gr.jp/cards/000153/files/1235_19874.html"},
        {"author_name": "石川啄木", "title": "悲しき玩具", "text_url": "https://www.aozora.gr.jp/cards/000153/files/1236_19875.html"},
        
        # 与謝野晶子 (1作品)
        {"author_name": "与謝野晶子", "title": "みだれ髪", "text_url": "https://www.aozora.gr.jp/cards/000885/files/14808_19230.html"}
    ]


def main():
    """本番実行メイン関数"""
    print("🚀 文豪ゆかり地図システム v3.0 - 本番実行開始")
    print("=" * 80)
    
    start_time = time.time()
    
    # データベース・抽出器初期化
    db = BungoDB()
    aozora_extractor = AozoraExtractor()
    ginza_extractor = GinzaPlaceExtractor() 
    simple_extractor = SimplePlaceExtractor()
    
    # 作品リスト取得
    works = get_production_works()
    print(f"📚 対象作品数: {len(works)}作品")
    print(f"📝 対象作者数: {len(set(w['author_name'] for w in works))}名")
    print()
    
    # 統計変数
    total_ginza = 0
    total_simple = 0
    failed_works = []
    
    # 各作品を処理
    for idx, work_info in enumerate(works, 1):
        print(f"📚 [{idx:2d}/{len(works)}] {work_info['author_name']} - {work_info['title']}")
        
        try:
            # 作者・作品登録
            author_id = db.upsert_author(work_info['author_name'])
            work_id = db.upsert_work(author_id=author_id, title=work_info['title'], wiki_url=work_info['text_url'])
            
            # テキスト取得
            text = aozora_extractor.download_and_extract_text(work_info['text_url'])
            if not text:
                print("   ❌ テキスト取得失敗")
                failed_works.append(work_info['title'])
                continue
            
            print(f"   📄 テキスト長: {len(text):,}文字")
            
            # 地名抽出
            ginza_text = text[:50000] if len(text) > 50000 else text  # GiNZA制限
            ginza_places = ginza_extractor.extract_places_from_text(work_id, ginza_text, work_info['text_url'])
            simple_places = simple_extractor.extract_places_from_text(work_id, text, work_info['text_url'])
            
            print(f"   🔬 GiNZA: {len(ginza_places):2d}個, 📝 正規表現: {len(simple_places):2d}個")
            
            # データベース保存
            ginza_saved = 0
            simple_saved = 0
            
            for place in ginza_places:
                try:
                    db.upsert_place(work_id, place.place_name, place.before_text, place.sentence, place.after_text, place.aozora_url, place.extraction_method, place.confidence)
                    ginza_saved += 1
                except: pass
            
            for place in simple_places:
                try:
                    db.upsert_place(work_id, place.place_name, place.before_text, place.sentence, place.after_text, place.aozora_url, place.extraction_method, place.confidence)
                    simple_saved += 1
                except: pass
            
            print(f"   💾 DB保存: {ginza_saved + simple_saved:2d}個")
            total_ginza += ginza_saved
            total_simple += simple_saved
            
        except Exception as e:
            print(f"   ❌ エラー: {e}")
            failed_works.append(work_info['title'])
        
        print()
    
    # 最終結果
    end_time = time.time()
    execution_time = end_time - start_time
    
    authors_count = db.get_authors_count()
    works_count = db.get_works_count()
    places_count = db.get_places_count()
    
    print("🎯 本番実行結果")
    print("=" * 80)
    print(f"📊 最終データベース状況:")
    print(f"   📚 作者: {authors_count:2d}件")
    print(f"   📖 作品: {works_count:2d}件")
    print(f"   🏞️ 地名: {places_count:3d}件")
    print(f"   ⏱️ 実行時間: {execution_time:.1f}秒")
    print()
    print(f"📈 抽出詳細:")
    print(f"   🔬 GiNZA総抽出: {total_ginza:3d}件")
    print(f"   📝 正規表現総抽出: {total_simple:3d}件")
    print(f"   📊 成功率: {(len(works) - len(failed_works))/len(works)*100:.1f}%")
    
    # 統計保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stats = {
        "execution_date": datetime.now().isoformat(),
        "execution_time_seconds": execution_time,
        "total_authors": authors_count,
        "total_works": works_count,
        "total_places": places_count,
        "ginza_extractions": total_ginza,
        "regex_extractions": total_simple,
        "success_rate": (len(works) - len(failed_works))/len(works),
        "failed_works": failed_works
    }
    
    with open(f"output/production_stats_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 本番実行完了！統計データ: output/production_stats_{timestamp}.json")
    
    # 最新地名サンプル
    print(f"\n📍 最新抽出地名 (15件):")
    print("-" * 50)
    recent_places = db.get_recent_places(limit=15)
    for place in recent_places:
        print(f"• {place['place_name']} ({place['extraction_method'][:6]}) - {place['confidence']:.2f}")
        print(f"  📚 {place['work_title']} / 📝 {place['author_name']}")
        print(f"  💬 {place['sentence'][:45]}...")
        print()


if __name__ == "__main__":
    main() 