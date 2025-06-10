#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Regex地名抽出問題解決コマンド
重複抽出と緯度経度変換問題を解決
"""

import click
import sqlite3
from typing import List, Dict
from bungo_map.extractors.improved_place_extractor import ImprovedPlaceExtractor

@click.group()
def regex():
    """Regex地名抽出の問題解決コマンド"""
    pass

@regex.command()
@click.option('--db-path', default='data/bungo_production.db', help='データベースパス')
@click.option('--limit', default=10, help='確認する件数')
def analyze_duplicates(db_path: str, limit: int):
    """重複抽出問題の分析"""
    click.echo("🔍 重複抽出問題を分析中...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 同じsentence内で複数抽出された地名を検索
    query = """
    SELECT sentence, GROUP_CONCAT(place_name, ', ') as places, 
           GROUP_CONCAT(extraction_method, ', ') as methods,
           COUNT(*) as count
    FROM places 
    WHERE sentence IS NOT NULL
    GROUP BY sentence 
    HAVING COUNT(*) > 1 
    ORDER BY COUNT(*) DESC 
    LIMIT ?
    """
    
    results = cursor.execute(query, (limit,)).fetchall()
    
    if not results:
        click.echo("✅ 重複抽出は検出されませんでした")
        return
    
    click.echo(f"\n🚨 重複抽出問題 {len(results)}件検出:\n")
    
    for i, (sentence, places, methods, count) in enumerate(results, 1):
        click.echo(f"【{i}】重複数: {count}件")
        click.echo(f"文: {sentence[:100]}...")
        click.echo(f"抽出地名: {places}")
        click.echo(f"抽出方法: {methods}")
        click.echo("-" * 80)
    
    conn.close()

@regex.command()
@click.option('--db-path', default='data/bungo_production.db', help='データベースパス')
@click.option('--test-text', help='テスト用テキスト')
def test_improvement(db_path: str, test_text: str):
    """改良版抽出器のテスト"""
    
    if test_text:
        texts = [test_text]
    else:
        # デフォルトテストケース
        texts = [
            "然るに、ことしの二月、私は千葉県船橋市に疎開している或る友人をたずねた",
            "その友人は、リュックサックを背負って船橋市へ出かけて行ったのである",
            "福岡県京都郡真崎村小川三四郎二十三年学生と正直に書いた"
        ]
    
    extractor = ImprovedPlaceExtractor()
    
    click.echo("🧪 改良版抽出器テスト結果:\n")
    
    for i, text in enumerate(texts, 1):
        click.echo(f"【テスト{i}】")
        analysis = extractor.analyze_extraction_problems(text)
        
        click.echo(f"📝 入力: {analysis['input_text']}")
        
        current = analysis['current_problems']
        improved = analysis['improved_results']
        comparison = analysis['comparison']
        
        click.echo(f"❌ 現在: {current['total_matches']}件抽出")
        if current['overlapping_groups']:
            click.echo(f"   重複グループ: {len(current['overlapping_groups'])}個")
        
        click.echo(f"✅ 改良版: {improved['total_matches']}件抽出")
        click.echo(f"📊 削減率: {comparison['reduction_rate']:.1%}")
        click.echo(f"📈 品質向上: {comparison['quality_improvement']:.1%}")
        click.echo()

@regex.command()
@click.option('--db-path', default='data/bungo_production.db', help='データベースパス')
@click.option('--geocoding-issues', is_flag=True, help='緯度経度変換問題を確認')
def check_geocoding(db_path: str, geocoding_issues: bool):
    """緯度経度変換問題の確認"""
    click.echo("🌍 緯度経度変換状況を確認中...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if geocoding_issues:
        # 変換に失敗した地名を確認
        query = """
        SELECT place_name, COUNT(*) as count,
               SUM(CASE WHEN lat IS NOT NULL AND lng IS NOT NULL THEN 1 ELSE 0 END) as geocoded,
               SUM(CASE WHEN lat IS NULL OR lng IS NULL THEN 1 ELSE 0 END) as not_geocoded
        FROM places 
        GROUP BY place_name 
        HAVING not_geocoded > 0
        ORDER BY not_geocoded DESC 
        LIMIT 15
        """
        
        results = cursor.execute(query).fetchall()
        
        click.echo("\n🚨 緯度経度変換に失敗した地名:\n")
        
        for place, total, geocoded, not_geocoded in results:
            success_rate = (geocoded / total) * 100 if total > 0 else 0
            click.echo(f"📍 {place}")
            click.echo(f"   総件数: {total}, 変換成功: {geocoded}, 失敗: {not_geocoded}")
            click.echo(f"   成功率: {success_rate:.1f}%")
            click.echo()
    
    else:
        # 全体的な変換状況
        stats_query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN lat IS NOT NULL AND lng IS NOT NULL THEN 1 ELSE 0 END) as geocoded,
            SUM(CASE WHEN lat IS NULL OR lng IS NULL THEN 1 ELSE 0 END) as not_geocoded
        FROM places
        """
        
        total, geocoded, not_geocoded = cursor.execute(stats_query).fetchone()
        success_rate = (geocoded / total) * 100 if total > 0 else 0
        
        click.echo(f"\n📊 緯度経度変換統計:")
        click.echo(f"   総地名数: {total:,}")
        click.echo(f"   変換成功: {geocoded:,} ({success_rate:.1f}%)")
        click.echo(f"   変換失敗: {not_geocoded:,} ({100-success_rate:.1f}%)")
    
    conn.close()

@regex.command()
@click.option('--db-path', default='data/bungo_production.db', help='データベースパス')
@click.option('--dry-run', is_flag=True, help='実際の変更は行わずテストのみ')
def fix_regex_patterns(db_path: str, dry_run: bool):
    """regex抽出パターンの修正適用"""
    click.echo("🔧 Regex抽出パターンの修正を適用中...")
    
    if dry_run:
        click.echo("🧪 ドライランモード: 実際の変更は行いません")
    
    # 修正提案の表示
    improvements = {
        "境界条件追加": {
            "before": r'[千葉][都道府県]',
            "after": r'(?<![一-龯])[千葉][都道府県](?![一-龯])',
            "benefit": "「千葉県船橋市」から「葉県」誤抽出を防止"
        },
        "優先度ベース重複排除": {
            "description": "完全地名 > 都道府県 > 市区町村 > 有名地名の順で優先",
            "benefit": "「千葉県船橋市」「葉県」「船橋」→「千葉県船橋市」のみ抽出"
        },
        "長さ制限強化": {
            "before": r'[一-龯]{2,8}[市区町村]',
            "after": r'[一-龯]{2,6}[市区町村]',
            "benefit": "品質向上（極端に長い誤抽出防止）"
        }
    }
    
    click.echo("\n📋 実装する改善案:\n")
    
    for name, details in improvements.items():
        click.echo(f"✨ {name}")
        if 'before' in details:
            click.echo(f"   修正前: {details['before']}")
            click.echo(f"   修正後: {details['after']}")
        if 'description' in details:
            click.echo(f"   詳細: {details['description']}")
        click.echo(f"   効果: {details['benefit']}")
        click.echo()
    
    if not dry_run:
        click.echo("⚠️  実際の修正実装は開発者による手動適用が必要です")
        click.echo("   simple_place_extractor.py の _build_place_patterns() を更新してください")

if __name__ == '__main__':
    regex() 