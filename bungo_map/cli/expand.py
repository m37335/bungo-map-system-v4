#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データ拡充CLI - 大規模データ拡充機能
"""

import argparse
import time
from typing import List, Dict
import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from bungo_map.core.database import BungoDatabase
from bungo_map.extractors.wikipedia_extractor import WikipediaExtractor
from bungo_map.extractors.aozora_extractor import AozoraExtractor


class DataExpansionEngine:
    """データ拡充エンジン"""
    
    def __init__(self, db_path: str = "data/bungo_production.db"):
        self.db = BungoDatabase(db_path)
        self.wiki_extractor = WikipediaExtractor()
        self.aozora_extractor = AozoraExtractor()
        
    def expand_authors(self, target_count: int = 30, test_mode: bool = False) -> Dict:
        """作者データを拡充する"""
        print(f"\n🚀 **作者データ拡充開始** (目標: {target_count}名)")
        
        start_time = time.time()
        
        # 現在の作者数確認（全作者検索で取得）
        current_authors = self.db.search_authors("", limit=1000)  # 空文字で全作者検索
        current_count = len(current_authors)
        print(f"📊 現在の作者数: {current_count}名")
        
        if current_count >= target_count:
            print(f"✅ 既に目標数に達しています ({current_count} >= {target_count})")
            return {"status": "already_sufficient", "current_count": current_count}
        
        # 著名文豪リスト取得
        famous_authors = self.wiki_extractor.get_famous_authors_list()
        
        # 既存作者名セット
        existing_names = {author['name'] for author in current_authors}
        
        # 新規追加対象の作者
        new_authors = [name for name in famous_authors if name not in existing_names]
        needed_count = target_count - current_count
        
        if test_mode:
            new_authors = new_authors[:3]  # テストモードでは3名まで
            
        target_authors = new_authors[:needed_count]
        
        print(f"📝 新規追加予定: {len(target_authors)}名")
        print(f"   {', '.join(target_authors)}")
        
        success_count = 0
        results = []
        
        for i, author_name in enumerate(target_authors, 1):
            print(f"\n[{i}/{len(target_authors)}] {author_name} を処理中...")
            
            try:
                # 作者情報をWikipediaから抽出
                author_data = self.wiki_extractor.extract_author_data(author_name)
                
                if author_data:
                    # データベースに作者を追加
                    author_id = self.db.insert_author(author_data)
                    
                    if author_id:
                        # 作品情報を抽出
                        works_data = self.wiki_extractor.extract_works_data(author_id, author_name, limit=10)
                        
                        # 作品をデータベースに追加
                        work_count = 0
                        for work in works_data:
                            work_id = self.db.insert_work(work)
                            if work_id:
                                work_count += 1
                        
                        success_count += 1
                        result = {
                            'author_name': author_name,
                            'author_id': author_id,
                            'works_added': work_count,
                            'status': 'success'
                        }
                        results.append(result)
                        
                        print(f"✅ {author_name}: 作者追加完了, {work_count}作品追加")
                    else:
                        print(f"❌ {author_name}: データベース挿入失敗")
                        results.append({'author_name': author_name, 'status': 'db_error'})
                else:
                    print(f"❌ {author_name}: Wikipedia情報取得失敗")
                    results.append({'author_name': author_name, 'status': 'extraction_error'})
                    
            except Exception as e:
                print(f"❌ {author_name}: エラー - {e}")
                results.append({'author_name': author_name, 'status': 'error', 'error': str(e)})
            
            # API制限対策: 少し待機
            time.sleep(1)
        
        end_time = time.time()
        
        # 最終結果
        final_authors = self.db.search_authors("", limit=1000)
        final_count = len(final_authors)
        
        summary = {
            'initial_count': current_count,
            'target_count': target_count,
            'final_count': final_count,
            'success_count': success_count,
            'failed_count': len(target_authors) - success_count,
            'execution_time': round(end_time - start_time, 2),
            'results': results
        }
        
        print(f"\n🎉 **作者データ拡充完了**")
        print(f"   開始時: {current_count}名 → 完了時: {final_count}名")
        print(f"   成功: {success_count}名, 失敗: {len(target_authors) - success_count}名")
        print(f"   実行時間: {summary['execution_time']}秒")
        
        return summary
    
    def expand_places_for_author(self, author_name: str, force_update: bool = False) -> Dict:
        """特定作者の地名データを拡充する"""
        print(f"\n📍 {author_name} の地名データ拡充開始...")
        
        start_time = time.time()
        
        # 作者情報取得
        authors = self.db.search_authors(author_name)
        if not authors:
            print(f"❌ 作者が見つかりません: {author_name}")
            return {"status": "author_not_found"}
        
        author = authors[0]
        
        # 作者の作品を取得
        works = self.db.get_works_by_author(author.author_id)
        print(f"📚 {author.name} の作品数: {len(works)}作品")
        
        total_places_added = 0
        results = []
        
        for work in works:
            print(f"\n   📖 {work.title} を処理中...")
            
            try:
                # 既存の地名数確認
                existing_places = self.db.get_places_by_work(work.work_id)
                
                if existing_places and not force_update:
                    print(f"      ⏭️  既に{len(existing_places)}地名あり（スキップ）")
                    continue
                
                # 青空文庫から本文取得
                aozora_url = self.aozora_extractor.search_aozora_work(work['title'], author['name'])
                
                if aozora_url:
                    print(f"      📥 青空文庫からダウンロード中...")
                    text_content = self.aozora_extractor.download_and_extract_text(aozora_url)
                    
                    if text_content:
                        print(f"      ✅ テキスト取得成功: {len(text_content)}文字")
                        # TODO: GiNZAで地名抽出（次のステップで実装）
                        print(f"      ⚠️ 地名抽出機能は次のステップで実装予定")
                        
                        result = {
                            'work_title': work['title'],
                            'places_added': 0,
                            'text_length': len(text_content),
                            'status': 'text_ready'
                        }
                        results.append(result)
                    else:
                        print(f"      ❌ 本文取得失敗")
                        results.append({'work_title': work['title'], 'status': 'text_error'})
                else:
                    print(f"      ❌ 青空文庫URL取得失敗")
                    results.append({'work_title': work['title'], 'status': 'url_error'})
                    
            except Exception as e:
                print(f"      ❌ エラー: {e}")
                results.append({'work_title': work.title, 'status': 'error', 'error': str(e)})
            
            # API制限対策
            time.sleep(2)
        
        end_time = time.time()
        
        summary = {
            'author_name': author.name,
            'works_processed': len(works),
            'total_places_added': total_places_added,
            'execution_time': round(end_time - start_time, 2),
            'results': results
        }
        
        print(f"\n✅ {author.name} の地名データ拡充完了")
        print(f"   処理作品: {len(works)}作品")
        print(f"   追加地名: {total_places_added}箇所")
        print(f"   実行時間: {summary['execution_time']}秒")
        
        return summary
    
    def test_wikipedia_extraction(self, author_names: List[str] = None) -> Dict:
        """Wikipedia抽出機能のテスト"""
        if not author_names:
            author_names = ["夏目漱石", "森鴎外", "川端康成"]
        
        print(f"\n🧪 **Wikipedia抽出テスト** ({len(author_names)}名)")
        
        results = []
        for author_name in author_names:
            result = self.wiki_extractor.test_extraction(author_name)
            results.append(result)
            
            # 結果表示
            print(f"\n📋 {author_name} の結果:")
            print(f"   Wikipedia URL: {result['author_data']['wikipedia_url']}")
            print(f"   生没年: {result['author_data']['birth_year']} - {result['author_data']['death_year']}")
            print(f"   作品数: {result['works_count']}")
            print(f"   作品: {', '.join(result['works'][:3])}{'...' if len(result['works']) > 3 else ''}")
        
        return {
            'test_authors': author_names,
            'results': results,
            'total_time': sum(r['extraction_time'] for r in results)
        }
    
    def test_aozora_extraction(self, work_samples: List[Dict] = None) -> Dict:
        """青空文庫抽出機能のテスト"""
        if not work_samples:
            work_samples = self.aozora_extractor.get_sample_works()
        
        print(f"\n🌸 **青空文庫抽出テスト** ({len(work_samples)}作品)")
        
        results = []
        for work_info in work_samples:
            result = self.aozora_extractor.test_extraction(work_info)
            results.append(result)
            
            # 結果表示
            print(f"\n📖 {result['author_name']} - {result['title']} の結果:")
            print(f"   成功: {'✅' if result['success'] else '❌'}")
            if result['success']:
                print(f"   テキスト長: {result['text_length']:,}文字")
                print(f"   サンプル: {result['sample_text']}")
            print(f"   実行時間: {result['extraction_time']}秒")
        
        return {
            'test_works': work_samples,
            'results': results,
            'success_rate': sum(1 for r in results if r['success']) / len(results) * 100,
            'total_time': sum(r['extraction_time'] for r in results)
        }
    
    def show_current_status(self) -> Dict:
        """現在のデータベース状況を表示"""
        print(f"\n📊 **現在のデータベース状況**")
        
        authors = self.db.search_authors("", limit=1000)
        total_works = 0
        total_places = 0
        
        for author in authors:
            works = self.db.get_works_by_author(author['author_id'])
            total_works += len(works)
            
            for work in works:
                places = self.db.get_places_by_work(work['work_id'])
                total_places += len(places)
        
        status = {
            'authors_count': len(authors),
            'works_count': total_works,
            'places_count': total_places
        }
        
        print(f"   作者数: {status['authors_count']}名")
        print(f"   作品数: {status['works_count']}作品")
        print(f"   地名数: {status['places_count']}箇所")
        
        # 作者一覧表示
        if authors:
            print(f"\n📝 登録作者一覧:")
            for i, author in enumerate(authors[:10], 1):
                works_count = len(self.db.get_works_by_author(author['author_id']))
                birth_info = f"({author['birth_year']}-{author['death_year']})" if author['birth_year'] else ""
                print(f"   {i:2d}. {author['name']} {birth_info} - {works_count}作品")
            
            if len(authors) > 10:
                print(f"   ... 他{len(authors)-10}名")
        
        return status


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='文豪データ拡充ツール')
    parser.add_argument('command', choices=['authors', 'places', 'test', 'status'], 
                       help='実行コマンド')
    parser.add_argument('--target', type=int, default=30, 
                       help='目標作者数 (authorsコマンド用)')
    parser.add_argument('--author', type=str, 
                       help='対象作者名 (placesコマンド用)')
    parser.add_argument('--force', action='store_true', 
                       help='強制更新')
    parser.add_argument('--test-mode', action='store_true',
                       help='テストモード（少量データで実行）')
    parser.add_argument('--db-path', type=str, default="data/bungo_production.db",
                       help='データベースファイルパス')
    
    args = parser.parse_args()
    
    # エンジン初期化
    engine = DataExpansionEngine(args.db_path)
    
    # コマンド実行
    if args.command == 'authors':
        result = engine.expand_authors(args.target, args.test_mode)
        
    elif args.command == 'places':
        if not args.author:
            print("❌ --author オプションで作者名を指定してください")
            return
        result = engine.expand_places_for_author(args.author, args.force)
        
    elif args.command == 'test':
        result = engine.test_wikipedia_extraction()
        
    elif args.command == 'status':
        result = engine.show_current_status()
    
    print(f"\n🎯 **実行完了**")


if __name__ == "__main__":
    main() 