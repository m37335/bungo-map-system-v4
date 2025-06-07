#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ジオコーディングコマンド
地名を緯度・経度に変換
"""

import click
import logging
from typing import List
from bungo_map.core.database import init_db
from bungo_map.geocoding import Geocoder


class GeocodeManager:
    """ジオコーディング管理クラス"""
    
    def __init__(self, db_path: str = "data/bungo_production.db"):
        self.db = init_db(db_path)
        self.geocoder = Geocoder()
        
        # ログ設定
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def geocode_missing_places(self, limit: int = None) -> dict:
        """緯度・経度が不明な地名をジオコーディング"""
        
        # 緯度・経度が未設定の地名を取得
        places = self.db.get_places_without_coordinates(limit)
        
        if not places:
            click.echo("✅ ジオコーディングが必要な地名はありません")
            return {"total": 0, "success": 0, "failed": 0}
        
        click.echo(f"🌍 ジオコーディング開始: {len(places)}件の地名を処理")
        
        # ジオコーディング実行
        place_names = [place.place_name for place in places]
        results = self.geocoder.batch_geocode(place_names)
        
        # 結果をデータベースに更新
        success_count = 0
        failed_count = 0
        
        for place, result in zip(places, results):
            if result.lat is not None and result.lng is not None:
                # 座標を更新
                updated_place = place
                updated_place.lat = result.lat
                updated_place.lng = result.lng
                
                self.db.update_place(updated_place)
                success_count += 1
                
                click.echo(f"✅ {place.place_name}: ({result.lat:.4f}, {result.lng:.4f}) [{result.source}]")
            else:
                failed_count += 1
                error_msg = result.error or "不明なエラー"
                click.echo(f"❌ {place.place_name}: {error_msg}")
        
        # 統計表示
        click.echo(f"\n📊 ジオコーディング結果:")
        click.echo(f"  - 処理総数: {len(places)}件")
        click.echo(f"  - 成功: {success_count}件")
        click.echo(f"  - 失敗: {failed_count}件")
        click.echo(f"  - 成功率: {success_count/len(places)*100:.1f}%")
        
        return {
            "total": len(places),
            "success": success_count,
            "failed": failed_count
        }
    
    def test_geocoder(self, place_names: List[str]) -> None:
        """ジオコーダーのテスト"""
        click.echo(f"🧪 ジオコーダーテスト: {len(place_names)}件")
        
        results = self.geocoder.batch_geocode(place_names)
        
        click.echo("\n📍 テスト結果:")
        for result in results:
            if result.lat is not None:
                click.echo(f"✅ {result.place_name}: ({result.lat:.4f}, {result.lng:.4f}) "
                          f"[{result.source}] 信頼度: {result.confidence:.2f}")
                if result.formatted_address:
                    click.echo(f"   住所: {result.formatted_address}")
            else:
                click.echo(f"❌ {result.place_name}: {result.error}")
        
        # キャッシュ統計
        stats = self.geocoder.get_cache_stats()
        click.echo(f"\n📈 キャッシュ統計:")
        click.echo(f"  - キャッシュ総数: {stats['total_cached']}")
        click.echo(f"  - 成功: {stats['successful']}")
        click.echo(f"  - 失敗: {stats['failed']}")
        click.echo(f"  - 成功率: {stats['success_rate']*100:.1f}%")
    
    def show_coordinates_status(self) -> None:
        """座標設定状況を表示"""
        total_places = self.db.get_place_count()
        places_with_coords = self.db.get_places_with_coordinates_count()
        places_without_coords = total_places - places_with_coords
        
        click.echo("🗺️  座標設定状況:")
        click.echo(f"  - 総地名数: {total_places}")
        click.echo(f"  - 座標設定済み: {places_with_coords}")
        click.echo(f"  - 座標未設定: {places_without_coords}")
        
        if total_places > 0:
            completion_rate = places_with_coords / total_places * 100
            click.echo(f"  - 完了率: {completion_rate:.1f}%")
        
        # 未設定の地名一覧（最大10件）
        if places_without_coords > 0:
            missing_places = self.db.get_places_without_coordinates(limit=10)
            click.echo(f"\n📝 座標未設定の地名 (最大10件):")
            for place in missing_places:
                click.echo(f"  - {place.place_name} (作品: {place.work_id})")


@click.command()
@click.option('--all', is_flag=True, help='全ての未設定地名をジオコーディング')
@click.option('--limit', type=int, help='処理する地名数の上限')
@click.option('--test', help='テスト用地名（カンマ区切り）')
@click.option('--status', is_flag=True, help='座標設定状況を表示')
def geocode(all: bool, limit: int, test: str, status: bool):
    """🌍 ジオコーディングコマンド"""
    
    manager = GeocodeManager()
    
    if status:
        # 座標設定状況を表示
        manager.show_coordinates_status()
        
    elif test:
        # テストモード
        test_places = [name.strip() for name in test.split(',')]
        manager.test_geocoder(test_places)
        
    elif all or limit:
        # ジオコーディング実行
        manager.geocode_missing_places(limit)
        
    else:
        click.echo("使用方法:")
        click.echo("  --status                    # 座標設定状況表示")
        click.echo("  --all                       # 全地名をジオコーディング")
        click.echo("  --limit 10                  # 最大10件をジオコーディング")
        click.echo("  --test '東京,京都,松山市'     # テスト実行")


if __name__ == "__main__":
    geocode() 