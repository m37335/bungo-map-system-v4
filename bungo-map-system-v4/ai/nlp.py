from typing import List, Dict, Any, Optional
import spacy
import ginza
import MeCab
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NLPResult:
    """NLP処理結果"""
    text: str
    tokens: List[str]
    pos_tags: List[str]
    entities: List[Dict[str, Any]]
    confidence: float

class NLPManager:
    """NLP処理管理クラス"""
    
    def __init__(self):
        # spaCyモデルの読み込み
        self.nlp = spacy.load("ja_ginza")
        
        # MeCabの初期化
        self.mecab = MeCab.Tagger("-Owakati")
        
        # 地名カテゴリの定義
        self.place_categories = {
            "LOC": "地名",
            "GPE": "国・地域",
            "FAC": "施設",
            "ORG": "組織"
        }

    def preprocess_text(self, text: str) -> str:
        """テキストの前処理"""
        # 不要な空白の削除
        text = re.sub(r'\s+', ' ', text)
        # 特殊文字の正規化
        text = text.replace('　', ' ')
        return text.strip()

    def tokenize(self, text: str) -> List[str]:
        """MeCabによる形態素解析"""
        try:
            return self.mecab.parse(text).strip().split()
        except Exception as e:
            logger.error(f"形態素解析エラー: {str(e)}")
            return []

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """spaCyによる固有表現抽出"""
        try:
            doc = self.nlp(text)
            entities = []
            
            for ent in doc.ents:
                if ent.label_ in self.place_categories:
                    entities.append({
                        "text": ent.text,
                        "label": self.place_categories[ent.label_],
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "confidence": self._calculate_entity_confidence(ent)
                    })
            
            return entities
            
        except Exception as e:
            logger.error(f"固有表現抽出エラー: {str(e)}")
            return []

    def _calculate_entity_confidence(self, entity) -> float:
        """エンティティの信頼度計算"""
        # 基本的な信頼度
        confidence = 0.7
        
        # 長さによる補正
        if len(entity.text) >= 4:
            confidence += 0.1
            
        # カテゴリによる補正
        if entity.label_ in ["LOC", "GPE"]:
            confidence += 0.1
            
        return min(confidence, 1.0)

    def analyze_text(self, text: str) -> NLPResult:
        """テキストの総合分析"""
        # テキストの前処理
        processed_text = self.preprocess_text(text)
        
        # 形態素解析
        tokens = self.tokenize(processed_text)
        
        # 品詞タグ付け
        doc = self.nlp(processed_text)
        pos_tags = [token.pos_ for token in doc]
        
        # 固有表現抽出
        entities = self.extract_entities(processed_text)
        
        # 信頼度の計算
        confidence = self._calculate_overall_confidence(tokens, entities)
        
        return NLPResult(
            text=processed_text,
            tokens=tokens,
            pos_tags=pos_tags,
            entities=entities,
            confidence=confidence
        )

    def _calculate_overall_confidence(
        self,
        tokens: List[str],
        entities: List[Dict[str, Any]]
    ) -> float:
        """総合信頼度の計算"""
        if not tokens or not entities:
            return 0.0
            
        # トークン数による補正
        token_confidence = min(len(tokens) / 100, 1.0)
        
        # エンティティの信頼度平均
        entity_confidence = sum(
            entity["confidence"] for entity in entities
        ) / len(entities)
        
        # 総合信頼度（トークン:エンティティ = 3:7）
        return (token_confidence * 0.3) + (entity_confidence * 0.7)
