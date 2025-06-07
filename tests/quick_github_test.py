#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from bungo_map.extraction.github_aozora_client import GitHubAozoraClient

print('🚀 GitHub Aozorahack Client 簡単テスト')
print('='*50)

client = GitHubAozoraClient()

# 統計取得
print('📊 統計取得中...')
try:
    stats = client.get_works_statistics()
    print(f'✅ 総作品数: {stats["total_works"]} 作品')
    print(f'✅ 作者数: {stats["total_authors"]} 人')
    print(f'🔥 人気作者トップ3:')
    for i, (author, count) in enumerate(stats['top_authors'][:3], 1):
        print(f'   {i}. {author}: {count} 作品')
except Exception as e:
    print(f'❌ 統計取得エラー: {e}')
    exit(1)

# テスト作品取得
print('\n📖 テスト作品取得')
test_works = [
    ('夏目漱石', '坊っちゃん'), 
    ('芥川龍之介', '羅生門'), 
    ('太宰治', '走れメロス')
]

success_count = 0
for author, title in test_works:
    print(f'   📚 {title} ({author}) 取得中...', end=' ')
    try:
        text = client.get_work_text(title, author)
        if text and len(text) > 100:
            print(f'✅ {len(text):,} 文字')
            success_count += 1
        else:
            print('❌ 失敗')
    except Exception as e:
        print(f'💥 エラー: {e}')

# 結果
success_rate = (success_count / len(test_works)) * 100
print(f'\n🎯 結果サマリー')
print(f'   成功率: {success_rate:.1f}% ({success_count}/{len(test_works)})')
print(f'   旧システム: 30.0% (404エラー多発)')
print(f'   新システム: {success_rate:.1f}%')

if success_rate > 30:
    improvement = success_rate - 30
    print(f'   🚀 改善: +{improvement:.1f}ポイント!')
    print('   ✨ GitHub aozorahackで404エラー解決!')
else:
    print('   ⚠️ 改善が必要です')