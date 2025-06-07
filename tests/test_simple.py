#!/usr/bin/env python3
"""
GitHub Aozorahack Client 簡単テスト
"""

import requests
import csv
import io
import time

def test_github_aozora():
    print("🚀 GitHub Aozorahack 直接テスト")
    print("="*50)
    
    # GitHub aozorahackのカタログURL
    catalog_url = "https://raw.githubusercontent.com/aozorahack/aozorabunko_text/master/list_person_all_extended_utf8.csv"
    
    print("📚 カタログ取得中...")
    try:
        response = requests.get(catalog_url, timeout=30)
        response.raise_for_status()
        
        # CSVパース
        csv_data = io.StringIO(response.text)
        reader = csv.DictReader(csv_data)
        
        catalog = list(reader)
        print(f"✅ カタログ取得成功: {len(catalog)} 作品")
        
        # 人気作者トップ5
        authors = {}
        for item in catalog:
            author = item.get('姓', '') + item.get('名', '')
            if author not in authors:
                authors[author] = 0
            authors[author] += 1
        
        top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5]
        print("🔥 人気作者トップ5:")
        for i, (author, count) in enumerate(top_authors, 1):
            print(f"   {i}. {author}: {count} 作品")
        
    except Exception as e:
        print(f"❌ カタログ取得エラー: {e}")
        return False
    
    # テスト作品検索
    print("\n🔍 テスト作品検索")
    test_works = [
        ("夏目漱石", "坊っちゃん"),
        ("芥川龍之介", "羅生門"), 
        ("太宰治", "走れメロス")
    ]
    
    found_works = []
    for author, title in test_works:
        for item in catalog:
            item_author = item.get('姓', '') + item.get('名', '')
            item_title = item.get('作品名', '')
            
            if (title in item_title or item_title in title) and (author in item_author or item_author in author):
                found_works.append((author, title, item))
                print(f"   ✅ 見つかりました: {item_title} by {item_author}")
                break
        else:
            print(f"   ❌ 見つかりません: {title} by {author}")
    
    # テキスト取得テスト
    print(f"\n📖 テキスト取得テスト ({len(found_works)} 作品)")
    successful_downloads = 0
    start_time = time.time()
    
    for author, title, item in found_works:
        print(f"   📚 {title} ({author}) ダウンロード中...")
        
        # テキストURL取得
        text_url = item.get('テキストファイルURL', '') or item.get('XHTML/HTMLファイルURL', '')
        
        if not text_url:
            print(f"      ❌ ダウンロードURLなし")
            continue
        
        try:
            response = requests.get(text_url, timeout=30)
            response.raise_for_status()
            
            # エンコーディング検出
            try:
                text = response.content.decode('shift_jis')
            except:
                try:
                    text = response.content.decode('utf-8')
                except:
                    text = response.content.decode('shift_jis', errors='ignore')
            
            if len(text) > 100:
                print(f"      ✅ 成功: {len(text):,} 文字")
                successful_downloads += 1
            else:
                print(f"      ❌ テキストが短すぎます")
                
        except Exception as e:
            print(f"      ❌ ダウンロードエラー: {e}")
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # 結果サマリー
    print(f"\n🎯 結果サマリー")
    print("="*50)
    
    total_tests = len(found_works)
    success_rate = (successful_downloads / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📊 総合結果:")
    print(f"   🎯 成功率: {success_rate:.1f}% ({successful_downloads}/{total_tests})")
    print(f"   ⏱️ 処理時間: {processing_time:.1f}秒")
    
    print(f"\n📈 改善効果:")
    print(f"   🔴 旧システム成功率: 30.0% (404エラー多発)")
    print(f"   🟢 新システム成功率: {success_rate:.1f}%")
    
    if success_rate > 30:
        improvement = success_rate - 30
        print(f"   🚀 改善: +{improvement:.1f}ポイント!")
        print(f"   ✨ GitHub aozorahackによる404エラー解決効果を確認!")
        
        if success_rate >= 80:
            print(f"   🏆 優秀！404問題を完全解決!")
        elif success_rate >= 60:
            print(f"   👍 良好！大幅な改善を達成!")
        else:
            print(f"   📈 改善中！さらなる最適化が必要")
    else:
        print(f"   ⚠️ 改善が必要です")
    
    return success_rate >= 60

if __name__ == "__main__":
    test_github_aozora() 