#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪地図システム検索CLI
仕様書 bungo_update_spec_draft01.md 6章CLI仕様に基づく実装

使用例:
  bungo search author "夏目"      # 作者名あいまい検索 → 作品一覧
  bungo search work "坊っちゃん"   # 作品名検索 → 地名＋抜粋
  bungo search place "松山市"     # 地名検索 → 作者・作品逆引き
"""

import click
import time
from typing import List, Dict, Optional
from bungo_map.core.database import BungoDatabase


class BungoSearchEngine:
    """文豪地図システム検索エンジン"""
    
    def __init__(self, db_path: str = "bungo_map.db"):
        """検索エンジン初期化"""
        self.db = BungoDatabase(db_path)
        click.echo(f"📚 データベース接続: {db_path}")
    
    def search_author(self, query: str, limit: int = 10) -> Dict:
        """
        作者名あいまい検索 → 作品一覧
        仕様書要件: 作者名あいまい検索 → 作品一覧
        """
        start_time = time.time()
        
        # 作者検索（部分一致）
        authors = self.db.search_authors(query, limit)
        
        # 該当作者の作品一覧取得
        works = []
        for author in authors:
            author_works = self.db.get_works_by_author(author['author_id'])
            works.extend(author_works)
        
        execution_time = time.time() - start_time
        
        return {
            'query': query,
            'authors': authors,
            'works': works[:limit * 3],  # 作品は多めに表示
            'execution_time': execution_time,
            'total_authors': len(authors),
            'total_works': len(works)
        }
    
    def search_work(self, query: str, limit: int = 10) -> Dict:
        """
        作品名検索 → 地名＋抜粋
        仕様書要件: 作品名検索 → 地名＋抜粋
        """
        start_time = time.time()
        
        # 作品検索（部分一致）
        works = self.db.search_works(query, limit)
        
        # 該当作品の地名一覧取得
        places = []
        for work in works:
            work_places = self.db.get_places_by_work(work['work_id'])
            places.extend(work_places)
        
        execution_time = time.time() - start_time
        
        return {
            'query': query,
            'works': works,
            'places': places[:limit * 5],  # 地名は多めに表示
            'execution_time': execution_time,
            'total_works': len(works),
            'total_places': len(places)
        }
    
    def search_place(self, query: str, limit: int = 10) -> Dict:
        """
        地名検索 → 作者・作品逆引き
        仕様書要件: 地名検索 → 作者・作品逆引き
        """
        start_time = time.time()
        
        # 地名検索（部分一致）
        places = self.db.search_places(query, limit)
        
        # 関連作者・作品の逆引き
        authors = set()
        works = set()
        
        for place in places:
            if place.get('author_name'):
                authors.add(place['author_name'])
            if place.get('work_title'):
                works.add((place.get('author_name'), place['work_title']))
        
        execution_time = time.time() - start_time
        
        return {
            'query': query,
            'places': places,
            'authors': list(authors),
            'works': [{'author_name': author, 'title': work} for author, work in works],
            'execution_time': execution_time,
            'total_places': len(places),
            'total_authors': len(authors),
            'total_works': len(works)
        }
    
    def get_statistics(self) -> Dict:
        """データベース統計取得"""
        return self.db.get_statistics()
    
    def close(self):
        """データベース接続クローズ"""
        self.db.close()


def print_author_results(result: Dict):
    """作者検索結果表示"""
    query = result['query']
    authors = result['authors']
    works = result['works']
    exec_time = result['execution_time']
    
    click.echo(f"\n🔍 作者検索「{query}」")
    click.echo("=" * 50)
    click.echo(f"⚡ 実行時間: {exec_time:.3f}秒")
    click.echo(f"📊 結果: 作者{len(authors)}名、作品{len(works)}件")
    
    if not authors:
        click.echo("❌ 該当する作者が見つかりません")
        return
    
    # 作者詳細表示
    for i, author in enumerate(authors, 1):
        click.echo(f"\n{i}. 👤 【作者】{author['name']}")
        birth = author.get('birth_year', '不明')
        death = author.get('death_year', '不明')
        click.echo(f"   📅 生没年: {birth} - {death}")
        if author.get('wikipedia_url'):
            click.echo(f"   🔗 Wikipedia: {author['wikipedia_url']}")
    
    # 関連作品表示
    if works:
        click.echo(f"\n📚 関連作品:")
        for work in works[:10]:
            click.echo(f"   • {work.get('author_name', 'N/A')} - 『{work['title']}』")


def print_work_results(result: Dict):
    """作品検索結果表示"""
    query = result['query']
    works = result['works']
    places = result['places']
    exec_time = result['execution_time']
    
    click.echo(f"\n🔍 作品検索「{query}」")
    click.echo("=" * 50)
    click.echo(f"⚡ 実行時間: {exec_time:.3f}秒")
    click.echo(f"📊 結果: 作品{len(works)}件、地名{len(places)}箇所")
    
    if not works:
        click.echo("❌ 該当する作品が見つかりません")
        return
    
    # 作品詳細表示
    for i, work in enumerate(works, 1):
        click.echo(f"\n{i}. 📚 【作品】{work['title']}")
        click.echo(f"   👤 作者: {work.get('author_name', 'N/A')}")
        if work.get('publication_year'):
            click.echo(f"   📅 発表年: {work['publication_year']}年")
        if work.get('aozora_url'):
            click.echo(f"   📖 青空文庫: {work['aozora_url']}")
    
    # 地名・抜粋表示
    if places:
        click.echo(f"\n🗺️ 登場する地名:")
        for place in places[:15]:
            click.echo(f"   • {place['place_name']}")
            if place.get('latitude') and place.get('longitude'):
                click.echo(f"     📍 座標: ({place['latitude']:.4f}, {place['longitude']:.4f})")
            if place.get('sentence'):
                context = place['sentence'][:80] + "..." if len(place['sentence']) > 80 else place['sentence']
                click.echo(f"     💭 文脈: 「{context}」")
            click.echo()


def print_place_results(result: Dict):
    """地名検索結果表示"""
    query = result['query']
    places = result['places']
    authors = result['authors']
    works = result['works']
    exec_time = result['execution_time']
    
    click.echo(f"\n🔍 地名検索「{query}」")
    click.echo("=" * 50)
    click.echo(f"⚡ 実行時間: {exec_time:.3f}秒")
    click.echo(f"📊 結果: 地名{len(places)}箇所、関連作者{len(authors)}名、関連作品{len(works)}件")
    
    if not places:
        click.echo("❌ 該当する地名が見つかりません")
        return
    
    # 地名詳細表示
    for i, place in enumerate(places, 1):
        click.echo(f"\n{i}. 🗺️ 【地名】{place['place_name']}")
        click.echo(f"   📚 作品: {place.get('author_name', 'N/A')} - 『{place.get('work_title', 'N/A')}』")
        
        if place.get('latitude') and place.get('longitude'):
            click.echo(f"   📍 座標: ({place['latitude']:.4f}, {place['longitude']:.4f})")
        if place.get('address'):
            click.echo(f"   🏠 住所: {place['address']}")
        
        if place.get('sentence'):
            context = place['sentence'][:100] + "..." if len(place['sentence']) > 100 else place['sentence']
            click.echo(f"   💭 文脈: 「{context}」")
    
    # 関連作者・作品サマリー
    if authors:
        click.echo(f"\n👤 関連作者: {', '.join(authors)}")
    if works:
        click.echo(f"\n📚 関連作品:")
        for work in works[:5]:
            click.echo(f"   • {work['author_name']} - 『{work['title']}』")


@click.group()
def search():
    """🔍 検索コマンド"""
    pass


@search.command()
@click.argument('query')
@click.option('--limit', default=10, help='最大結果数')
@click.option('--db', default='bungo_map.db', help='データベースファイル')
def author(query: str, limit: int, db: str):
    """作者名あいまい検索 → 作品一覧"""
    try:
        engine = BungoSearchEngine(db)
        result = engine.search_author(query, limit)
        print_author_results(result)
        engine.close()
    except Exception as e:
        click.echo(f"❌ エラー: {e}")


@search.command()
@click.argument('query')
@click.option('--limit', default=10, help='最大結果数')
@click.option('--db', default='bungo_map.db', help='データベースファイル')
def work(query: str, limit: int, db: str):
    """作品名検索 → 地名＋抜粋"""
    try:
        engine = BungoSearchEngine(db)
        result = engine.search_work(query, limit)
        print_work_results(result)
        engine.close()
    except Exception as e:
        click.echo(f"❌ エラー: {e}")


@search.command()
@click.argument('query')
@click.option('--limit', default=10, help='最大結果数')
@click.option('--db', default='bungo_map.db', help='データベースファイル')
def place(query: str, limit: int, db: str):
    """地名検索 → 作者・作品逆引き"""
    try:
        engine = BungoSearchEngine(db)
        result = engine.search_place(query, limit)
        print_place_results(result)
        engine.close()
    except Exception as e:
        click.echo(f"❌ エラー: {e}")


@search.command()
@click.option('--db', default='bungo_map.db', help='データベースファイル')
def stats(db: str):
    """データベース統計表示"""
    try:
        engine = BungoSearchEngine(db)
        stats = engine.get_statistics()
        
        click.echo("\n📈 データベース統計")
        click.echo("=" * 30)
        click.echo(f"👤 作者数: {stats.get('authors_count', 0)}名")
        click.echo(f"📚 作品数: {stats.get('works_count', 0)}作品")
        click.echo(f"🗺️ 地名数: {stats.get('places_count', 0)}箇所")
        click.echo(f"📍 ジオコーディング率: {stats.get('geocoded_rate', 0):.1f}%")
        click.echo(f"✅ ジオコーディング済み: {stats.get('geocoded_count', 0)}箇所")
        
        engine.close()
    except Exception as e:
        click.echo(f"❌ エラー: {e}")


if __name__ == "__main__":
    search() 