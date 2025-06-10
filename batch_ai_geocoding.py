#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 バッチAI Geocoding実行スクリプト
全地名を一括でAI文脈判断型Geocodingで処理
"""

import sqlite3
import time
from bungo_map.ai.context_aware_geocoding import ContextAwareGeocodingService

def batch_ai_geocoding():
    """全地名のバッチAI Geocoding"""
    print("🚀 バッチAI文脈判断型Geocoding開始")
    
    # サービス初期化
    service = ContextAwareGeocodingService()
    
    # データベースから全未処理地名を取得
    with sqlite3.connect('/app/data/bungo_production.db') as conn:
        cursor = conn.execute("""
            SELECT place_name, sentence, before_text, after_text, COUNT(*) as count
            FROM places 
            WHERE lat IS NULL 
            GROUP BY place_name
            ORDER BY count DESC
        """)
        unique_places = cursor.fetchall()
        print(f'📊 未処理の固有地名数: {len(unique_places)}件')
        
        # 総処理対象数を取得
        total_cursor = conn.execute('SELECT COUNT(*) FROM places WHERE lat IS NULL')
        total_count = total_cursor.fetchone()[0]
        print(f'📊 未処理の総地名数: {total_count}件')
        
        success_count = 0
        failed_places = []
        batch_size = 50
        batch_count = 0
        
        for i, (place_name, sentence, before_text, after_text, count) in enumerate(unique_places):
            print(f'\n🗺️ [{i+1}/{len(unique_places)}] {place_name} ({count}箇所)')
            
            # AI文脈判断型Geocoding実行
            result = service.geocode_place_sync(
                place_name, 
                sentence or '', 
                before_text or '', 
                after_text or ''
            )
            
            if result and result.latitude is not None:
                print(f'✅ 座標取得: ({result.latitude:.4f}, {result.longitude:.4f}) [{result.source}]')
                
                # この地名の全レコードを更新
                conn.execute("""
                    UPDATE places 
                    SET lat = ?, lng = ?, geocoding_source = ?, geocoding_status = 'success'
                    WHERE place_name = ? AND lat IS NULL
                """, (result.latitude, result.longitude, result.source, place_name))
                
                success_count += count  # 実際の更新件数を追加
                
                # バッチサイズごとにコミット
                batch_count += 1
                if batch_count % batch_size == 0:
                    conn.commit()
                    print(f'💾 バッチコミット完了 ({batch_count}件処理)')
                    time.sleep(0.1)  # API負荷軽減
                    
            else:
                print(f'❌ 座標取得失敗')
                failed_places.append(place_name)
                
                # 失敗レコードもステータス更新
                conn.execute("""
                    UPDATE places 
                    SET geocoding_status = 'failed'
                    WHERE place_name = ? AND lat IS NULL
                """, (place_name,))
        
        # 最終コミット
        conn.commit()
        
        # 結果サマリー
        print(f'\n{"="*60}')
        print(f'🎉 バッチAI Geocoding完了！')
        print(f'{"="*60}')
        print(f'📊 処理結果:')
        print(f'   ✅ 成功地名数: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)')
        print(f'   ❌ 失敗地名数: {len(failed_places)}種類')
        print(f'   🔍 固有地名処理: {len(unique_places)}種類')
        
        if failed_places:
            print(f'\n❌ 失敗した地名（一部）:')
            for place in failed_places[:10]:
                print(f'   - {place}')
            if len(failed_places) > 10:
                print(f'   ... 他{len(failed_places)-10}件')

if __name__ == "__main__":
    batch_ai_geocoding() 