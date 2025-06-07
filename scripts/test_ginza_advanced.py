#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌟 GiNZA高度地名抽出テスト
"""

def test_ginza_installation():
    """GiNZAのインストール状況をテスト"""
    try:
        import spacy
        import ginza
        print("✅ SpaCy・GiNZA インポート成功")
        
        # GiNZAの利用可能モデル確認
        print(f"📦 SpaCy バージョン: {spacy.__version__}")
        print(f"📦 GiNZA バージョン: {ginza.__version__}")
        
        return True
    except Exception as e:
        print(f"❌ インポートエラー: {e}")
        return False

def test_basic_ginza():
    """基本的なGiNZA動作テスト"""
    try:
        import spacy
        import ginza
        
        # 最新の推奨方法
        nlp = ginza.load()
        print("✅ GiNZA モデル読み込み成功")
        
        test_text = "東京で夏目漱石は生まれました。京都にも住んでいました。蜀川や阿修羅、帝釈天という言葉も出てきます。"
        doc = nlp(test_text)
        
        print(f"📖 解析テキスト: {test_text}")
        print("\n🗺️ 固有表現抽出結果:")
        
        places = []
        persons = []
        others = []
        
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC', 'Place']:
                places.append((ent.text, ent.label_))
            elif ent.label_ in ['PERSON', 'Person']:
                persons.append((ent.text, ent.label_))
            else:
                others.append((ent.text, ent.label_))
        
        print(f"🗺️ 地名候補: {len(places)}件")
        for place, label in places:
            print(f"  - {place} ({label})")
        
        print(f"👤 人名候補: {len(persons)}件")
        for person, label in persons:
            print(f"  - {person} ({label})")
        
        print(f"🏷️ その他固有表現: {len(others)}件")
        for other, label in others[:5]:
            print(f"  - {other} ({label})")
        
        return True
        
    except Exception as e:
        print(f"❌ GiNZA基本テストエラー: {e}")
        return False

def test_aozora_text_ginza():
    """青空文庫テキストでGiNZAテスト"""
    try:
        import spacy
        import ginza
        
        nlp = ginza.load()
        
        # 青空文庫テキストを読み込み
        with open('aozora_cache/夏目漱石_一夜.txt', 'r', encoding='utf-8') as f:
            text = f.read()[:1000]  # 最初の1000文字
        
        print(f"📖 青空文庫テキスト解析 ({len(text)}文字)")
        doc = nlp(text)
        
        places = []
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC', 'Place'] and len(ent.text) > 1:
                places.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
        
        print(f"🗺️ GiNZAで抽出された地名: {len(places)}件")
        for place in places[:10]:
            print(f"  - {place['text']} ({place['label']}) at {place['start']}-{place['end']}")
        
        return True
        
    except FileNotFoundError:
        print("❌ 青空文庫テキストファイルが見つかりません")
        return False
    except Exception as e:
        print(f"❌ 青空文庫テストエラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("🌟 GiNZA高度地名抽出テスト開始")
    
    if not test_ginza_installation():
        return
    
    if not test_basic_ginza():
        return
    
    test_aozora_text_ginza()
    
    print("\n🎉 GiNZAテスト完了")

if __name__ == "__main__":
    main() 