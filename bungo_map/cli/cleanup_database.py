#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧹 データベースsentenceクリーンアップ
既存のplacesテーブルのsentenceフィールドを青空文庫クリーナーでクリーンアップ
"""

import click
import logging
from bungo_map.core.database import Database
from bungo_map.utils.aozora_text_cleaner import clean_aozora_sentence

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option('--batch-size', type=int, default=100, help='バッチサイズ')
@click.option('--preview', is_flag=True, help='プレビューモード（実際の更新は行わない）')
def cleanup_database(batch_size: int, preview: bool):
    """データベースのsentenceフィールドをクリーンアップ"""
    
    click.echo("🧹 データベースsentenceクリーンアップ開始")
    click.echo(f"バッチサイズ: {batch_size}")
    click.echo(f"プレビューモード: {'有効' if preview else '無効'}")
    click.echo("-" * 60)
    
    db = Database('data/bungo_production.db')
    
    # 全placesを取得
    with db.get_connection() as conn:
        cursor = conn.execute("SELECT place_id, sentence FROM places ORDER BY place_id")
        places = cursor.fetchall()
    
    total_places = len(places)
    click.echo(f"📊 対象レコード: {total_places}件")
    
    if total_places == 0:
        click.echo("❌ クリーンアップ対象がありません")
        return
    
    # 統計情報
    stats = {
        'processed': 0,
        'cleaned': 0,
        'unchanged': 0,
        'examples': []
    }
    
    # バッチ処理
    for i in range(0, total_places, batch_size):
        batch = places[i:i + batch_size]
        click.echo(f"\n📦 バッチ {i//batch_size + 1}/{(total_places + batch_size - 1)//batch_size} 処理中...")
        
        batch_updates = []
        
        for place_id, original_sentence in batch:
            if not original_sentence:
                stats['unchanged'] += 1
                continue
            
            # クリーンアップ実行
            cleaned_sentence = clean_aozora_sentence(original_sentence)
            
            # 変更があるかチェック
            if cleaned_sentence != original_sentence:
                stats['cleaned'] += 1
                batch_updates.append((place_id, cleaned_sentence, original_sentence))
                
                # 例を保存（最初の5件）
                if len(stats['examples']) < 5:
                    stats['examples'].append({
                        'place_id': place_id,
                        'original': original_sentence[:100] + "..." if len(original_sentence) > 100 else original_sentence,
                        'cleaned': cleaned_sentence[:100] + "..." if len(cleaned_sentence) > 100 else cleaned_sentence
                    })
            else:
                stats['unchanged'] += 1
            
            stats['processed'] += 1
        
        # データベース更新（プレビューモードでない場合）
        if not preview and batch_updates:
            with db.get_connection() as conn:
                for place_id, cleaned_sentence, _ in batch_updates:
                    conn.execute(
                        "UPDATE places SET sentence = ? WHERE place_id = ?",
                        (cleaned_sentence, place_id)
                    )
                conn.commit()
            
            click.echo(f"  ✅ {len(batch_updates)}件更新")
        elif batch_updates:
            click.echo(f"  👀 {len(batch_updates)}件が更新対象（プレビューモード）")
        
        # 進捗表示
        progress = (stats['processed'] / total_places) * 100
        click.echo(f"  📊 進捗: {stats['processed']}/{total_places} ({progress:.1f}%)")
    
    # 最終結果
    click.echo("\n" + "=" * 60)
    click.echo("🎉 クリーンアップ完了！")
    click.echo(f"📊 最終統計:")
    click.echo(f"  処理レコード: {stats['processed']}")
    click.echo(f"  クリーンアップ: {stats['cleaned']}件")
    click.echo(f"  変更なし: {stats['unchanged']}件")
    click.echo(f"  変更率: {(stats['cleaned']/stats['processed']*100):.1f}%")
    
    if preview and stats['cleaned'] > 0:
        click.echo(f"\n⚠️  プレビューモードです。実際に更新するには --preview を外してください。")
    
    # クリーンアップ例を表示
    if stats['examples']:
        click.echo(f"\n📋 クリーンアップ例:")
        for i, example in enumerate(stats['examples'], 1):
            click.echo(f"  【例{i}】 place_id: {example['place_id']}")
            click.echo(f"    変更前: {example['original']}")
            click.echo(f"    変更後: {example['cleaned']}")
            click.echo()

@click.command()
def preview_cleanup():
    """プレビューモードでクリーンアップを実行"""
    ctx = click.get_current_context()
    ctx.invoke(cleanup_database, preview=True)

if __name__ == '__main__':
    cleanup_database() 