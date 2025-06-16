"""
AI地名クリーナーモジュール
地名データの品質向上と正規化を行うAI機能を提供します。
"""

import os
import logging
from typing import List, Dict, Optional, Any
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
    
    def __init__(self, api_key: Optional[str] = None, db: Optional[object] = None):
        """初期化
        
        Args:
            api_key: OpenAI APIキー（未指定の場合は環境変数から取得）
            db: データベース接続オブジェクト
        """
        self.logger = logging.getLogger(__name__)
        self.console = Console()
        self.db = db
        
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

    def analyze_all_places(self) -> Dict[str, Any]:
        """全地名データの分析を実行
        
        Returns:
            Dict[str, Any]: 分析結果
        """
        if not self.db:
            raise ValueError("データベース接続が設定されていません")
        
        places = self.db.get_all_places()
        analysis = {
            'total_places': len(places),
            'confidence_stats': self._analyze_confidence(places),
            'category_distribution': self._analyze_categories(places),
            'quality_score': self._calculate_quality_score(places),
            'recommendations': []
        }
        
        return analysis

    def apply_normalizations(self, normalizations: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """正規化ルールを適用
        
        Args:
            normalizations: 正規化ルールのリスト
            
        Returns:
            List[Dict[str, Any]]: 正規化結果のリスト
        """
        results = []
        
        for norm in normalizations:
            try:
                before = norm['before']
                after = norm['after']
                
                # データベース内の地名を更新
                if self.db:
                    self.db.update_place_name(before, after)
                
                results.append({
                    'before': before,
                    'after': after,
                    'success': True
                })
                
            except Exception as e:
                self.logger.error(f"正規化適用中にエラーが発生: {str(e)}")
                results.append({
                    'before': norm['before'],
                    'after': norm['after'],
                    'success': False,
                    'error': str(e)
                })
        
        return results

    def generate_cleaning_report(self) -> Dict[str, Any]:
        """クリーニングレポートを生成
        
        Returns:
            Dict[str, Any]: レポート内容
        """
        if not self.db:
            raise ValueError("データベース接続が設定されていません")
        
        places = self.db.get_all_places()
        
        report = {
            'total_places': len(places),
            'cleaned_places': len([p for p in places if p.get('cleaned_name')]),
            'confidence_stats': self._analyze_confidence(places),
            'category_distribution': self._analyze_categories(places),
            'quality_score': self._calculate_quality_score(places),
            'recommendations': self._generate_recommendations(places)
        }
        
        return report

    def _analyze_confidence(self, places: List[Dict]) -> Dict[str, float]:
        """信頼度統計分析"""
        confidences = [p.get('confidence', 0.0) for p in places]
        
        if not confidences:
            return {'avg': 0.0, 'min': 0.0, 'max': 0.0}
        
        return {
            'avg': sum(confidences) / len(confidences),
            'min': min(confidences),
            'max': max(confidences),
            'high_confidence': len([c for c in confidences if c > 0.8]),
            'low_confidence': len([c for c in confidences if c < 0.5])
        }

    def _analyze_categories(self, places: List[Dict]) -> Dict[str, int]:
        """カテゴリー分布分析"""
        categories = {}
        for place in places:
            category = place.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
        return categories

    def _calculate_quality_score(self, places: List[Dict]) -> float:
        """データ品質スコア計算"""
        if not places:
            return 0.0
        
        # 信頼度平均
        avg_confidence = sum(p.get('confidence', 0.0) for p in places) / len(places)
        
        # カテゴリー情報の完全性
        categorized = len([p for p in places if p.get('category')])
        category_completeness = categorized / len(places)
        
        # 総合スコア
        quality_score = (avg_confidence * 0.6) + (category_completeness * 0.4)
        
        return round(quality_score, 3)

    def _generate_recommendations(self, places: List[Dict]) -> List[str]:
        """改善推奨事項生成"""
        recommendations = []
        
        # 信頼度分析
        confidence_stats = self._analyze_confidence(places)
        if confidence_stats['low_confidence'] > 0:
            recommendations.append(f"低信頼度地名 {confidence_stats['low_confidence']}件の確認を推奨")
        
        # 品質スコア分析
        quality_score = self._calculate_quality_score(places)
        if quality_score < 0.7:
            recommendations.append("データ品質向上のため、追加検証を推奨")
        
        # カテゴリー分析
        categories = self._analyze_categories(places)
        unknown_count = categories.get('unknown', 0)
        if unknown_count > 0:
            recommendations.append(f"未分類地名 {unknown_count}件のカテゴリー設定を推奨")
        
        return recommendations 