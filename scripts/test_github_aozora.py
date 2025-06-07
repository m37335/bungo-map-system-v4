#!/usr/bin/env python3
"""
GitHub Aozorahack Client テスト
成功率30%問題を解決できるかテスト
"""

import sys
import os
import asyncio
import logging
import time
from pathlib import Path

# bungo_mapパッケージをインポート
sys.path.insert(0, str(Path(__file__).parent))
from bungo_map.extraction.github_aozora_client import GitHubAozoraClient

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_github_client():
    """GitHub Aozorahackクライアントのテスト"""
    print("🚀 GitHub Aozorahack Client テスト開始")
    print("="*60)
    
    client = GitHubAozoraClient()
    
    # Step 1: 統計情報取得
    print("\n📊 Step 1: 統計情報取得")
    try:
        stats = client.get_works_statistics()
        print(f"   📚 総作品数: {stats['total_works']} 作品")
        print(f"   👥 作者数: {stats['total_authors']} 人")
        print(f"   🔥 人気作者トップ5:")
        for i, (author, count) in enumerate(stats['top_authors'][:5], 1):
            print(f"      {i}. {author}: {count} 作品")
    except Exception as e:
        print(f"   ❌ 統計取得エラー: {e}")
        return False
    
    # Step 2: 作品検索テスト
    print("\n🔍 Step 2: 作品検索テスト")
    search_tests = [
        ("夏目漱石", "坊っちゃん"),
        ("芥川龍之介", "羅生門"),
        ("太宰治", "走れメロス"),
        ("宮沢賢治", "銀河鉄道の夜"),
        ("森鴎外", "舞姫")
    ]
    
    found_works = []
    for author, title in search_tests:
        work = client.search_work_by_title(title, author)
        if work:
            print(f"   ✅ 見つかりました: {work.title} by {work.author}")
            found_works.append((author, title, work))
        else:
            print(f"   ❌ 見つかりません: {title} by {author}")
    
    # Step 3: テキスト取得テスト（実際の404問題を検証）
    print(f"\n📖 Step 3: テキスト取得テスト（{len(found_works)} 作品）")
    
    successful_downloads = 0
    start_time = time.time()
    
    for author, title, work in found_works:
        print(f"\n   📚 {title} ({author}) ダウンロード中...")
        
        try:
            text = client.get_work_text(title, author)
            
            if text:
                print(f"      ✅ 成功: {len(text):,} 文字")
                print(f"      📄 先頭100文字: {text[:100].replace(chr(10), ' ')}...")
                
                # 青空文庫記法が除去されているかチェック
                if "［＃" in text or "《" in text:
                    print(f"      ⚠️ 青空文庫記法が残っています")
                else:
                    print(f"      ✨ 青空文庫記法が正しく除去されています")
                
                successful_downloads += 1
            else:
                print(f"      ❌ ダウンロード失敗")
                
        except Exception as e:
            print(f"      ❌ エラー: {e}")
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Step 4: 結果サマリー
    print(f"\n🎯 Step 4: 結果サマリー")
    print("="*60)
    
    total_tests = len(found_works)
    success_rate = (successful_downloads / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📊 総合結果:")
    print(f"   🎯 成功率: {success_rate:.1f}% ({successful_downloads}/{total_tests})")
    print(f"   ⏱️ 処理時間: {processing_time:.1f}秒")
    print(f"   📈 平均時間/作品: {processing_time/total_tests:.1f}秒" if total_tests > 0 else "")
    
    # 成功率比較
    print(f"\n📈 改善効果:")
    print(f"   🔴 旧システム成功率: 30.0% (404エラー多発)")
    print(f"   🟢 新システム成功率: {success_rate:.1f}%")
    
    if success_rate > 30:
        improvement = success_rate - 30
        print(f"   🚀 改善: +{improvement:.1f}ポイント!")
        print(f"   ✨ GitHub aozorahackによる404エラー解決効果を確認!")
    else:
        print(f"   ⚠️ 改善が必要です")
    
    # 推奨作品テスト
    print(f"\n🌟 Step 5: 推奨作品テスト")
    try:
        recommended = client.get_recommended_works()
        print(f"   📚 推奨作品数: {len(recommended)} 作品")
        print(f"   🎯 推奨作品例:")
        for work in recommended[:3]:
            print(f"      • {work.title} by {work.author}")
    except Exception as e:
        print(f"   ❌ 推奨作品取得エラー: {e}")
    
    return success_rate >= 80  # 80%以上で成功とする

async def run_extended_test():
    """拡張テスト：30作品での検証"""
    print(f"\n🔥 拡張テスト: 30作品で旧システム成功率30%を検証")
    print("="*60)
    
    client = GitHubAozoraClient()
    
    # 30作品のテストセット（旧システムで失敗したもの含む）
    extended_works = [
        ("夏目漱石", "坊っちゃん"), ("夏目漱石", "吾輩は猫である"), ("夏目漱石", "こころ"),
        ("芥川龍之介", "羅生門"), ("芥川龍之介", "蜘蛛の糸"), ("芥川龍之介", "鼻"),
        ("太宰治", "走れメロス"), ("太宰治", "人間失格"), ("太宰治", "津軽"),
        ("宮沢賢治", "銀河鉄道の夜"), ("宮沢賢治", "注文の多い料理店"), ("宮沢賢治", "風の又三郎"),
        ("森鴎外", "舞姫"), ("森鴎外", "高瀬舟"), ("森鴎外", "山椒大夫"),
        ("樋口一葉", "たけくらべ"), ("樋口一葉", "にごりえ"), ("樋口一葉", "十三夜"),
        ("島崎藤村", "破戒"), ("島崎藤村", "夜明け前"),
        ("志賀直哉", "城の崎にて"), ("志賀直哉", "小僧の神様"),
        ("川端康成", "伊豆の踊子"), ("川端康成", "雪国"),
        ("谷崎潤一郎", "細雪"), ("谷崎潤一郎", "春琴抄"),
        ("武者小路実篤", "友情"), ("有島武郎", "生れ出づる悩み"),
        ("石川啄木", "一握の砂"), ("正岡子規", "病床六尺")
    ]
    
    successful_count = 0
    start_time = time.time()
    
    for i, (author, title) in enumerate(extended_works, 1):
        print(f"[{i:2d}/30] {title} ({author}) ", end="")
        
        try:
            text = client.get_work_text(title, author)
            if text and len(text) > 100:
                print("✅")
                successful_count += 1
            else:
                print("❌")
        except:
            print("💥")
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    success_rate = (successful_count / len(extended_works)) * 100
    
    print(f"\n🎯 30作品テスト結果:")
    print(f"   📊 成功率: {success_rate:.1f}% ({successful_count}/30)")
    print(f"   ⏱️ 処理時間: {processing_time:.1f}秒")
    print(f"   📈 平均時間/作品: {processing_time/30:.1f}秒")
    
    print(f"\n📊 性能比較:")
    print(f"   🔴 旧システム: 30.0% (9/30) - 404エラー多発")
    print(f"   🟢 新システム: {success_rate:.1f}% ({successful_count}/30)")
    
    if success_rate > 30:
        improvement = success_rate - 30
        print(f"   🚀 改善効果: +{improvement:.1f}ポイント!")
        
        if success_rate >= 80:
            print(f"   🏆 優秀！新システムで404問題を完全解決!")
        elif success_rate >= 60:
            print(f"   👍 良好！大幅な改善を達成!")
        else:
            print(f"   📈 改善中！さらなる最適化が必要")

async def main():
    """メイン実行関数"""
    try:
        # 基本テスト
        basic_success = await test_github_client()
        
        if basic_success:
            # 拡張テスト（30作品）
            await run_extended_test()
        
        print(f"\n🎉 GitHub Aozorahackクライアントテスト完了!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ テストが中断されました")
    except Exception as e:
        print(f"\n❌ テストエラー: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 