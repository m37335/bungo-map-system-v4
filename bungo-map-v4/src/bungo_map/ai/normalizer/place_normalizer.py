#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地名正規化システム
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import openai
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()

@dataclass
class NormalizerConfig:
    """正規化設定"""
    api_key: str
    model: str = 'gpt-3.5-turbo'
    temperature: float = 0.0
    max_tokens: int = 100
    retry_count: int = 3
    retry_delay: float = 1.0
    batch_size: int = 10

class PlaceNormalizer:
    """地名正規化クラス"""
    
    def __init__(self, config: NormalizerConfig):
        """初期化"""
        self.config = config
        openai.api_key = config.api_key
        self.stats = {
            'total_places': 0,
            'normalized': 0,
            'failed': 0,
            'skipped': 0,
            'api_calls': 0
        }
        logger.info("🔄 Place Normalizer v4 初期化完了")
    
    def normalize_places(self, places: List[Dict]) -> List[Dict]:
        """地名データの正規化を実行"""
        self.stats = {
            'total_places': len(places),
            'normalized': 0,
            'failed': 0,
            'skipped': 0,
            'api_calls': 0
        }
        
        # バッチ処理用に分割
        batches = [places[i:i + self.config.batch_size] 
                  for i in range(0, len(places), self.config.batch_size)]
        
        normalized_places = []
        with Progress() as progress:
            task = progress.add_task("[cyan]正規化中...", total=len(places))
            
            for batch in batches:
                batch_results = self._normalize_batch(batch)
                normalized_places.extend(batch_results)
                progress.update(task, advance=len(batch))
        
        return normalized_places
    
    def _normalize_batch(self, places: List[Dict]) -> List[Dict]:
        """バッチ単位で正規化を実行"""
        results = []
        
        for place in places:
            # 正規化実行
            try:
                normalized = self._normalize_place(place)
                if normalized:
                    results.append(normalized)
                    self.stats['normalized'] += 1
                else:
                    results.append(place)
                    self.stats['failed'] += 1
            except Exception as e:
                logger.error(f"正規化エラー: {str(e)}")
                results.append(place)
                self.stats['failed'] += 1
        
        return results
    
    def _normalize_place(self, place: Dict) -> Optional[Dict]:
        """個別の地名を正規化"""
        name = place.get('name', '')
        if not name:
            return None
        
        # OpenAI APIを使用して正規化
        for attempt in range(self.config.retry_count):
            try:
                self.stats['api_calls'] += 1
                response = openai.ChatCompletion.create(
                    model=self.config.model or 'gpt-3.5-turbo',
                    messages=[
                        {
                            'role': 'system',
                            'content': 'あなたは地名の正規化を担当するAIアシスタントです。'
                                     '入力された地名を、日本の標準的な表記に正規化してください。'
                                     '例えば、「東京都」と「東京」は同じ場所を指す場合、'
                                     'より一般的な「東京」に正規化します。'
                        },
                        {
                            'role': 'user',
                            'content': f'以下の地名を正規化してください：{name}'
                        }
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                
                normalized_name = response.choices[0].message.content.strip()
                if normalized_name:
                    normalized = place.copy()
                    normalized.update({
                        'name': normalized_name,
                        'original_name': name,
                        'normalization_confidence': 0.9  # GPT-3.5の結果は高信頼
                    })
                    return normalized
                
                return None
            
            except Exception as e:
                if attempt < self.config.retry_count - 1:
                    time.sleep(self.config.retry_delay)
                else:
                    raise e
    
    def get_stats(self) -> Dict:
        """正規化統計を取得"""
        return self.stats
    
    def display_stats(self) -> None:
        """正規化統計を表示"""
        console.print("\n[bold blue]地名正規化統計[/bold blue]")
        
        table = Table(title="正規化結果")
        table.add_column("項目", style="cyan")
        table.add_column("件数", justify="right", style="green")
        table.add_column("割合", justify="right", style="green")
        
        total = self.stats['total_places']
        if total > 0:
            table.add_row(
                "総地名数",
                str(total),
                "100%"
            )
            table.add_row(
                "正規化成功",
                str(self.stats['normalized']),
                f"{(self.stats['normalized'] / total) * 100:.1f}%"
            )
            table.add_row(
                "正規化失敗",
                str(self.stats['failed']),
                f"{(self.stats['failed'] / total) * 100:.1f}%"
            )
            table.add_row(
                "スキップ",
                str(self.stats['skipped']),
                f"{(self.stats['skipped'] / total) * 100:.1f}%"
            )
            table.add_row(
                "API呼び出し回数",
                str(self.stats['api_calls']),
                "-"
            )
        
        console.print(table) 