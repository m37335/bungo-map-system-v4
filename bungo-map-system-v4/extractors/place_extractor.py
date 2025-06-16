from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass
from ..ai.llm import LLMManager
from ..ai.nlp import NLPManager, NLPResult

logger = logging.getLogger(__name__)

@dataclass
class ExtractedPlace:
    """抽出された地名情報"""
    name: str
    context: str
    confidence: float
    source: str
    metadata: Dict[str, Any]

class PlaceExtractor:
    """地名抽出エンジン"""
    
    def __init__(self):
        self.llm_manager = LLMManager()
        self.nlp_manager = NLPManager()
        
        # 抽出レベルとその信頼度閾値
        self.extraction_levels = {
            "llm_context": 0.8,  # LLM文脈理解
            "famous_place": 0.7,  # 有名地名
            "city": 0.6,         # 市区町村
            "prefecture": 0.5,   # 都道府県
            "district": 0.4      # 郡
        }

    async def extract_places(
        self,
        text: str,
        work_title: str,
        author_name: str
    ) -> List[ExtractedPlace]:
        """地名の抽出"""
        try:
            # 1. NLPによる基本的な地名抽出
            nlp_result = self.nlp_manager.analyze_text(text)
            nlp_places = self._process_nlp_entities(nlp_result)
            
            # 2. LLMによる文脈理解と地名抽出
            llm_places = await self.llm_manager.extract_places(text)
            
            # 3. 地名の統合と重複除去
            merged_places = self._merge_places(nlp_places, llm_places)
            
            # 4. 文脈分析の追加
            places_with_context = await self._add_context_analysis(
                merged_places,
                work_title,
                author_name
            )
            
            return places_with_context
            
        except Exception as e:
            logger.error(f"地名抽出エラー: {str(e)}")
            return []

    def _process_nlp_entities(self, nlp_result: NLPResult) -> List[Dict[str, Any]]:
        """NLPエンティティの処理"""
        places = []
        for entity in nlp_result.entities:
            if entity["label"] in ["地名", "国・地域"]:
                places.append({
                    "name": entity["text"],
                    "context": nlp_result.text[
                        max(0, entity["start"] - 20):
                        min(len(nlp_result.text), entity["end"] + 20)
                    ],
                    "confidence": entity["confidence"],
                    "source": "nlp"
                })
        return places

    def _merge_places(
        self,
        nlp_places: List[Dict[str, Any]],
        llm_places: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """地名の統合と重複除去"""
        merged = {}
        
        # NLPの結果を追加
        for place in nlp_places:
            merged[place["name"]] = place
        
        # LLMの結果を追加または更新
        for place in llm_places:
            if place["name"] in merged:
                # 既存の地名の場合、信頼度の高い方を採用
                if place["confidence"] > merged[place["name"]]["confidence"]:
                    merged[place["name"]] = {
                        **place,
                        "source": "llm+nlp"
                    }
            else:
                merged[place["name"]] = {
                    **place,
                    "source": "llm"
                }
        
        return list(merged.values())

    async def _add_context_analysis(
        self,
        places: List[Dict[str, Any]],
        work_title: str,
        author_name: str
    ) -> List[ExtractedPlace]:
        """文脈分析の追加"""
        result = []
        
        for place in places:
            # 文脈分析の取得
            context_analysis = await self.llm_manager.analyze_place_context(
                place["name"],
                work_title,
                author_name
            )
            
            # 総合信頼度の計算
            confidence = self.llm_manager.calculate_confidence(
                [place],
                context_analysis
            )
            
            # 抽出レベルに基づく信頼度の調整
            level = self._determine_extraction_level(place["name"])
            confidence *= self.extraction_levels[level]
            
            result.append(ExtractedPlace(
                name=place["name"],
                context=place["context"],
                confidence=confidence,
                source=place["source"],
                metadata={
                    "extraction_level": level,
                    "context_analysis": context_analysis
                }
            ))
        
        return result

    def _determine_extraction_level(self, place_name: str) -> str:
        """抽出レベルの判定"""
        # 都道府県の判定
        if place_name.endswith(("都", "道", "府", "県")):
            return "prefecture"
            
        # 市区町村の判定
        if place_name.endswith(("市", "区", "町", "村")):
            return "city"
            
        # 郡の判定
        if place_name.endswith("郡"):
            return "district"
            
        # 有名地名の判定（簡易的な実装）
        famous_places = {"東京", "京都", "大阪", "名古屋", "横浜"}
        if place_name in famous_places:
            return "famous_place"
            
        # デフォルトはLLM文脈理解
        return "llm_context"
