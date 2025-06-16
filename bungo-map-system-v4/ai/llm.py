from typing import Dict, List, Optional, Any
import openai
from openai import OpenAI
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMManager:
    """LLM（大規模言語モデル）管理クラス"""
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.prompt_templates = self._load_prompt_templates()

    def _load_prompt_templates(self) -> Dict[str, str]:
        """プロンプトテンプレートの読み込み"""
        return {
            "place_extraction": """
            以下の文章から地名を抽出してください。
            出力は以下のJSON形式で返してください：
            {
                "places": [
                    {
                        "name": "地名",
                        "context": "前後の文脈",
                        "confidence": 0.0-1.0の信頼度
                    }
                ]
            }
            
            文章：
            {text}
            """,
            
            "place_context": """
            以下の地名について、文豪作品での文脈を分析してください。
            出力は以下のJSON形式で返してください：
            {
                "analysis": {
                    "historical_context": "歴史的文脈",
                    "literary_significance": "文学的な意味",
                    "confidence": 0.0-1.0の信頼度
                }
            }
            
            地名：{place_name}
            作品：{work_title}
            作者：{author_name}
            """
        }

    async def extract_places(self, text: str) -> List[Dict[str, Any]]:
        """文章から地名を抽出"""
        try:
            prompt = self.prompt_templates["place_extraction"].format(text=text)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "あなたは文豪作品の地名抽出の専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("places", [])
            
        except Exception as e:
            logger.error(f"地名抽出エラー: {str(e)}")
            return []

    async def analyze_place_context(
        self,
        place_name: str,
        work_title: str,
        author_name: str
    ) -> Optional[Dict[str, Any]]:
        """地名の文脈分析"""
        try:
            prompt = self.prompt_templates["place_context"].format(
                place_name=place_name,
                work_title=work_title,
                author_name=author_name
            )
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "あなたは文豪作品の文脈分析の専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("analysis")
            
        except Exception as e:
            logger.error(f"文脈分析エラー: {str(e)}")
            return None

    def calculate_confidence(
        self,
        extracted_places: List[Dict[str, Any]],
        context_analysis: Optional[Dict[str, Any]]
    ) -> float:
        """信頼度スコアの計算"""
        if not extracted_places:
            return 0.0
            
        # 地名抽出の信頼度
        extraction_confidence = sum(
            place.get("confidence", 0.0) for place in extracted_places
        ) / len(extracted_places)
        
        # 文脈分析の信頼度
        context_confidence = context_analysis.get("confidence", 0.0) if context_analysis else 0.0
        
        # 総合信頼度（抽出:文脈 = 7:3）
        return (extraction_confidence * 0.7) + (context_confidence * 0.3)
