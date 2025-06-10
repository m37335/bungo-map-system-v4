#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 最新統合システムによる全作品地名抽出
AI複合地名抽出を含む高精度抽出システム
"""

import click
import logging
import time
import sqlite3
from typing import List, Dict
from bungo_map.core.database import Database
from bungo_map.extractors.simple_place_extractor import SimplePlaceExtractor
from bungo_map.ai.extractors.precise_compound_extractor import PreciseCompoundExtractor

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.command()
@click.option('--with-ai', is_flag=True, help='AI複合地名抽出を有効化')
@click.option('--limit', type=int, help='処理作品数の制限（テスト用）')
@click.option('--offset', type=int, default=0, help='開始位置')
@click.option('--batch-size', type=int, default=10, help='バッチサイズ')
def full_extraction(with_ai: bool, limit: int, offset: int, batch_size: int):
    """最新統合システムによる全作品地名抽出"""
    
    click.echo("🚀 最新統合システムによる地名抽出開始")
    click.echo(f"AI複合地名抽出: {'有効' if with_ai else '無効'}")
    click.echo(f"バッチサイズ: {batch_size}")
    if limit:
        click.echo(f"制限: {limit}作品")
    click.echo("-" * 60)
    
    # データベース接続
    db = Database('data/bungo_production.db')
    
    # 抽出器の初期化
    regex_extractor = SimplePlaceExtractor()
    ai_extractor = PreciseCompoundExtractor() if with_ai else None
    
    if with_ai and ai_extractor:
        click.echo("✅ AI複合地名抽出器初期化完了")
    else:
        click.echo("📋 Regex抽出器のみ使用")
    
    # コンテンツ付き作品を取得
    works_query = """
        SELECT work_id, title, content, aozora_url
        FROM works 
        WHERE content IS NOT NULL 
        ORDER BY work_id
    """
    
    if limit:
        works_query += f" LIMIT {limit} OFFSET {offset}"
    
    with db.get_connection() as conn:
        cursor = conn.execute(works_query)
        works = cursor.fetchall()
    
    total_works = len(works)
    click.echo(f"📚 処理対象: {total_works}作品")
    
    # 統計情報
    stats = {
        'total_works': total_works,
        'processed': 0,
        'total_places': 0,
        'regex_places': 0,
        'ai_places': 0,
        'errors': 0,
        'start_time': time.time()
    }
    
    # バッチ処理
    for i in range(0, total_works, batch_size):
        batch = works[i:i + batch_size]
        click.echo(f"\n📦 バッチ {i//batch_size + 1}/{(total_works + batch_size - 1)//batch_size} 処理中...")
        
        for work in batch:
            work_id, title, content, aozora_url = work
            
            try:
                click.echo(f"  📖 処理中: {title[:50]}...")
                
                # Phase 1: Regex抽出
                regex_places = regex_extractor.extract_places_from_text(
                    work_id, content, aozora_url
                )
                
                # Phase 2: AI複合地名抽出（有効な場合）
                ai_places = []
                if with_ai and ai_extractor:
                    ai_places = ai_extractor.extract_precise_places(
                        work_id, content, aozora_url
                    )
                
                # 重複排除と統合
                all_places = regex_places + ai_places
                deduplicated_places = deduplicate_places(all_places)
                
                # データベースに保存
                with db.get_connection() as conn:
                    for place in deduplicated_places:
                        conn.execute("""
                            INSERT INTO places (
                                work_id, place_name, before_text, sentence, after_text,
                                aozora_url, confidence, extraction_method
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            place.work_id, place.place_name, place.before_text,
                            place.sentence, place.after_text, place.aozora_url,
                            place.confidence, place.extraction_method
                        ))
                    conn.commit()
                
                # 統計更新
                stats['processed'] += 1
                stats['total_places'] += len(deduplicated_places)
                stats['regex_places'] += len(regex_places)
                stats['ai_places'] += len(ai_places)
                
                click.echo(f"    ✅ {len(deduplicated_places)}件抽出 (Regex:{len(regex_places)}, AI:{len(ai_places)})")
                
            except Exception as e:
                stats['errors'] += 1
                click.echo(f"    ❌ エラー: {e}")
                logger.error(f"作品 {work_id} でエラー: {e}")
        
        # バッチ終了時の進捗表示
        progress = (stats['processed'] / total_works) * 100
        elapsed = time.time() - stats['start_time']
        click.echo(f"  📊 進捗: {stats['processed']}/{total_works} ({progress:.1f}%) - {elapsed:.1f}秒経過")
    
    # 最終結果
    total_time = time.time() - stats['start_time']
    click.echo("\n" + "=" * 60)
    click.echo("🎉 抽出完了！")
    click.echo(f"📊 最終統計:")
    click.echo(f"  処理作品: {stats['processed']}/{stats['total_works']}")
    click.echo(f"  総抽出地名: {stats['total_places']}件")
    click.echo(f"  Regex抽出: {stats['regex_places']}件")
    if with_ai:
        click.echo(f"  AI複合地名: {stats['ai_places']}件")
    click.echo(f"  エラー: {stats['errors']}件")
    click.echo(f"  処理時間: {total_time:.1f}秒")
    click.echo(f"  平均速度: {stats['total_places']/total_time:.1f}件/秒")

def deduplicate_places(places: List) -> List:
    """複数抽出器の結果を統合・重複排除"""
    if not places:
        return []
    
    # 作品内の文レベルで重複排除
    by_sentence = {}
    for place in places:
        sentence_key = (place.work_id, place.sentence)
        if sentence_key not in by_sentence:
            by_sentence[sentence_key] = []
        by_sentence[sentence_key].append(place)
    
    deduplicated = []
    
    for sentence_key, sentence_places in by_sentence.items():
        if len(sentence_places) == 1:
            deduplicated.extend(sentence_places)
            continue
        
        # 優先度: AI複合地名 > 長い地名 > 高信頼度
        sorted_places = sorted(sentence_places, key=lambda p: (
            -1 if 'precise_compound' in p.extraction_method else 0,  # AI複合地名を最優先
            -len(p.place_name),  # 長い地名を優先
            -p.confidence        # 高信頼度を優先
        ))
        
        selected = []
        for place in sorted_places:
            # 包含関係をチェック
            is_contained = any(
                place.place_name in selected_place.place_name and 
                place.place_name != selected_place.place_name
                for selected_place in selected
            )
            
            if not is_contained:
                # 現在の地名が既存を包含するかチェック
                to_remove = [
                    i for i, selected_place in enumerate(selected)
                    if (selected_place.place_name in place.place_name and
                        selected_place.place_name != place.place_name)
                ]
                
                # 包含される地名を削除
                for i in reversed(to_remove):
                    selected.pop(i)
                
                selected.append(place)
        
        deduplicated.extend(selected)
    
    return deduplicated

if __name__ == '__main__':
    full_extraction() 