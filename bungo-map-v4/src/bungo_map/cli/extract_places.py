#!/usr/bin/env python3
"""
地名抽出スクリプト
作品から地名を抽出し、placesテーブルに登録する
"""

import os
import sys
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Set
from rich.console import Console
from rich.progress import Progress

# 地名抽出器のインポート
from bungo_map.extractors_v4.ginza_place_extractor import GinzaPlaceExtractor
from bungo_map.extractors_v4.advanced_place_extractor import AdvancedPlaceExtractor
from bungo_map.extractors_v4.improved_place_extractor import ImprovedPlaceExtractor
from bungo_map.extractors_v4.enhanced_place_extractor import EnhancedPlaceExtractor

class PlaceExtractor:
    def __init__(self, db_path: str):
        self.console = Console()
        self.db_path = db_path
        self.extractors = [
            GinzaPlaceExtractor(),
            AdvancedPlaceExtractor(),
            ImprovedPlaceExtractor(),
            EnhancedPlaceExtractor()
        ]
    
    def _get_db_connection(self) -> sqlite3.Connection:
        """データベース接続を取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def extract_places(self, work_id: int, text: str) -> List[Dict[str, Any]]:
        """作品から地名を抽出"""
        places = []
        seen_places: Set[str] = set()
        for extractor in self.extractors:
            try:
                if isinstance(extractor, GinzaPlaceExtractor):
                    extracted = extractor.extract_places_ginza(work_id, text)
                elif isinstance(extractor, AdvancedPlaceExtractor):
                    extracted = extractor.extract_places_combined(work_id, text)
                elif isinstance(extractor, ImprovedPlaceExtractor):
                    extracted = extractor.extract_places_with_deduplication(work_id, text)
                elif isinstance(extractor, EnhancedPlaceExtractor):
                    extracted = extractor.extract_places(work_id, text)
                else:
                    continue
                
                for place in extracted:
                    if place.place_name not in seen_places:
                        seen_places.add(place.place_name)
                        places.append({
                            'work_id': work_id,
                            'place_name': place.place_name,
                            'lat': None,
                            'lng': None,
                            'before_text': getattr(place, 'before_text', ''),
                            'sentence': place.sentence,
                            'after_text': getattr(place, 'after_text', ''),
                            'confidence': place.confidence,
                            'extraction_method': extractor.__class__.__name__
                        })
            except Exception as e:
                self.console.print(f"[red]❌ 抽出エラー ({extractor.__class__.__name__}): {e}[/red]")
        return places
    
    def process_works(self):
        """全作品を処理"""
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            
            # 作品一覧を取得
            cursor.execute("""
                SELECT w.work_id, w.title, a.name as author_name, w.text_url
                FROM works w
                JOIN authors a ON w.author_id = a.author_id
            """)
            works = cursor.fetchall()
            
            if not works:
                self.console.print("[yellow]⚠️ 処理対象の作品が見つかりません[/yellow]")
                return
            
            self.console.print(f"[green]📚 処理対象: {len(works)}作品[/green]")
            
            with Progress() as progress:
                task = progress.add_task("[cyan]地名抽出中...", total=len(works))
                
                for work in works:
                    try:
                        # 作品のテキストを取得
                        if not work['text_url']:
                            self.console.print(f"[yellow]⚠️ テキストURLが未設定: {work['title']}[/yellow]")
                            continue
                        
                        # テキストファイルを読み込み
                        text_path = Path(work['text_url'])
                        if not text_path.exists():
                            self.console.print(f"[yellow]⚠️ テキストファイルが見つかりません: {text_path}[/yellow]")
                            continue
                        
                        with open(text_path, 'r', encoding='utf-8') as f:
                            text = f.read()
                        
                        # 地名を抽出
                        places = self.extract_places(work['work_id'], text)
                        
                        # 抽出した地名をデータベースに登録
                        for place in places:
                            cursor.execute("""
                                INSERT INTO places (
                                    work_id, place_name, lat, lng,
                                    before_text, sentence, after_text,
                                    confidence, extraction_method
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                place['work_id'], place['place_name'],
                                place['lat'], place['lng'],
                                place['before_text'], place['sentence'],
                                place['after_text'], place['confidence'],
                                place['extraction_method']
                            ))
                        
                        conn.commit()
                        self.console.print(f"[green]✅ {work['title']}: {len(places)}件の地名を抽出[/green]")
                        
                    except Exception as e:
                        self.console.print(f"[red]❌ 処理エラー ({work['title']}): {e}[/red]")
                    
                    progress.update(task, advance=1)
            
            # 統計情報を表示
            cursor.execute("SELECT COUNT(*) FROM places")
            total_places = cursor.fetchone()[0]
            self.console.print(f"\n[green]📊 合計: {total_places}件の地名を抽出[/green]")
            
        finally:
            conn.close()

def main():
    # データベースパスを環境変数から取得
    db_path = os.getenv('BUNGO_DB_PATH', 'data/databases/bungo_v4.db')
    
    extractor = PlaceExtractor(db_path)
    extractor.process_works()

if __name__ == '__main__':
    main() 