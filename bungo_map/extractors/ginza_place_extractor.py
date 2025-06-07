#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GiNZA NLP地名抽出器
"""

import spacy
from typing import List, Dict, Tuple
from bungo_map.core.models import Place


class GinzaPlaceExtractor:
    """GiNZAを使った高度な地名抽出器"""
    
    def __init__(self):
        try:
            self.nlp = spacy.load('ja_ginza')
            print("✅ GiNZA (ja_ginza) モデル読み込み完了")
        except OSError:
            print("⚠️ ja_ginza モデルが見つかりません。ja_core_news_smを使用します。")
            self.nlp = spacy.load('ja_core_news_sm')
            print("✅ ja_core_news_sm モデル読み込み完了")
    
    def extract_places_from_text(self, work_id: int, text: str, aozora_url: str = None) -> List[Place]:
        """テキストから地名を抽出"""
        places = []
        
        # GiNZAの制限（約49KB）を考慮してテキストを分割
        max_chars = 40000  # 安全マージンを設けて40KB
        text_chunks = self._split_text_by_size(text, max_chars)
        
        print(f"📝 テキスト分割: {len(text_chunks)}チャンク")
        
        all_sentences = []
        for chunk_idx, chunk in enumerate(text_chunks):
            try:
                doc = self.nlp(chunk)
                chunk_sentences = [sent.text.strip() for sent in doc.sents]
                all_sentences.extend(chunk_sentences)
                print(f"   チャンク{chunk_idx + 1}: {len(chunk_sentences)}文")
            except Exception as e:
                print(f"⚠️ チャンク{chunk_idx + 1}の解析エラー: {e}")
                continue
        
        print(f"📄 総文数: {len(all_sentences)}")
        sentences = all_sentences
        
        for i, sentence in enumerate(sentences):
            # 各文を解析
            sent_doc = self.nlp(sentence)
            
            # 地名候補を抽出（GiNZAのラベル）
            for ent in sent_doc.ents:
                if ent.label_ in ['Province', 'City', 'County', 'GPE', 'LOC']:  # GiNZAの地名ラベル
                    # 前後の文脈を取得
                    before_text = sentences[i-1] if i > 0 else ""
                    after_text = sentences[i+1] if i < len(sentences)-1 else ""
                    
                    # 信頼度計算（簡易版）
                    confidence = self._calculate_confidence(ent, sentence)
                    
                    place = Place(
                        work_id=work_id,
                        place_name=ent.text,
                        before_text=before_text[:500],  # 500文字に制限
                        sentence=sentence,
                        after_text=after_text[:500],   # 500文字に制限
                        aozora_url=aozora_url,
                        confidence=confidence,
                        extraction_method="ginza_nlp"
                    )
                    places.append(place)
        
        return self._deduplicate_places(places)
    
    def _calculate_confidence(self, entity, sentence: str) -> float:
        """地名の信頼度を計算（簡易版）"""
        base_confidence = 0.7
        
        # 実在地名の可能性
        known_places = [
            '東京', '京都', '大阪', '鎌倉', '松山', '津軽', 
            '北海道', '九州', '四国', '本州',
            'シラクス', 'ローマ', 'パリ', 'ロンドン'
        ]
        
        if entity.text in known_places:
            base_confidence += 0.2
        
        # 「市」「県」「町」などの接尾辞
        location_suffixes = ['市', '県', '町', '村', '区', '島', '山', '川', '海', '湖']
        if any(entity.text.endswith(suffix) for suffix in location_suffixes):
            base_confidence += 0.15
        
        # 文中での位置（文の前半の方が地名の可能性が高い）
        if sentence.find(entity.text) < len(sentence) * 0.5:
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def _deduplicate_places(self, places: List[Place]) -> List[Place]:
        """重複する地名を除去"""
        seen = set()
        unique_places = []
        
        for place in places:
            # 地名と作品IDの組み合わせで重複チェック
            key = (place.work_id, place.place_name)
            if key not in seen:
                seen.add(key)
                unique_places.append(place)
        
        return unique_places
    
    def _split_text_by_size(self, text: str, max_chars: int) -> List[str]:
        """テキストを指定サイズ以下のチャンクに分割"""
        chunks = []
        
        # 文単位で分割を試行（。！？で区切り）
        sentences = text.split('。')
        
        current_chunk = ""
        for sentence in sentences:
            # 文を追加しても制限を超えない場合
            if len(current_chunk.encode('utf-8')) + len((sentence + '。').encode('utf-8')) <= max_chars:
                current_chunk += sentence + '。'
            else:
                # 現在のチャンクを保存
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 新しいチャンクを開始
                current_chunk = sentence + '。'
                
                # 単一の文が制限を超える場合は強制分割
                if len(current_chunk.encode('utf-8')) > max_chars:
                    char_chunks = [current_chunk[i:i+max_chars//3] for i in range(0, len(current_chunk), max_chars//3)]
                    chunks.extend(char_chunks[:-1])
                    current_chunk = char_chunks[-1] if char_chunks else ""
        
        # 最後のチャンクを追加
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def extract_with_context(self, work_id: int, text: str, context_size: int = 50) -> List[Dict]:
        """より詳細な文脈付きで地名を抽出"""
        results = []
        doc = self.nlp(text)
        
        for ent in doc.ents:
            if ent.label_ in ['Province', 'City', 'County', 'GPE', 'LOC']:
                # より詳細な文脈抽出
                start_char = max(0, ent.start_char - context_size)
                end_char = min(len(text), ent.end_char + context_size)
                
                context = text[start_char:end_char]
                
                result = {
                    'place_name': ent.text,
                    'start_pos': ent.start_char,
                    'end_pos': ent.end_char,
                    'context': context,
                    'label': ent.label_,
                    'confidence': self._calculate_confidence(ent, context)
                }
                results.append(result)
        
        return results
    
    def test_extraction(self, test_texts: List[str]) -> Dict:
        """抽出機能のテスト"""
        results = {
            'total_texts': len(test_texts),
            'total_places': 0,
            'extractions': []
        }
        
        for i, text in enumerate(test_texts):
            places = self.extract_places_from_text(work_id=999, text=text)
            
            extraction = {
                'text_id': i + 1,
                'text': text[:100] + "..." if len(text) > 100 else text,
                'places_count': len(places),
                'places': [
                    {
                        'name': place.place_name,
                        'confidence': place.confidence,
                        'method': place.extraction_method
                    }
                    for place in places
                ]
            }
            
            results['extractions'].append(extraction)
            results['total_places'] += len(places)
        
        return results 