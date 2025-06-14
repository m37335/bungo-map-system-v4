#!/usr/bin/env python3
import requests
import re
import sqlite3

print("📚 夏目漱石「こころ」処理テスト")

# 1. テキストファイル取得
url = "https://www.aozora.gr.jp/cards/000148/files/773_14560.html"
response = requests.get(url, timeout=30)

# Shift_JISでデコード
content = response.content.decode('shift_jis', errors='ignore')
print(f"✅ テキスト取得: {len(content):,}文字")

# 2. 本文部分を抽出（HTMLタグ除去）
text_content = re.sub(r'<[^>]+>', '', content)
lines = text_content.split('\n')

# メタデータをスキップして本文を探す
main_lines = []
found_main = False

for line in lines:
    line = line.strip()
    if not line:
        continue
        
    # 本文開始の検出
    if ('先生と私' in line or '私はその人を' in line) and not found_main:
        found_main = True
        
    if found_main:
        # フッター検出で終了
        if any(x in line for x in ['底本：', '入力：', '校正：', 'ファイル作成']):
            break
        main_lines.append(line)

main_text = '\n'.join(main_lines)
print(f"✅ 本文抽出: {len(main_text):,}文字")

# 3. 文分割
sentences = re.split(r'[。！？]', main_text)
sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
print(f"✅ 文分割: {len(sentences)}文")

# 最初の数文を表示
if sentences:
    print(f"\n📝 最初の3文:")
    for i, sentence in enumerate(sentences[:3], 1):
        print(f"  {i}. {sentence[:80]}...")

# 4. v4データベースに追加
db_path = '/app/bungo-map-v4/data/databases/bungo_v4.db'
work_id = 1000
author_id = 1001

with sqlite3.connect(db_path) as conn:
    # 既存センテンスクリア
    conn.execute("DELETE FROM sentences WHERE work_id = ?", (work_id,))
    
    # 新しいセンテンス追加（最初の50文のみテスト）
    added = 0
    for i, sentence in enumerate(sentences[:50], 1):
        if len(sentence.strip()) < 5:
            continue
            
        before_text = sentences[i-2] if i > 1 else ""
        after_text = sentences[i] if i < len(sentences) else ""
        
        conn.execute("""
            INSERT INTO sentences (sentence_text, work_id, author_id, before_text, after_text, position_in_work)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sentence, work_id, author_id, before_text[:200], after_text[:200], i))
        added += 1
    
    conn.commit()
    print(f"✅ v4データベースに追加: {added}文")

print(f"\n🎉 「こころ」処理完了！") 