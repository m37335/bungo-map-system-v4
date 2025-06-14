#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GiNZA地名抽出システム v4 (高精度NLP基盤)
v3からの移植・改良版 - spaCy + GiNZA統合
"""

import logging
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# GiNZA/spaCyの動的インポート（オプショナル依存）
try:
    import spacy
    import ginza
    GINZA_AVAILABLE = True
    logger.info("✅ GiNZA/spaCy利用可能")
except ImportError:
    GINZA_AVAILABLE = False
    logger.warning("⚠️ GiNZA/spaCy未インストール - フォールバック機能で動作")

@dataclass
class GinzaPlace:
    """GiNZA地名データ"""
    work_id: int
    place_name: str
    sentence: str
    category: str = ""
    confidence: float = 0.0
    method: str = "ginza"
    entity_type: str = ""
    pos_tag: str = ""
    lemma: str = ""
    start_char: int = 0
    end_char: int = 0
    reading: str = ""
    aozora_url: str = ""

class GinzaPlaceExtractor:
    """GiNZA高精度地名抽出クラス v4"""
    
    def __init__(self):
        self.nlp = None
        
        # GiNZA初期化（利用可能な場合）
        if GINZA_AVAILABLE:
            try:
                self.nlp = spacy.load('ja_ginza')
                logger.info("✅ GiNZA日本語モデル初期化成功")
            except OSError:
                logger.warning("⚠️ GiNZAモデル未インストール - pip install ja-ginza で導入してください")
                self.nlp = None
        
        # フォールバック地名リスト
        self.fallback_places = self._build_fallback_places()
        
        # 地名関連エンティティタイプ
        self.place_entity_types = {
            'GPE',      # 地政学的エンティティ
            'LOC',      # 場所
            'FACILITY', # 施設
            'ORG'       # 組織（場所名を含む場合）
        }
        
        logger.info("🌟 GiNZA地名抽出システムv4初期化完了")
    
    def _build_fallback_places(self) -> Set[str]:
        """フォールバック用地名リスト"""
        return {
            # 主要都道府県・都市
            '北海道', '青森', '岩手', '宮城', '秋田', '山形', '福島',
            '茨城', '栃木', '群馬', '埼玉', '千葉', '東京', '神奈川',
            '新潟', '富山', '石川', '福井', '山梨', '長野', '岐阜',
            '静岡', '愛知', '三重', '滋賀', '京都', '大阪', '兵庫',
            '奈良', '和歌山', '鳥取', '島根', '岡山', '広島', '山口',
            '徳島', '香川', '愛媛', '高知', '福岡', '佐賀', '長崎',
            '熊本', '大分', '宮崎', '鹿児島', '沖縄',
            
            # 主要都市
            '札幌', '仙台', '横浜', '名古屋', '神戸', '広島', '福岡',
            '新宿', '渋谷', '池袋', '銀座', '浅草', '上野',
            
            # 古典地名
            '江戸', '京', '大和', '武蔵', '相模', '津軽', '陸奥'
        }
    
    def extract_places_ginza(self, work_id: int, text: str, aozora_url: str = "") -> List[GinzaPlace]:
        """GiNZAを使った高精度地名抽出（メイン機能）"""
        if not text or len(text) < 10:
            logger.warning(f"テキストが短すぎます: {len(text)}文字")
            return []
        
        places = []
        
        if self.nlp:
            places = self._extract_with_ginza(work_id, text, aozora_url)
            logger.info(f"📊 GiNZA抽出: {len(places)}件")
        else:
            # フォールバック機能
            places = self._extract_fallback(work_id, text, aozora_url)
            logger.info(f"📊 フォールバック抽出: {len(places)}件")
        
        logger.info(f"✅ GiNZA地名抽出完了: {len(places)}件")
        return places
    
    def _extract_with_ginza(self, work_id: int, text: str, aozora_url: str) -> List[GinzaPlace]:
        """GiNZAを使った実際の抽出処理"""
        places = []
        
        try:
            # テキストが長すぎる場合は分割処理
            max_length = 100000  # 100KB
            if len(text) > max_length:
                chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
                for chunk in chunks:
                    places.extend(self._process_chunk_with_ginza(work_id, chunk, aozora_url))
            else:
                places = self._process_chunk_with_ginza(work_id, text, aozora_url)
        
        except Exception as e:
            logger.error(f"❌ GiNZA抽出エラー: {e}")
        
        return places
    
    def _process_chunk_with_ginza(self, work_id: int, text: str, aozora_url: str) -> List[GinzaPlace]:
        """テキストチャンクの GiNZA 処理"""
        places = []
        
        try:
            doc = self.nlp(text)
            
            # 固有表現抽出
            for ent in doc.ents:
                if (ent.label_ in self.place_entity_types and 
                    self._is_valid_ginza_place(ent.text)):
                    
                    confidence = self._calculate_ginza_confidence(ent)
                    
                    place = GinzaPlace(
                        work_id=work_id,
                        place_name=ent.text,
                        sentence=self._get_sentence_context(doc, ent),
                        category=self._categorize_ginza_place(ent),
                        confidence=confidence,
                        entity_type=ent.label_,
                        start_char=ent.start_char,
                        end_char=ent.end_char,
                        reading=self._get_reading(ent),
                        aozora_url=aozora_url
                    )
                    places.append(place)
            
            # 追加の固有名詞チェック（地名っぽいもの）
            for token in doc:
                if (token.pos_ == 'PROPN' and 
                    len(token.text) >= 2 and
                    token.text not in [p.place_name for p in places] and
                    self._is_potential_place_name(token.text)):
                    
                    place = GinzaPlace(
                        work_id=work_id,
                        place_name=token.text,
                        sentence=self._get_token_context(doc, token),
                        category='propn_place',
                        confidence=0.65,  # 中程度の信頼度
                        pos_tag=token.pos_,
                        lemma=token.lemma_,
                        start_char=token.idx,
                        end_char=token.idx + len(token.text),
                        aozora_url=aozora_url
                    )
                    places.append(place)
        
        except Exception as e:
            logger.error(f"❌ GiNZAチャンク処理エラー: {e}")
        
        return places
    
    def _extract_fallback(self, work_id: int, text: str, aozora_url: str) -> List[GinzaPlace]:
        """フォールバック地名抽出（GiNZA未利用時）"""
        places = []
        
        try:
            for place_name in self.fallback_places:
                if place_name in text:
                    start = text.find(place_name)
                    place = GinzaPlace(
                        work_id=work_id,
                        place_name=place_name,
                        sentence=self._get_context_simple(text, place_name),
                        category='fallback_place',
                        confidence=0.80,  # フォールバック信頼度
                        method='fallback',
                        start_char=start,
                        end_char=start + len(place_name),
                        aozora_url=aozora_url
                    )
                    places.append(place)
        
        except Exception as e:
            logger.error(f"❌ フォールバック抽出エラー: {e}")
        
        return places
    
    def _is_valid_ginza_place(self, place_name: str) -> bool:
        """GiNZA地名の妥当性チェック"""
        if not place_name or len(place_name.strip()) <= 1:
            return False
        
        # 除外パターン
        exclusions = {'日', '月', '年', '時', '分', '秒', '人', '方', '間', '前', '後'}
        if place_name in exclusions:
            return False
        
        return True
    
    def _is_potential_place_name(self, text: str) -> bool:
        """地名の可能性チェック"""
        # 地名的な接尾辞パターン
        place_suffixes = ['県', '市', '区', '町', '村', '山', '川', '島', '駅', '港']
        return any(text.endswith(suffix) for suffix in place_suffixes)
    
    def _calculate_ginza_confidence(self, ent) -> float:
        """GiNZA地名の信頼度計算"""
        base_confidence = 0.70
        
        # エンティティタイプによる調整
        if ent.label_ == 'GPE':
            base_confidence += 0.20
        elif ent.label_ == 'LOC':
            base_confidence += 0.15
        elif ent.label_ == 'FACILITY':
            base_confidence += 0.10
        
        # フォールバックリストに含まれている場合
        if ent.text in self.fallback_places:
            base_confidence += 0.10
        
        return min(base_confidence, 1.0)
    
    def _categorize_ginza_place(self, ent) -> str:
        """GiNZA地名のカテゴリー分類"""
        category_map = {
            'GPE': 'geopolitical_entity',
            'LOC': 'location',
            'FACILITY': 'facility',
            'ORG': 'organization_place'
        }
        return category_map.get(ent.label_, 'unknown_place')
    
    def _get_reading(self, ent) -> str:
        """読み仮名取得（可能な場合）"""
        try:
            # GiNZAの読み情報があれば取得
            return getattr(ent, 'reading', '') or ''
        except:
            return ''
    
    def _get_sentence_context(self, doc, ent) -> str:
        """文レベルのコンテキスト取得"""
        try:
            for sent in doc.sents:
                if ent.start >= sent.start and ent.end <= sent.end:
                    return sent.text
            return ''
        except:
            return ''
    
    def _get_token_context(self, doc, token) -> str:
        """トークンレベルのコンテキスト取得"""
        try:
            for sent in doc.sents:
                if token.i >= sent.start and token.i < sent.end:
                    return sent.text
            return ''
        except:
            return ''
    
    def _get_context_simple(self, text: str, place_name: str, context_len: int = 50) -> str:
        """簡易コンテキスト取得"""
        try:
            start = text.find(place_name)
            if start == -1:
                return ""
            
            context_start = max(0, start - context_len)
            context_end = min(len(text), start + len(place_name) + context_len)
            
            return text[context_start:context_end]
        except Exception:
            return ""
    
    def test_extraction(self, test_text: str) -> Dict[str, Any]:
        """抽出機能のテスト"""
        logger.info("🧪 GiNZA Place Extractor テスト開始")
        
        places = self.extract_places_ginza(999, test_text)
        
        # 統計作成
        categories = {}
        entity_types = {}
        for place in places:
            categories[place.category] = categories.get(place.category, 0) + 1
            entity_types[place.entity_type] = entity_types.get(place.entity_type, 0) + 1
        
        return {
            'test_text_length': len(test_text),
            'total_places': len(places),
            'ginza_available': GINZA_AVAILABLE,
            'nlp_model_loaded': self.nlp is not None,
            'places': [
                {
                    'name': place.place_name,
                    'category': place.category,
                    'confidence': place.confidence,
                    'entity_type': place.entity_type,
                    'method': place.method,
                    'reading': place.reading
                }
                for place in places[:10]  # 最初の10件のみ
            ],
            'stats': {
                'categories': categories,
                'entity_types': entity_types
            },
            'success': len(places) > 0
        }

if __name__ == "__main__":
    # 包括的テスト
    extractor = GinzaPlaceExtractor()
    
    test_text = """
    昨日、東京都新宿区から神奈川県横浜市まで電車で移動しました。
    北海道の札幌市は雪が美しい街です。
    古い時代の江戸から明治の東京への変遷は興味深いものがあります。
    京都の金閣寺や奈良の東大寺を見学しました。
    富士山の頂上から見る日本の景色は格別です。
    津軽海峡を越えて本州から北海道に渡りました。
    """
    
    result = extractor.test_extraction(test_text)
    
    print("✅ GiNZA Place Extractor v4 テスト完了")
    print(f"📊 抽出地名数: {result['total_places']}")
    print(f"🔧 GiNZA利用可能: {result['ginza_available']}")
    print(f"🤖 NLPモデル読み込み済み: {result['nlp_model_loaded']}")
    
    for place in result['places']:
        print(f"🗺️ {place['name']} [{place['category']}] "
              f"({place['entity_type']}, 信頼度: {place['confidence']:.2f})")
        if place['reading']:
            print(f"    読み: {place['reading']}")
    
    print(f"\n📈 カテゴリー別統計: {result['stats']['categories']}")
    print(f"🏷️ エンティティタイプ別統計: {result['stats']['entity_types']}") 