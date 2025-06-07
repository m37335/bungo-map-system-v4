#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データ収集コマンド
"""

import click
from typing import List
from bungo_map.core.database import init_db
from bungo_map.extractors.wikipedia_extractor import WikipediaExtractor
from bungo_map.extractors.place_extractor import PlaceExtractor
from bungo_map.extractors.ginza_place_extractor import GinzaPlaceExtractor


class DataCollector:
    """データ収集パイプライン"""
    
    def __init__(self, db_path: str = "data/bungo_production.db"):
        self.db = init_db(db_path)
        self.wiki_extractor = WikipediaExtractor()
        self.place_extractor = PlaceExtractor()
        self.ginza_extractor = None  # 遅延初期化
        
    def _get_ginza_extractor(self):
        """GiNZA抽出器の遅延初期化"""
        if self.ginza_extractor is None:
            self.ginza_extractor = GinzaPlaceExtractor()
        return self.ginza_extractor
        
    def collect_author_data(self, author_name: str, limit: int = 5, use_ginza: bool = False) -> dict:
        """作者のデータを収集"""
        result = {
            "author": None,
            "works": [],
            "places": [],
            "stats": {"authors": 0, "works": 0, "places": 0}
        }
        
        extraction_method = "GiNZA NLP" if use_ginza else "サンプルデータ"
        click.echo(f"📚 {author_name} のデータ収集開始... (抽出方法: {extraction_method})")
        
        # 1. 作者情報を取得・挿入
        author = self.wiki_extractor.extract_author_data(author_name)
        if author:
            author_id = self.db.insert_author(author)
            author.author_id = author_id
            result["author"] = author
            result["stats"]["authors"] = 1
            click.echo(f"✅ 作者情報登録: {author_name} (ID: {author_id})")
            
            # 2. 作品情報を取得・挿入
            works = self.wiki_extractor.extract_works_data(author_id, author_name, limit)
            for work in works:
                work_id = self.db.insert_work(work)
                work.work_id = work_id
                result["works"].append(work)
                result["stats"]["works"] += 1
                click.echo(f"  📖 作品登録: {work.title} (ID: {work_id})")
                
                # 3. 地名情報を抽出・挿入
                if use_ginza:
                    # GiNZAによる本格的な地名抽出（模擬テキスト使用）
                    places = self._extract_with_ginza(work_id, work.title)
                else:
                    # サンプルデータによる地名抽出
                    places = self.place_extractor.extract_places(work_id, work.title)
                
                for place in places:
                    place_id = self.db.insert_place(place)
                    place.place_id = place_id
                    result["places"].append(place)
                    result["stats"]["places"] += 1
                    click.echo(f"    📍 地名登録: {place.place_name} (信頼度: {place.confidence:.2f})")
        
        return result
    
    def _extract_with_ginza(self, work_id: int, work_title: str) -> List:
        """GiNZAを使った地名抽出（模擬テキスト版）"""
        ginza = self._get_ginza_extractor()
        
        # 作品別の模擬テキスト（実際にはこれを青空文庫から取得）
        mock_texts = {
            "坊っちゃん": """
            汽車が松山市に着いた時には、もう日が暮れていた。プラットホームには赤シャツが
            迎えに来ていて、おれを宿屋まで案内してくれた。翌日、道後温泉に連れて行かれた。
            湯は思ったより熱く、瀬戸内海を望む風景は美しかった。愛媛県の風景は素晴らしい。
            """,
            "吾輩は猫である": """
            この家は東京の片隅にある小さな家である。主人は学校の教師をしている。
            毎日本郷の学校へ通っている。時々上野の博物館や浅草の寺を訪れることもある。
            この辺りは文京区で、昔からの住宅街である。
            """,
            "こころ": """
            私は夏休みに鎌倉の海岸で先生と出会った。先生は毎日同じ時刻に海に入り、
            同じように上がって、同じ場所で休んでいた。秋になって東京に戻ると、
            先生との文通が始まった。神奈川県の海辺の思い出は忘れられない。
            """,
            "羅生門": """
            ある日の暮方の事である。一人の下人が京都の羅生門の下で雨やみを待っていた。
            羅生門から朱雀大路を見下ろすと人影はない。ただ、ところどころに夕日が
            照っているだけである。京都府の古い都の面影がそこにはあった。
            """,
            "人間失格": """
            私の生まれた津軽の大きな家の思い出。父は地主で、この辺りでは名の知れた家だった。
            やがて東京の学校に入学することになった。青森県から本州への旅は長かった。
            """,
            "走れメロス": """
            メロスは激怒した。必ず、かの邪智暴虐の王を除かなければならぬと決意した。
            きょう未明シラクスの市に出て来て、王の不信を確信した。シチリア島の古い都市である。
            """
        }
        
        text = mock_texts.get(work_title, "")
        if text:
            return ginza.extract_places_from_text(work_id, text.strip())
        else:
            # GiNZA用のサンプルデータがない場合は空リストを返す
            return []
    
    def collect_multiple_authors(self, author_names: List[str], limit: int = 5, use_ginza: bool = False) -> dict:
        """複数作者のデータを収集"""
        total_result = {
            "authors": [],
            "works": [],
            "places": [],
            "stats": {"authors": 0, "works": 0, "places": 0}
        }
        
        for author_name in author_names:
            result = self.collect_author_data(author_name, limit, use_ginza)
            
            if result["author"]:
                total_result["authors"].append(result["author"])
                total_result["works"].extend(result["works"])
                total_result["places"].extend(result["places"])
                
                # 統計を累積
                for key in total_result["stats"]:
                    total_result["stats"][key] += result["stats"][key]
            
            click.echo("")  # 空行
        
        return total_result


@click.command()
@click.option('--author', help='収集する作者名')
@click.option('--limit', default=5, help='作品数制限')
@click.option('--demo', is_flag=True, help='デモ用サンプルデータ収集')
@click.option('--ginza', is_flag=True, help='GiNZA NLP地名抽出を使用')
def collect(author: str, limit: int, demo: bool, ginza: bool):
    """📚 データ収集コマンド"""
    
    collector = DataCollector()
    
    if demo:
        # デモ用: 3人の有名作家のデータを収集
        extraction_method = "GiNZA NLP" if ginza else "サンプルデータ"
        click.echo(f"🎭 デモデータ収集開始... (抽出方法: {extraction_method})")
        demo_authors = ["夏目漱石", "芥川龍之介", "太宰治"]
        result = collector.collect_multiple_authors(demo_authors, limit=3, use_ginza=ginza)
        
        click.echo("🎉 デモデータ収集完了！")
        click.echo(f"📊 統計: 作者{result['stats']['authors']}人, "
                  f"作品{result['stats']['works']}作品, "
                  f"地名{result['stats']['places']}箇所")
        
    elif author:
        # 個別作家のデータ収集
        result = collector.collect_author_data(author, limit, use_ginza=ginza)
        
        if result["author"]:
            click.echo("🎉 データ収集完了！")
            click.echo(f"📊 統計: 作者{result['stats']['authors']}人, "
                      f"作品{result['stats']['works']}作品, "
                      f"地名{result['stats']['places']}箇所")
        else:
            click.echo("❌ 作者情報の取得に失敗しました")
    else:
        click.echo("使用方法:")
        click.echo("  --author '夏目漱石'          # 個別作家")
        click.echo("  --demo                      # デモデータ")
        click.echo("  --ginza                     # GiNZA NLP抽出")
        click.echo("  --demo --ginza              # デモ + GiNZA")


if __name__ == "__main__":
    collect() 