#!/usr/bin/env python3
"""
文豪地図システム - 簡単データ収集
青空文庫から新しい作品を取得してデータベースに追加
"""

import requests
import sqlite3
import re
import os
import time
from pathlib import Path
from urllib.parse import urljoin
import zipfile
import io

# 新しい作品の設定
NEW_WORKS = [
    {
        "author": "森鴎外",
        "title": "舞姫", 
        "aozora_id": "52374",  # 青空文庫ID
        "zip_url": "https://www.aozora.gr.jp/cards/000129/files/52374_zip.zip"
    },
    {
        "author": "樋口一葉",
        "title": "たけくらべ",
        "aozora_id": "2386",
        "zip_url": "https://www.aozora.gr.jp/cards/000064/files/2386_zip.zip"
    },
    {
        "author": "宮沢賢治",
        "title": "注文の多い料理店",
        "aozora_id": "1927",
        "zip_url": "https://www.aozora.gr.jp/cards/000081/files/1927_zip.zip"
    }
]

def find_database():
    """データベースファイルを検索"""
    possible_paths = [
        "bungo_project_v3/data/bungo_production.db",
        "bungo_project_v2/data/bungo_production.db", 
        "bungo_project/data/bungo_production.db"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def download_and_extract_text(zip_url, title):
    """青空文庫から作品テキストをダウンロード・抽出"""
    print(f"   📥 {title} ダウンロード中...")
    
    try:
        # キャッシュディレクトリ作成
        cache_dir = Path("aozora_cache")
        cache_dir.mkdir(exist_ok=True)
        
        # ダウンロード
        response = requests.get(zip_url, timeout=30)
        response.raise_for_status()
        
        # ZIPファイルを展開
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            # テキストファイルを探す
            txt_files = [name for name in zip_file.namelist() if name.endswith('.txt')]
            
            if not txt_files:
                print(f"   ❌ {title}: テキストファイルが見つかりません")
                return None
            
            # 最初のtxtファイルを読み込み
            with zip_file.open(txt_files[0]) as txt_file:
                # Shift-JISで読み込み（青空文庫の標準）
                try:
                    content = txt_file.read().decode('shift_jis')
                except UnicodeDecodeError:
                    try:
                        content = txt_file.read().decode('utf-8')
                    except UnicodeDecodeError:
                        content = txt_file.read().decode('utf-8', errors='ignore')
        
        # 青空文庫の注記を削除（簡単版）
        content = re.sub(r'《.*?》', '', content)  # ルビ除去
        content = re.sub(r'［＃.*?］', '', content)  # 注記除去
        content = re.sub(r'-----.*?-----', '', content, flags=re.DOTALL)  # ヘッダ除去
        
        print(f"   ✅ {title}: {len(content)}文字 取得完了")
        return content
        
    except Exception as e:
        print(f"   ❌ {title} ダウンロードエラー: {e}")
        return None

def extract_places_simple(text, title):
    """簡単な地名抽出（正規表現ベース）"""
    print(f"   🔍 {title} 地名抽出中...")
    
    # 地名パターン（一般的な地名と文学作品によく出る地名）
    place_patterns = [
        # 主要都市
        r'東京|京都|大阪|名古屋|横浜|神戸|福岡|札幌|仙台|広島|熊本|鹿児島',
        # 歴史的地名
        r'江戸|平安京|鎌倉|奈良|大和|大坂|長安|洛中|洛外',
        # 地方・県名
        r'北海道|青森|岩手|宮城|秋田|山形|福島|茨城|栃木|群馬|埼玉|千葉|東京|神奈川|新潟|富山|石川|福井|山梨|長野|岐阜|静岡|愛知|三重|滋賀|京都|大阪|兵庫|奈良|和歌山|鳥取|島根|岡山|広島|山口|徳島|香川|愛媛|高知|福岡|佐賀|長崎|熊本|大分|宮崎|鹿児島|沖縄',
        # 区名・市名（抜粋）
        r'新宿|渋谷|品川|目黒|世田谷|中野|杉並|練馬|台東|墨田|江東|荒川|足立|葛飾|江戸川|千代田|中央|港|文京|豊島|北|板橋',
        # ヨーロッパ地名（舞姫等）
        r'ベルリン|パリ|ロンドン|ウィーン|ローマ|ミュンヘン|ハンブルク|フランクフルト|ドレスデン|ライプツィヒ',
        # その他文学地名
        r'上野|浅草|銀座|丸の内|新橋|有楽町|両国|日本橋|神田|小川町|麹町|麻布|赤坂|青山|表参道'
    ]
    
    places = []
    full_pattern = '|'.join(place_patterns)
    
    # 文章を句点で分割
    sentences = re.split(r'[。？！]', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 5:  # 短すぎる文は除外
            continue
            
        # 地名を検索
        matches = re.finditer(f'({full_pattern})', sentence)
        for match in matches:
            place_name = match.group(1)
            
            # 前後の文脈を取得
            start_pos = max(0, sentence.find(place_name) - 20)
            end_pos = min(len(sentence), sentence.find(place_name) + len(place_name) + 20)
            context = sentence[start_pos:end_pos]
            
            places.append({
                'place_name': place_name,
                'sentence': sentence,
                'context': context,
                'confidence': 0.8  # 正規表現ベースの基本信頼度
            })
    
    # 重複除去（地名と文章の組み合わせ）
    unique_places = []
    seen = set()
    for place in places:
        key = (place['place_name'], place['sentence'][:50])
        if key not in seen:
            seen.add(key)
            unique_places.append(place)
    
    print(f"   ✅ {title}: {len(unique_places)}件の地名を抽出")
    return unique_places

def save_to_database(db_path, author_name, title, places, aozora_url):
    """データベースに保存"""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # 著者を追加（存在しない場合）
        cursor.execute("INSERT OR IGNORE INTO authors (name) VALUES (?)", (author_name,))
        cursor.execute("SELECT author_id FROM authors WHERE name = ?", (author_name,))
        author_id = cursor.fetchone()[0]
        
        # 作品を追加（存在しない場合）
        cursor.execute("INSERT OR IGNORE INTO works (author_id, title) VALUES (?, ?)", (author_id, title))
        cursor.execute("SELECT work_id FROM works WHERE author_id = ? AND title = ?", (author_id, title))
        work_result = cursor.fetchone()
        if work_result:
            work_id = work_result[0]
        else:
            print(f"   ❌ 作品追加エラー: {title}")
            return
        
        # 地名を追加
        added_count = 0
        for place in places:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO places 
                    (work_id, place_name, sentence, confidence, extraction_method, aozora_url)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    work_id,
                    place['place_name'], 
                    place['sentence'],
                    place['confidence'],
                    'regex_simple',
                    aozora_url
                ))
                if cursor.rowcount > 0:
                    added_count += 1
            except Exception as e:
                print(f"   ⚠️ 地名保存エラー ({place['place_name']}): {e}")
        
        conn.commit()
        print(f"   ✅ データベース保存: {added_count}件追加")

def main():
    """メイン処理"""
    print("🚀 文豪地図システム - 新規データ収集")
    print("=" * 50)
    
    db_path = find_database()
    if not db_path:
        print("❌ データベースファイルが見つかりません")
        return
    
    print(f"📁 使用データベース: {db_path}")
    
    for work_info in NEW_WORKS:
        print(f"\n📚 処理中: {work_info['author']} - {work_info['title']}")
        
        # テキストダウンロード
        text = download_and_extract_text(work_info['zip_url'], work_info['title'])
        if not text:
            continue
        
        # 地名抽出
        places = extract_places_simple(text, work_info['title'])
        if not places:
            print(f"   ⚠️ {work_info['title']}: 地名が見つかりませんでした")
            continue
        
        # データベース保存
        save_to_database(
            db_path, 
            work_info['author'], 
            work_info['title'], 
            places,
            work_info['zip_url']
        )
        
        # 短時間の待機（サーバー負荷軽減）
        time.sleep(2)
    
    print(f"\n🎉 データ収集完了!")
    print(f"新しいデータを確認するには:")
    print(f"  python3 simple_data_export.py")

if __name__ == "__main__":
    main() 