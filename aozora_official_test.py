#!/usr/bin/env python3
"""
青空文庫公式カタログ使用 - 404エラー解決テスト
成功率30%問題を解決
"""

import requests
import zipfile
import io
import csv
import time

def test_aozora_official():
    print('🚀 青空文庫公式カタログ 404エラー解決テスト')
    print('='*60)
    
    # 青空文庫公式カタログZIP
    catalog_url = 'https://www.aozora.gr.jp/index_pages/list_person_all_extended_utf8.zip'
    
    print('📚 カタログZIP取得中...')
    try:
        response = requests.get(catalog_url, timeout=30)
        response.raise_for_status()
        
        # ZIPファイルを解凍
        zip_data = zipfile.ZipFile(io.BytesIO(response.content))
        
        # CSVファイルを抽出
        csv_filename = 'list_person_all_extended_utf8.csv'
        csv_content = zip_data.read(csv_filename).decode('utf-8')
        
        # CSVパース
        catalog = list(csv.DictReader(io.StringIO(csv_content)))
        print(f'✅ カタログ取得成功: {len(catalog)} 作品')
        
        # 人気作者トップ5
        authors = {}
        for item in catalog:
            author = item.get('姓', '') + item.get('名', '')
            if author and author not in authors:
                authors[author] = 0
            if author:
                authors[author] += 1
        
        top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5]
        print('🔥 人気作者トップ5:')
        for i, (author, count) in enumerate(top_authors, 1):
            print(f'   {i}. {author}: {count} 作品')
        
    except Exception as e:
        print(f'❌ カタログ取得エラー: {e}')
        return False
    
    # テスト作品検索
    print('\n🔍 テスト作品検索')
    test_works = [
        ('夏目漱石', '坊っちゃん'),
        ('芥川龍之介', '羅生門'), 
        ('太宰治', '走れメロス')
    ]
    
    found_works = []
    for author, title in test_works:
        for item in catalog:
            item_author = item.get('姓', '') + item.get('名', '')
            item_title = item.get('作品名', '')
            
            if (title in item_title or item_title in title) and (author in item_author or item_author in author):
                found_works.append((author, title, item))
                print(f'   ✅ 見つかりました: {item_title} by {item_author}')
                print(f'      📄 テキストURL: {item.get("テキストファイルURL", "N/A")}')
                break
        else:
            print(f'   ❌ 見つかりません: {title} by {author}')
    
    # テキスト取得テスト（実際の404問題を検証）
    print(f'\n📖 テキスト取得テスト ({len(found_works)} 作品)')
    successful_downloads = 0
    start_time = time.time()
    
    for author, title, item in found_works:
        print(f'   📚 {title} ({author}) ダウンロード中...')
        
        # テキストURL取得
        text_url = item.get('テキストファイルURL', '') or item.get('XHTML/HTMLファイルURL', '')
        
        if not text_url:
            print(f'      ❌ ダウンロードURLなし')
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
                print(f'      ✅ 成功: {len(text):,} 文字')
                print(f'      📄 先頭50文字: {text[:50].replace(chr(10), " ")}...')
                successful_downloads += 1
            else:
                print(f'      ❌ テキストが短すぎます')
                
        except Exception as e:
            print(f'      ❌ ダウンロードエラー: {e}')
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # 結果サマリー
    print(f'\n🎯 結果サマリー')
    print('='*60)
    
    total_tests = len(found_works)
    success_rate = (successful_downloads / total_tests * 100) if total_tests > 0 else 0
    
    print(f'📊 総合結果:')
    print(f'   🎯 成功率: {success_rate:.1f}% ({successful_downloads}/{total_tests})')
    print(f'   ⏱️ 処理時間: {processing_time:.1f}秒')
    
    print(f'\n📈 改善効果:')
    print(f'   🔴 旧システム成功率: 30.0% (404エラー多発)')
    print(f'   🟢 新システム成功率: {success_rate:.1f}%')
    
    if success_rate > 30:
        improvement = success_rate - 30
        print(f'   🚀 改善: +{improvement:.1f}ポイント!')
        print(f'   ✨ 青空文庫公式カタログによる404エラー解決効果を確認!')
        
        if success_rate >= 80:
            print(f'   🏆 優秀！404問題を完全解決!')
        elif success_rate >= 60:
            print(f'   👍 良好！大幅な改善を達成!')
        else:
            print(f'   📈 改善中！さらなる最適化が必要')
    else:
        print(f'   ⚠️ 改善が必要です')
    
    # 30作品での拡張テスト
    print(f'\n🔥 拡張テスト: 30作品で旧システム30%成功率を検証')
    extended_works = [
        ('夏目漱石', '坊っちゃん'), ('夏目漱石', '吾輩は猫である'), ('夏目漱石', 'こころ'),
        ('芥川龍之介', '羅生門'), ('芥川龍之介', '蜘蛛の糸'), ('芥川龍之介', '鼻'),
        ('太宰治', '走れメロス'), ('太宰治', '人間失格'), ('太宰治', '津軽'),
        ('宮沢賢治', '銀河鉄道の夜'), ('宮沢賢治', '注文の多い料理店'), ('宮沢賢治', '風の又三郎'),
        ('森鴎外', '舞姫'), ('森鴎外', '高瀬舟'), ('森鴎外', '山椒大夫'),
        ('樋口一葉', 'たけくらべ'), ('樋口一葉', 'にごりえ'), ('樋口一葉', '十三夜'),
        ('島崎藤村', '破戒'), ('島崎藤村', '夜明け前'),
        ('志賀直哉', '城の崎にて'), ('志賀直哉', '小僧の神様'),
        ('川端康成', '伊豆の踊子'), ('川端康成', '雪国'),
        ('谷崎潤一郎', '細雪'), ('谷崎潤一郎', '春琴抄'),
        ('武者小路実篤', '友情'), ('有島武郎', '生れ出づる悩み'),
        ('石川啄木', '一握の砂'), ('正岡子規', '病床六尺')
    ]
    
    extended_successful = 0
    start_time = time.time()
    
    for i, (author, title) in enumerate(extended_works, 1):
        print(f'[{i:2d}/30] {title} ({author}) ', end='')
        
        # 検索
        found = False
        for item in catalog:
            item_author = item.get('姓', '') + item.get('名', '')
            item_title = item.get('作品名', '')
            
            if (title in item_title or item_title in title) and (author in item_author or item_author in author):
                text_url = item.get('テキストファイルURL', '') or item.get('XHTML/HTMLファイルURL', '')
                if text_url:
                    try:
                        response = requests.get(text_url, timeout=15)
                        response.raise_for_status()
                        text = response.content.decode('shift_jis', errors='ignore')
                        if len(text) > 100:
                            print('✅')
                            extended_successful += 1
                        else:
                            print('❌')
                    except:
                        print('💥')
                else:
                    print('🚫')
                found = True
                break
        
        if not found:
            print('❓')
    
    end_time = time.time()
    extended_time = end_time - start_time
    extended_rate = (extended_successful / 30) * 100
    
    print(f'\n🎯 30作品テスト結果:')
    print(f'   📊 成功率: {extended_rate:.1f}% ({extended_successful}/30)')
    print(f'   ⏱️ 処理時間: {extended_time:.1f}秒')
    print(f'   📈 平均時間/作品: {extended_time/30:.1f}秒')
    
    print(f'\n📊 最終比較:')
    print(f'   🔴 旧システム: 30.0% (9/30) - 404エラー多発')
    print(f'   🟢 新システム: {extended_rate:.1f}% ({extended_successful}/30)')
    
    if extended_rate > 30:
        improvement = extended_rate - 30
        print(f'   🚀 改善効果: +{improvement:.1f}ポイント!')
        
        if extended_rate >= 80:
            print(f'   🏆 優秀！青空文庫公式カタログで404問題を完全解決!')
        elif extended_rate >= 60:
            print(f'   👍 良好！大幅な改善を達成!')
        else:
            print(f'   📈 改善中！さらなる最適化が必要')
    
    return extended_rate >= 60

if __name__ == '__main__':
    test_aozora_official() 