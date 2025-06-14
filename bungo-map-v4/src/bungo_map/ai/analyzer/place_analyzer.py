#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名データ品質分析システム
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

logger = logging.getLogger(__name__)
console = Console()

@dataclass
class AnalysisConfig:
    """分析設定"""
    min_confidence: float = 0.7
    min_coordinate_accuracy: float = 0.8
    enable_context_analysis: bool = True
    enable_type_analysis: bool = True
    enable_geocoding_analysis: bool = True
    enable_frequency_analysis: bool = True

class PlaceAnalyzer:
    """地名データ品質分析クラス"""
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """初期化"""
        self.config = config or AnalysisConfig()
        self.stats = {
            'total_places': 0,
            'high_confidence': 0,
            'low_confidence': 0,
            'valid_coordinates': 0,
            'invalid_coordinates': 0,
            'context_valid': 0,
            'context_invalid': 0,
            'type_distribution': {},
            'geocoding_stats': {
                'total': 0,
                'success': 0,
                'failed': 0,
                'accuracy_distribution': {}
            },
            'frequency_stats': {
                'total_unique': 0,
                'high_frequency': 0,
                'low_frequency': 0,
                'frequency_distribution': {}
            }
        }
        logger.info("🧪 Place Analyzer v4 初期化完了")
    
    def analyze_places(self, places: List[Dict]) -> Dict:
        """地名データの品質分析を実行"""
        self._reset_stats()
        
        with Progress() as progress:
            task = progress.add_task("[cyan]地名データを分析中...", total=len(places))
            
            for place in places:
                self._analyze_place(place)
                progress.update(task, advance=1)
        
        return self._generate_report()
    
    def _reset_stats(self) -> None:
        """統計情報をリセット"""
        self.stats = {
            'total_places': 0,
            'high_confidence': 0,
            'low_confidence': 0,
            'valid_coordinates': 0,
            'invalid_coordinates': 0,
            'context_valid': 0,
            'context_invalid': 0,
            'type_distribution': {},
            'geocoding_stats': {
                'total': 0,
                'success': 0,
                'failed': 0,
                'accuracy_distribution': {}
            },
            'frequency_stats': {
                'total_unique': 0,
                'high_frequency': 0,
                'low_frequency': 0,
                'frequency_distribution': {}
            }
        }
    
    def _analyze_place(self, place: Dict) -> None:
        """個別の地名データを分析"""
        self.stats['total_places'] += 1
        
        # 信頼度分析
        confidence = place.get('confidence', 0.0)
        if confidence >= self.config.min_confidence:
            self.stats['high_confidence'] += 1
        else:
            self.stats['low_confidence'] += 1
        
        # 座標検証
        if self._validate_coordinates(place):
            self.stats['valid_coordinates'] += 1
        else:
            self.stats['invalid_coordinates'] += 1
        
        # 文脈分析
        if self.config.enable_context_analysis:
            if self._analyze_context(place):
                self.stats['context_valid'] += 1
            else:
                self.stats['context_invalid'] += 1
        
        # タイプ分析
        if self.config.enable_type_analysis:
            place_type = self._analyze_place_type(place)
            self.stats['type_distribution'][place_type] = \
                self.stats['type_distribution'].get(place_type, 0) + 1
        
        # ジオコーディング分析
        if self.config.enable_geocoding_analysis:
            self._analyze_geocoding(place)
        
        # 頻度分析
        if self.config.enable_frequency_analysis:
            self._analyze_frequency(place)
    
    def _validate_coordinates(self, place: Dict) -> bool:
        """座標の妥当性を検証"""
        try:
            lat = float(place.get('latitude', 0))
            lon = float(place.get('longitude', 0))
            
            # 日本国内の座標範囲チェック
            if not (24 <= lat <= 46 and 122 <= lon <= 154):
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    def _analyze_context(self, place: Dict) -> bool:
        """文脈の妥当性を分析"""
        context = place.get('context', '')
        if not context:
            return False
        
        # 文脈の長さチェック
        if len(context) < 10:
            return False
        
        # 地名が文脈内に存在するかチェック
        name = place.get('name', '')
        if name not in context:
            return False
        
        return True
    
    def _analyze_place_type(self, place: Dict) -> str:
        """地名のタイプを分析"""
        name = place.get('name', '')
        
        if '県' in name:
            return 'prefecture'
        elif '市' in name:
            return 'city'
        elif '区' in name:
            return 'ward'
        elif '町' in name:
            return 'town'
        elif '村' in name:
            return 'village'
        elif '山' in name:
            return 'mountain'
        elif '川' in name:
            return 'river'
        elif '駅' in name:
            return 'station'
        else:
            return 'other'
    
    def _analyze_geocoding(self, place: Dict) -> None:
        """ジオコーディングの分析"""
        self.stats['geocoding_stats']['total'] += 1
        
        if 'latitude' in place and 'longitude' in place:
            self.stats['geocoding_stats']['success'] += 1
            
            # 精度分布の更新
            accuracy = place.get('geocoding_accuracy', 0.0)
            accuracy_range = round(accuracy * 10) / 10  # 0.1刻みでグループ化
            self.stats['geocoding_stats']['accuracy_distribution'][accuracy_range] = \
                self.stats['geocoding_stats']['accuracy_distribution'].get(accuracy_range, 0) + 1
        else:
            self.stats['geocoding_stats']['failed'] += 1
    
    def _analyze_frequency(self, place: Dict) -> None:
        """地名の出現頻度を分析"""
        frequency = place.get('frequency', 1)
        
        # 頻度分布の更新
        frequency_range = min(frequency // 10 * 10, 100)  # 10刻みでグループ化（最大100）
        self.stats['frequency_stats']['frequency_distribution'][frequency_range] = \
            self.stats['frequency_stats']['frequency_distribution'].get(frequency_range, 0) + 1
        
        # 高頻度/低頻度の判定
        if frequency >= 5:
            self.stats['frequency_stats']['high_frequency'] += 1
        else:
            self.stats['frequency_stats']['low_frequency'] += 1
    
    def _generate_report(self) -> Dict:
        """分析レポートを生成"""
        total = self.stats['total_places']
        if total == 0:
            return self.stats
        
        # 基本統計
        report = {
            'total_places': total,
            'confidence_stats': {
                'high_confidence': self.stats['high_confidence'],
                'low_confidence': self.stats['low_confidence'],
                'high_confidence_ratio': self.stats['high_confidence'] / total
            },
            'coordinate_stats': {
                'valid': self.stats['valid_coordinates'],
                'invalid': self.stats['invalid_coordinates'],
                'valid_ratio': self.stats['valid_coordinates'] / total
            },
            'context_stats': {
                'valid': self.stats['context_valid'],
                'invalid': self.stats['context_invalid'],
                'valid_ratio': self.stats['context_valid'] / total if self.config.enable_context_analysis else 0
            },
            'type_distribution': self.stats['type_distribution'],
            'geocoding_stats': self.stats['geocoding_stats'],
            'frequency_stats': self.stats['frequency_stats']
        }
        
        # 品質スコアの計算
        report['quality_score'] = self._calculate_quality_score(report)
        
        # 推奨事項の生成
        report['recommendations'] = self._generate_recommendations(report)
        
        return report
    
    def _calculate_quality_score(self, report: Dict) -> float:
        """品質スコアを計算"""
        weights = {
            'confidence': 0.3,
            'coordinates': 0.2,
            'context': 0.2,
            'geocoding': 0.2,
            'frequency': 0.1
        }
        
        scores = {
            'confidence': report['confidence_stats']['high_confidence_ratio'],
            'coordinates': report['coordinate_stats']['valid_ratio'],
            'context': report['context_stats']['valid_ratio'],
            'geocoding': report['geocoding_stats']['success'] / report['geocoding_stats']['total'] if report['geocoding_stats']['total'] > 0 else 0,
            'frequency': report['frequency_stats']['high_frequency'] / report['total_places']
        }
        
        return sum(score * weights[key] for key, score in scores.items())
    
    def _generate_recommendations(self, report: Dict) -> List[str]:
        """改善推奨事項を生成"""
        recommendations = []
        
        # 信頼度に関する推奨
        if report['confidence_stats']['high_confidence_ratio'] < 0.7:
            recommendations.append(
                f"信頼度の低い地名が{report['confidence_stats']['low_confidence']}件あります。"
                "地名抽出の精度向上を検討してください。"
            )
        
        # 座標に関する推奨
        if report['coordinate_stats']['valid_ratio'] < 0.8:
            recommendations.append(
                f"無効な座標が{report['coordinate_stats']['invalid']}件あります。"
                "ジオコーディングの精度向上を検討してください。"
            )
        
        # 文脈に関する推奨
        if report['context_stats']['valid_ratio'] < 0.6:
            recommendations.append(
                f"文脈が不適切な地名が{report['context_stats']['invalid']}件あります。"
                "文脈分析の精度向上を検討してください。"
            )
        
        # ジオコーディングに関する推奨
        if report['geocoding_stats']['failed'] > 0:
            recommendations.append(
                f"ジオコーディングに失敗した地名が{report['geocoding_stats']['failed']}件あります。"
                "手動での座標補完を検討してください。"
            )
        
        # 頻度に関する推奨
        if report['frequency_stats']['low_frequency'] / report['total_places'] > 0.5:
            recommendations.append(
                "低頻度の地名が多く見られます。"
                "地名の正規化や統合を検討してください。"
            )
        
        return recommendations
    
    def display_report(self, report: Dict) -> None:
        """分析レポートを表示"""
        console.print("\n[bold cyan]📊 地名データ品質分析レポート[/bold cyan]")
        
        # 基本統計
        console.print("\n[bold]基本統計[/bold]")
        console.print(f"総地名数: {report['total_places']}")
        console.print(f"品質スコア: {report['quality_score']:.1%}")
        
        # 信頼度分布
        console.print("\n[bold]信頼度分布[/bold]")
        console.print(f"高信頼度: {report['confidence_stats']['high_confidence']}件 ({report['confidence_stats']['high_confidence_ratio']:.1%})")
        console.print(f"低信頼度: {report['confidence_stats']['low_confidence']}件 ({1 - report['confidence_stats']['high_confidence_ratio']:.1%})")
        
        # 座標統計
        console.print("\n[bold]座標統計[/bold]")
        console.print(f"有効座標: {report['coordinate_stats']['valid']}件 ({report['coordinate_stats']['valid_ratio']:.1%})")
        console.print(f"無効座標: {report['coordinate_stats']['invalid']}件 ({1 - report['coordinate_stats']['valid_ratio']:.1%})")
        
        # 文脈統計
        if report['context_stats']['valid_ratio'] > 0:
            console.print("\n[bold]文脈統計[/bold]")
            console.print(f"有効文脈: {report['context_stats']['valid']}件 ({report['context_stats']['valid_ratio']:.1%})")
            console.print(f"無効文脈: {report['context_stats']['invalid']}件 ({1 - report['context_stats']['valid_ratio']:.1%})")
        
        # タイプ分布
        console.print("\n[bold]タイプ分布[/bold]")
        type_table = Table(show_header=True, header_style="bold magenta")
        type_table.add_column("タイプ")
        type_table.add_column("件数")
        type_table.add_column("割合")
        
        for type_name, count in report['type_distribution'].items():
            ratio = count / report['total_places']
            type_table.add_row(type_name, str(count), f"{ratio:.1%}")
        
        console.print(type_table)
        
        # ジオコーディング統計
        console.print("\n[bold]ジオコーディング統計[/bold]")
        console.print(f"成功: {report['geocoding_stats']['success']}件")
        console.print(f"失敗: {report['geocoding_stats']['failed']}件")
        
        # 頻度統計
        console.print("\n[bold]頻度統計[/bold]")
        console.print(f"高頻度: {report['frequency_stats']['high_frequency']}件")
        console.print(f"低頻度: {report['frequency_stats']['low_frequency']}件")
        
        # 推奨事項
        if report['recommendations']:
            console.print("\n[bold yellow]💡 改善推奨事項[/bold yellow]")
            for i, rec in enumerate(report['recommendations'], 1):
                console.print(f"{i}. {rec}") 