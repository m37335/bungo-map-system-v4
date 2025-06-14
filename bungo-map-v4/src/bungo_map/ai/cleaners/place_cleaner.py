"""
AI地名クリーナーモジュール
地名データの品質向上と正規化を行うAI機能を提供します。
"""

import os
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import openai
from rich.console import Console
from rich.progress import Progress

class PlaceCleaningResult:
    def __init__(self, original_name, cleaned_name, confidence, cleaning_type):
        self.original_name = original_name
        self.cleaned_name = cleaned_name
        self.confidence = confidence
        self.cleaning_type = cleaning_type

class CleanerConfig:
    def __init__(self, min_confidence=0.5):
        self.min_confidence = min_confidence

class PlaceCleaner:
    """AI地名クリーナークラス"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初期化
        
        Args:
            api_key: OpenAI APIキー（未指定の場合は環境変数から取得）
        """
        self.logger = logging.getLogger(__name__)
        self.console = Console()
        
        # OpenAI API設定
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.getenv("OPENAI_API_KEY")
            
        if not openai.api_key:
            raise ValueError("OpenAI APIキーが設定されていません")
    
    def clean_place_name(self, place_name: str) -> PlaceCleaningResult:
        """地名をクリーニング
        
        Args:
            place_name: クリーニング対象の地名
            
        Returns:
            PlaceCleaningResult: クリーニング結果
        """
        try:
            # OpenAI APIを使用して地名をクリーニング
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは地名クリーニングの専門家です。"},
                    {"role": "user", "content": f"以下の地名を正規化してください: {place_name}"}
                ]
            )
            
            cleaned_name = response.choices[0].message.content.strip()
            
            return PlaceCleaningResult(
                original_name=place_name,
                cleaned_name=cleaned_name,
                confidence=0.95,  # 仮の信頼度
                cleaning_type="normalization"
            )
            
        except Exception as e:
            self.logger.error(f"地名クリーニング中にエラーが発生: {str(e)}")
            raise
    
    def batch_clean_places(self, place_names: List[str]) -> List[PlaceCleaningResult]:
        """複数の地名を一括クリーニング
        
        Args:
            place_names: クリーニング対象の地名リスト
            
        Returns:
            List[PlaceCleaningResult]: クリーニング結果のリスト
        """
        results = []
        
        with Progress() as progress:
            task = progress.add_task("地名クリーニング中...", total=len(place_names))
            
            for place_name in place_names:
                try:
                    result = self.clean_place_name(place_name)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"地名 '{place_name}' のクリーニングに失敗: {str(e)}")
                    results.append(PlaceCleaningResult(
                        original_name=place_name,
                        cleaned_name=place_name,
                        confidence=0.0,
                        cleaning_type="error"
                    ))
                
                progress.update(task, advance=1)
        
        return results 