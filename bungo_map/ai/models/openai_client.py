"""
OpenAI GPT-3.5 クライアント
地名データクリーニング専用の設定とプロンプト
"""

import os
import json
import time
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import openai
from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class PlaceAnalysis:
    """地名分析結果"""
    place_name: str
    is_valid: bool
    confidence: float
    normalized_name: str
    place_type: str
    suggestions: List[str]
    reasoning: str

class OpenAIClient:
    """GPT-3.5を使用した地名データクリーニングクライアント"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: OpenAI APIキー。Noneの場合は環境変数から取得
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI APIキーが設定されていません。環境変数OPENAI_API_KEYを設定してください。")
        
        openai.api_key = self.api_key
        self.model = "gpt-3.5-turbo"
        self.max_retries = 3
        self.retry_delay = 1.0
        
    def analyze_place_name(self, place_name: str, context: str = "", work_title: str = "", author: str = "") -> PlaceAnalysis:
        """
        地名を分析して品質を判定
        
        Args:
            place_name: 分析対象の地名
            context: 地名が出現する文脈
            work_title: 作品タイトル
            author: 作者名
            
        Returns:
            PlaceAnalysis: 分析結果
        """
        prompt = self._create_analysis_prompt(place_name, context, work_title, author)
        
        try:
            response = self._call_openai_with_retry(prompt)
            return self._parse_analysis_response(place_name, response)
        except Exception as e:
            logger.error(f"地名分析エラー: {place_name}, {str(e)}")
            return PlaceAnalysis(
                place_name=place_name,
                is_valid=False,
                confidence=0.0,
                normalized_name=place_name,
                place_type="unknown",
                suggestions=[],
                reasoning=f"分析エラー: {str(e)}"
            )
    
    def batch_analyze_places(self, places: List[Dict], batch_size: int = 10) -> List[PlaceAnalysis]:
        """
        複数の地名を一括分析
        
        Args:
            places: 地名リスト（辞書形式：name, context, work_title, author）
            batch_size: バッチサイズ
            
        Returns:
            List[PlaceAnalysis]: 分析結果リスト
        """
        results = []
        total = len(places)
        
        logger.info(f"地名一括分析開始: {total}件")
        
        for i in range(0, total, batch_size):
            batch = places[i:i + batch_size]
            batch_results = []
            
            for place_data in batch:
                result = self.analyze_place_name(
                    place_name=place_data.get('name', ''),
                    context=place_data.get('context', ''),
                    work_title=place_data.get('work_title', ''),
                    author=place_data.get('author', '')
                )
                batch_results.append(result)
                
                # レート制限対策
                time.sleep(0.1)
            
            results.extend(batch_results)
            logger.info(f"進捗: {min(i + batch_size, total)}/{total} 完了")
        
        return results
    
    def suggest_normalization(self, place_names: List[str]) -> Dict[str, str]:
        """
        地名の正規化提案
        
        Args:
            place_names: 正規化対象の地名リスト
            
        Returns:
            Dict[str, str]: 元地名 -> 正規化後地名のマッピング
        """
        prompt = f"""
以下の地名リストを分析し、表記ゆれを統一した正規化案を提案してください。

地名リスト:
{json.dumps(place_names, ensure_ascii=False, indent=2)}

以下の形式でJSONで回答してください：
{{
  "normalizations": {{
    "元の地名": "正規化後の地名",
    ...
  }},
  "reasoning": "正規化の理由"
}}

正規化ルール：
1. 漢字表記を優先
2. 現在の正式な地名に統一
3. 「市」「町」「村」などの行政区分を適切に付与
4. 同一地点の異なる表記を統合
"""
        
        try:
            response = self._call_openai_with_retry(prompt)
            result = json.loads(response)
            return result.get('normalizations', {})
        except Exception as e:
            logger.error(f"正規化提案エラー: {str(e)}")
            return {}
    
    def _create_analysis_prompt(self, place_name: str, context: str, work_title: str, author: str) -> str:
        """地名分析用のプロンプトを作成"""
        return f"""
以下の地名を分析し、その妥当性と品質を評価してください。

地名: {place_name}
文脈: {context}
作品: {work_title}
作者: {author}

以下の観点で分析してください：
1. 実在する地名か（実在/架空/不明）
2. 表記が適切か
3. 作品の時代背景と整合するか
4. 正規化が必要か

以下のJSON形式で回答してください：
{{
  "is_valid": true/false,
  "confidence": 0.0-1.0,
  "normalized_name": "正規化後の地名",
  "place_type": "city/town/district/landmark/nature/fictional/other",
  "suggestions": ["改善提案1", "改善提案2"],
  "reasoning": "判定理由の詳細説明"
}}

日本の文学作品における地名の特徴を考慮して分析してください。
"""
    
    def _call_openai_with_retry(self, prompt: str) -> str:
        """リトライ機能付きOpenAI API呼び出し"""
        for attempt in range(self.max_retries):
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "あなたは日本の地名と文学に詳しい専門家です。地名の妥当性を正確に判定してください。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.1,
                    timeout=30
                )
                return response.choices[0].message.content.strip()
            
            except openai.error.RateLimitError:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"レート制限に達しました。{wait_time}秒待機します...")
                    time.sleep(wait_time)
                else:
                    raise
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"API呼び出しエラー (試行 {attempt + 1}): {str(e)}")
                    time.sleep(self.retry_delay)
                else:
                    raise
    
    def _parse_analysis_response(self, place_name: str, response: str) -> PlaceAnalysis:
        """GPT-3.5の応答を解析してPlaceAnalysisオブジェクトに変換"""
        try:
            # JSONの抽出を試行
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            
            data = json.loads(response_clean)
            
            return PlaceAnalysis(
                place_name=place_name,
                is_valid=data.get('is_valid', False),
                confidence=float(data.get('confidence', 0.0)),
                normalized_name=data.get('normalized_name', place_name),
                place_type=data.get('place_type', 'unknown'),
                suggestions=data.get('suggestions', []),
                reasoning=data.get('reasoning', '')
            )
        
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"応答解析エラー: {str(e)}, 応答: {response}")
            # フォールバック：基本的な分析結果を返す
            return PlaceAnalysis(
                place_name=place_name,
                is_valid=True,  # デフォルトは有効として扱う
                confidence=0.5,
                normalized_name=place_name,
                place_type='unknown',
                suggestions=[],
                reasoning=f"応答解析エラーのため基本判定: {str(e)}"
            ) 