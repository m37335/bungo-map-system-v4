#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import MeCab

def test_mecab():
    try:
        text = open('aozora_cache/夏目漱石_一夜.txt', 'r', encoding='utf-8').read()[:500]
        print(f"📖 テキスト長: {len(text)}文字")
        
        tagger = MeCab.Tagger()
        node = tagger.parseToNode(text)
        
        places = []
        while node:
            if node.surface:
                features = node.feature.split(',')
                # 固有名詞・地名候補をチェック
                if len(features) > 1 and '名詞' in features[0]:
                    if len(node.surface) >= 2:
                        places.append((node.surface, features[0]))
            node = node.next
        
        print('✅ MeCab初期化成功')
        print(f'🗺️ 名詞候補: {len(places)}箇所')
        
        # 地名候補をフィルタ
        place_candidates = []
        for surface, pos in places[:20]:
            if any(keyword in surface for keyword in ['川', '山', '海', '京', '江', '阿', '帝', '蜀']):
                place_candidates.append(surface)
        
        print(f'🗺️ 地名候補: {len(place_candidates)}箇所')
        for place in place_candidates[:5]:
            print(f'  - {place}')
            
    except Exception as e:
        print(f"❌ MeCabエラー: {e}")

if __name__ == "__main__":
    test_mecab() 