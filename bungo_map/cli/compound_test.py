#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 AI複合地名抽出効果検証
従来手法 vs AI複合地名抽出の比較テスト
"""

import click
from bungo_map.extractors.simple_place_extractor import SimplePlaceExtractor
from bungo_map.ai.extractors.precise_compound_extractor import PreciseCompoundExtractor

@click.command()
def test_compound_extraction():
    """AI複合地名抽出の効果検証"""
    
    # テストケース
    test_cases = [
        {
            "text": "福岡県京都郡真崎村小川三四郎二十三年学生と正直に書いた",
            "expected": "福岡県京都郡真崎村",
            "description": "3層複合地名（都道府県+郡+村）"
        },
        {
            "text": "然るに、ことしの二月、私は千葉県船橋市に疎開している或る友人をたずねた",
            "expected": "千葉県船橋市", 
            "description": "2層複合地名（都道府県+市）"
        },
        {
            "text": "東京都新宿区にある高層ビルから富士山を眺める",
            "expected": "東京都新宿区",
            "description": "2層複合地名（都道府県+区）"
        },
        {
            "text": "北海道札幌市白石区で生まれ育った友人",
            "expected": "北海道札幌市白石区",
            "description": "3層複合地名（道+市+区）"
        }
    ]
    
    # 抽出器の初期化
    regex_extractor = SimplePlaceExtractor()
    ai_compound_extractor = PreciseCompoundExtractor()
    
    click.echo("🧪 AI複合地名抽出効果検証\n")
    click.echo("=" * 80)
    
    total_tests = len(test_cases)
    regex_success = 0
    ai_success = 0
    
    for i, case in enumerate(test_cases, 1):
        click.echo(f"\n【テスト{i}】 {case['description']}")
        click.echo(f"テキスト: {case['text'][:60]}...")
        click.echo(f"期待結果: {case['expected']}")
        click.echo("-" * 60)
        
        # 従来のRegex抽出
        regex_places = regex_extractor.extract_places_from_text(999, case['text'])
        regex_names = [place.place_name for place in regex_places]
        regex_found = case['expected'] in regex_names
        
        if regex_found:
            regex_success += 1
        
        click.echo(f"📋 従来Regex: {len(regex_names)}件 - {regex_names}")
        click.echo(f"   期待結果検出: {'✅' if regex_found else '❌'}")
        
        # AI複合地名抽出
        ai_places = ai_compound_extractor.extract_precise_places(999, case['text'])
        ai_names = [place.place_name for place in ai_places]
        ai_found = case['expected'] in ai_names
        
        if ai_found:
            ai_success += 1
        
        click.echo(f"🤖 AI複合地名: {len(ai_names)}件 - {ai_names}")
        click.echo(f"   期待結果検出: {'✅' if ai_found else '❌'}")
        
        # 改善効果
        if ai_found and not regex_found:
            click.echo(f"🚀 改善: AI複合地名抽出により '{case['expected']}' を正しく検出！")
        elif regex_found and not ai_found:
            click.echo(f"⚠️  劣化: AI複合地名抽出で '{case['expected']}' を見落とし")
        elif regex_found and ai_found:
            click.echo("✅ 両手法で検出成功")
        else:
            click.echo("❌ 両手法で検出失敗")
    
    # 総合結果
    click.echo("\n" + "=" * 80)
    click.echo("📊 総合結果")
    click.echo(f"従来Regex: {regex_success}/{total_tests} ({regex_success/total_tests*100:.1f}%) 成功")
    click.echo(f"AI複合地名: {ai_success}/{total_tests} ({ai_success/total_tests*100:.1f}%) 成功")
    
    improvement = ai_success - regex_success
    if improvement > 0:
        click.echo(f"🎉 改善効果: +{improvement}件 ({improvement/total_tests*100:.1f}%ポイント向上)")
    elif improvement < 0:
        click.echo(f"⚠️  性能低下: {improvement}件 ({abs(improvement)/total_tests*100:.1f}%ポイント低下)")
    else:
        click.echo("➡️  性能同等")
    
    # 推奨事項
    click.echo("\n📋 推奨事項:")
    if ai_success > regex_success:
        click.echo("✅ AI複合地名抽出の導入を強く推奨")
        click.echo("   - 複合地名の検出精度が大幅に向上")
        click.echo("   - 境界条件問題の解決")
        click.echo("   - 地理的階層構造の正確な理解")
    else:
        click.echo("⚠️  AI複合地名抽出の調整が必要")
        click.echo("   - パターンマッチングの精度向上")
        click.echo("   - 境界条件の最適化")

if __name__ == '__main__':
    test_compound_extraction() 