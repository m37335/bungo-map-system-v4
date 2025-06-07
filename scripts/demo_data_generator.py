#!/usr/bin/env python3
"""
文豪地図システム - デモ用データ生成
サンプルテキストから地名を抽出してデータベースに追加
"""

import sqlite3
import re
import os
from pathlib import Path

# デモ用サンプルテキスト
DEMO_WORKS = [
    {
        "author": "森鴎外",
        "title": "舞姫",
        "text": """
        太田豊太郎は官費でベルリン大学に留学していた。
        彼はプロイセンの首都で法学を学び、ウンター・デン・リンデンを歩いた。
        故郷の東京が恋しくなることもあったが、ドイツの文化に魅力を感じていた。
        ある日、彼は劇場でエリスという美しい踊り子に出会った。
        彼女の家は貧しく、ベルリンの下町に住んでいた。
        太田はエリスと恋に落ちたが、やがて日本への帰国命令が下された。
        横浜港に到着した時、彼の心は複雑だった。
        """
    },
    {
        "author": "樋口一葉",
        "title": "たけくらべ",
        "text": """
        廻れば大門の見返り柳いと長けれど、お歯ぐろ溝に燈火うつる三階の騒ぎも手に取る如く、
        明けくれなしの車の行来にはかり知られぬ全盛をうらなひて、
        大音寺前と吉原と鋏んで其の名も高い廓の里、
        古い暖簾の下風に山の手の若旦那衆、深編み笠の角兵衛獅子、
        一ぷく買の頬冠り、物もらひなども氷る間もなく売り買ひののぞきの垣根を越えて、
        又一つ向ふの横町は正にものかく里の他界、
        住む人の生れも育ちも自づから京橋辺より文京の本郷辺までも劣り、
        """
    },
    {
        "author": "宮沢賢治",
        "title": "注文の多い料理店",
        "text": """
        二人の若い紳士が、岩手山のふもとの、奥深い山の中で道に迷いました。
        彼らは東京から来た都会の人でした。
        山は深く、イーハトーブの自然は美しくも恐ろしいものでした。
        歩いているうちに、森の中で「山猫軒」という西洋料理店を見つけました。
        店は盛岡の街からは遠く離れた場所にありました。
        一関の駅から汽車に乗って花巻を過ぎ、
        さらに北へ向かった山奥のことでした。
        """
    },
    {
        "author": "夏目漱石",
        "title": "三四郎",
        "text": """
        三四郎は熊本から東京へ出てきた。
        彼は小川三四郎という名前で、九州の田舎から上野駅に降り立った。
        東京帝国大学の学生となり、本郷のそばに下宿を構えた。
        神田の古本屋街を歩き、時には上野公園で時間を過ごした。
        銀座の賑わいは九州では見ることのできない光景だった。
        美禰子という美しい女性に心を奪われ、
        池の端あたりで彼女と出会ったのが運命的だった。
        """
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

def extract_places_from_text(text, title):
    """テキストから地名を抽出"""
    print(f"   🔍 {title} 地名抽出中...")
    
    # 詳細な地名パターン
    place_patterns = [
        # 主要都市
        r'東京|京都|大阪|名古屋|横浜|神戸|福岡|札幌|仙台|広島|熊本|鹿児島|盛岡|一関|花巻',
        # 歴史的地名
        r'江戸|平安京|鎌倉|奈良|大和|大坂|イーハトーブ|プロイセン',
        # 都道府県
        r'岩手|熊本|九州|京橋|文京|本郷|岩手山',
        # 区名・地名
        r'上野|神田|銀座|池の端|大門|吉原|大音寺前|小川|本郷',
        # 海外地名
        r'ベルリン|ドイツ|ウンター・デン・リンデン',
        # 駅・港
        r'上野駅|横浜港'
    ]
    
    places = []
    full_pattern = '|'.join(place_patterns)
    
    # 文章を句点で分割
    sentences = re.split(r'[。？！\n]', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 5:  # 短すぎる文は除外
            continue
            
        # 地名を検索
        matches = re.finditer(f'({full_pattern})', sentence)
        for match in matches:
            place_name = match.group(1)
            
            places.append({
                'place_name': place_name,
                'sentence': sentence.strip(),
                'confidence': 0.9  # デモ用高信頼度
            })
    
    # 重複除去
    unique_places = []
    seen = set()
    for place in places:
        key = (place['place_name'], place['sentence'][:30])
        if key not in seen:
            seen.add(key)
            unique_places.append(place)
    
    print(f"   ✅ {title}: {len(unique_places)}件の地名を抽出")
    return unique_places

def save_to_database(db_path, author_name, title, places):
    """データベースに保存"""
    print(f"   💾 {title} データベース保存中...")
    
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
                    (work_id, place_name, sentence, confidence, extraction_method)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    work_id,
                    place['place_name'], 
                    place['sentence'],
                    place['confidence'],
                    'demo_regex'
                ))
                if cursor.rowcount > 0:
                    added_count += 1
            except Exception as e:
                print(f"   ⚠️ 地名保存エラー ({place['place_name']}): {e}")
        
        conn.commit()
        print(f"   ✅ {title}: {added_count}件をデータベースに追加")

def show_current_stats(db_path):
    """現在のデータベース統計を表示"""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM authors")
        author_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM works")
        work_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM places")
        place_count = cursor.fetchone()[0]
        
        print(f"\n📊 現在のデータベース状況:")
        print(f"   👥 著者: {author_count}名")
        print(f"   📚 作品: {work_count}作品")
        print(f"   🗺️ 地名: {place_count}件")

def main():
    """メイン処理"""
    print("🎬 文豪地図システム - デモ用データ生成")
    print("=" * 50)
    
    db_path = find_database()
    if not db_path:
        print("❌ データベースファイルが見つかりません")
        return
    
    print(f"📁 使用データベース: {db_path}")
    
    # 処理前の統計
    show_current_stats(db_path)
    
    # 各作品を処理
    total_added = 0
    for work_info in DEMO_WORKS:
        print(f"\n📚 処理中: {work_info['author']} - {work_info['title']}")
        
        # 地名抽出
        places = extract_places_from_text(work_info['text'], work_info['title'])
        if places:
            # データベース保存
            save_to_database(db_path, work_info['author'], work_info['title'], places)
            total_added += len(places)
    
    # 処理後の統計
    show_current_stats(db_path)
    
    print(f"\n🎉 デモデータ生成完了!")
    print(f"📈 今回追加: {total_added}件")
    print(f"\n📋 確認コマンド:")
    print(f"   python3 simple_data_export.py")

if __name__ == "__main__":
    main() 