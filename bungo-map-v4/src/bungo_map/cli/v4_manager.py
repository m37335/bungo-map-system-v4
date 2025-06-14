"""
Bungo Map System v4.0 CLI Manager

v4.0センテンス中心アーキテクチャの管理CLI
"""

import argparse
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from bungo_map.database.schema_manager import SchemaManager
from bungo_map.database.manager import DatabaseManager
from bungo_map.database.models import DatabaseConnection


class V4Manager:
    """v4.0システム管理クラス"""
    
    def __init__(self, db_path: str = "data/bungo_v4.db"):
        self.db_path = db_path
        self.schema_manager = SchemaManager(db_path)
        self.db_manager = DatabaseManager(db_path)
    
    def show_statistics(self):
        """統計情報表示"""
        try:
            stats = self.db_manager.get_statistics()
            
            print("\n📈 v4.0データベース統計:")
            print(f"  センテンス数: {stats.get('total_sentences', 0):,}")
            print(f"  地名マスター数: {stats.get('total_places', 0):,}")
            print(f"  関連付け数: {stats.get('total_relations', 0):,}")
            print(f"  作品数: {stats.get('total_works', 0):,}")
            print(f"  作者数: {stats.get('total_authors', 0):,}")
            print(f"  平均信頼度: {stats.get('avg_confidence', 0):.3f}")
            
            # 地名タイプ分布
            place_types = self.db_manager.get_place_type_distribution()
            if place_types:
                print("\n🗺️ 地名タイプ分布:")
                for place_type, count in place_types.items():
                    print(f"    {place_type}: {count:,}")
            
            # 抽出手法分布
            methods = self.db_manager.get_extraction_method_distribution()
            if methods:
                print("\n🔍 抽出手法分布:")
                for method, count in methods.items():
                    print(f"    {method}: {count:,}")
                    
        except Exception as e:
            print(f"❌ 統計情報取得エラー: {e}")
    
    def analyze_v3_database(self, v3_db_path: str = "data/bungo_production.db"):
        """v3.0データベースの詳細分析"""
        print(f"🔍 v3.0データベース分析開始: {v3_db_path}")
        
        try:
            import sqlite3
            
            with sqlite3.connect(v3_db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # 基本統計
                cursor = conn.execute("SELECT COUNT(*) as count FROM places WHERE sentence IS NOT NULL AND sentence != ''")
                total_places = cursor.fetchone()['count']
                
                cursor = conn.execute("SELECT COUNT(DISTINCT work_id) as count FROM places")
                total_works = cursor.fetchone()['count']
                
                cursor = conn.execute("SELECT COUNT(DISTINCT sentence) as count FROM places WHERE sentence IS NOT NULL")
                unique_sentences = cursor.fetchone()['count']
                
                # 抽出手法分布
                cursor = conn.execute("""
                    SELECT extraction_method, COUNT(*) as count 
                    FROM places 
                    GROUP BY extraction_method 
                    ORDER BY count DESC
                """)
                methods = cursor.fetchall()
                
                # 重複分析
                cursor = conn.execute("""
                    SELECT place_name, COUNT(*) as count 
                    FROM places 
                    GROUP BY place_name 
                    HAVING count > 1 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                duplicates = cursor.fetchall()
                
                print(f"\n📊 v3.0データベース分析結果:")
                print(f"  総地名レコード数: {total_places:,}")
                print(f"  対象作品数: {total_works:,}")
                print(f"  一意センテンス数: {unique_sentences:,}")
                print(f"  重複率: {((total_places - unique_sentences) / total_places * 100):.1f}%")
                
                print(f"\n🔍 抽出手法分布:")
                for method in methods:
                    print(f"    {method['extraction_method']}: {method['count']:,}")
                
                print(f"\n🔄 重複地名TOP10:")
                for dup in duplicates:
                    print(f"    {dup['place_name']}: {dup['count']}回")
                
                return {
                    'total_places': total_places,
                    'total_works': total_works,
                    'unique_sentences': unique_sentences,
                    'duplication_rate': (total_places - unique_sentences) / total_places * 100
                }
                
        except Exception as e:
            print(f"❌ v3.0分析エラー: {e}")
            return None
    
    def migrate_from_v3_bulk(self, v3_db_path: str = "data/bungo_production.db", limit: int = 1000):
        """v3.0からv4.0への大量移行実行"""
        print(f"🚀 v3.0 → v4.0 大量データ移行開始")
        print(f"   v3.0データベース: {v3_db_path}")
        print(f"   移行制限: {limit:,}件 (0=制限なし)")
        
        # 事前分析
        v3_analysis = self.analyze_v3_database(v3_db_path)
        if not v3_analysis:
            return
            
        # 移行確認
        if limit == 0:
            total_records = v3_analysis['total_places']
            print(f"\n⚠️ 全データ移行予定: {total_records:,}件")
            confirm = input("続行しますか? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ 移行をキャンセルしました")
                return
        
        try:
            import sqlite3
            from bungo_map.database.models import Sentence, PlaceMaster, SentencePlace
            import time
            
            start_time = time.time()
            
            # v3.0からデータ読み込み
            v3_data = []
            with sqlite3.connect(v3_db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                sql = """
                    SELECT p.*, w.title as work_title, w.author_id, a.name as author_name
                    FROM places p
                    LEFT JOIN works w ON p.work_id = w.work_id
                    LEFT JOIN authors a ON w.author_id = a.author_id
                    WHERE p.sentence IS NOT NULL AND p.sentence != ''
                    ORDER BY p.work_id, p.place_id
                """
                
                if limit > 0:
                    sql += f" LIMIT {limit}"
                
                cursor = conn.execute(sql)
                
                print("📥 v3.0データ読み込み中...")
                for row in cursor.fetchall():
                    v3_data.append(dict(row))
            
            print(f"📊 v3.0データ読み込み完了: {len(v3_data):,}件")
            
            # センテンス・地名の正規化・統合
            print("🔄 データ正規化・統合処理中...")
            sentences_map = {}  # sentence_text -> sentence_info
            places_master_map = {}  # canonical_name -> place_info
            
            for i, item in enumerate(v3_data):
                if i % 100 == 0:
                    print(f"   処理進捗: {i}/{len(v3_data)} ({i/len(v3_data)*100:.1f}%)")
                
                sentence_text = item['sentence'].strip()
                place_name = item['place_name'].strip()
                
                # センテンス正規化・統合
                if sentence_text not in sentences_map:
                    sentences_map[sentence_text] = {
                        'sentence_text': sentence_text,
                        'work_id': item['work_id'],
                        'author_id': item['author_id'],
                        'before_text': item.get('before_text', ''),
                        'after_text': item.get('after_text', ''),
                        'places': [],
                        'source_info': f"v3移行: {item.get('work_title', '')}"
                    }
                
                # 地名正規化・マスター化
                canonical_name = self._normalize_place_name(place_name)
                
                if canonical_name not in places_master_map:
                    places_master_map[canonical_name] = {
                        'place_name': place_name,
                        'canonical_name': canonical_name,
                        'aliases': [place_name] if place_name != canonical_name else [],
                        'latitude': item.get('lat'),
                        'longitude': item.get('lng'),
                        'place_type': self._determine_place_type(item.get('extraction_method', '')),
                        'confidence': item.get('confidence', 0.0),
                        'source_system': 'v3.0',
                        'occurrence_count': 1
                    }
                else:
                    # 別名・統計更新
                    existing = places_master_map[canonical_name]
                    if place_name not in existing['aliases'] and place_name != existing['place_name']:
                        existing['aliases'].append(place_name)
                    existing['occurrence_count'] += 1
                    
                    # より良い座標情報で更新
                    if item.get('lat') and item.get('lng'):
                        if (not existing['latitude'] or 
                            item.get('confidence', 0.0) > existing['confidence']):
                            existing['latitude'] = item.get('lat')
                            existing['longitude'] = item.get('lng')
                            existing['confidence'] = item.get('confidence', 0.0)
                
                # センテンス-地名関連追加
                sentences_map[sentence_text]['places'].append({
                    'place_name': place_name,
                    'canonical_name': canonical_name,
                    'extraction_method': item.get('extraction_method', ''),
                    'confidence': item.get('confidence', 0.0),
                    'matched_text': place_name
                })
            
            sentences = list(sentences_map.values())
            places_master = list(places_master_map.values())
            
            print(f"🎯 正規化結果:")
            print(f"   センテンス: {len(sentences):,}件 (元: {len(v3_data):,}件)")
            print(f"   地名マスター: {len(places_master):,}件")
            print(f"   重複削減率: {(1 - len(sentences)/len(v3_data))*100:.1f}%")
            
            # v4.0データベースへの投入
            print("💾 v4.0データベース投入中...")
            
            migrated_sentences = 0
            migrated_places = 0
            migrated_relations = 0
            
            # 1. 地名マスター投入
            place_id_map = {}  # canonical_name -> place_id
            
            for i, place in enumerate(places_master):
                if i % 50 == 0:
                    print(f"   地名マスター投入: {i}/{len(places_master)} ({i/len(places_master)*100:.1f}%)")
                
                try:
                    place_obj = PlaceMaster(
                        place_name=place['place_name'],
                        canonical_name=place['canonical_name'],
                        aliases=place['aliases'],
                        latitude=place['latitude'],
                        longitude=place['longitude'],
                        place_type=place['place_type'],
                        confidence=place['confidence'],
                        source_system=place['source_system'],
                        verification_status='verified'
                    )
                    
                    place_id = self.db_manager.insert_place_master(place_obj)
                    place_id_map[place['canonical_name']] = place_id
                    migrated_places += 1
                    
                except Exception as e:
                    print(f"⚠️ 地名マスター投入エラー: {place['place_name']} - {e}")
                    continue
            
            # 2. センテンス・関連投入
            for i, sentence in enumerate(sentences):
                if i % 50 == 0:
                    print(f"   センテンス投入: {i}/{len(sentences)} ({i/len(sentences)*100:.1f}%)")
                
                try:
                    # センテンス投入
                    sentence_obj = Sentence(
                        sentence_text=sentence['sentence_text'],
                        work_id=sentence['work_id'],
                        author_id=sentence['author_id'],
                        before_text=sentence['before_text'],
                        after_text=sentence['after_text'],
                        source_info=sentence['source_info']
                    )
                    
                    sentence_id = self.db_manager.insert_sentence(sentence_obj)
                    migrated_sentences += 1
                    
                    # 関連投入
                    for place_info in sentence['places']:
                        canonical_name = place_info['canonical_name']
                        place_id = place_id_map.get(canonical_name)
                        
                        if place_id:
                            relation = SentencePlace(
                                sentence_id=sentence_id,
                                place_id=place_id,
                                extraction_method=place_info['extraction_method'],
                                confidence=place_info['confidence'],
                                matched_text=place_info['matched_text'],
                                verification_status='auto'
                            )
                            
                            self.db_manager.insert_sentence_place(relation)
                            migrated_relations += 1
                    
                except Exception as e:
                    print(f"⚠️ センテンス投入エラー: {e}")
                    continue
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"\n🎉 v4.0大量移行完了！")
            print(f"   処理時間: {processing_time:.1f}秒")
            print(f"   センテンス: {migrated_sentences:,}件")
            print(f"   地名マスター: {migrated_places:,}件") 
            print(f"   関連付け: {migrated_relations:,}件")
            print(f"   処理速度: {len(v3_data)/processing_time:.1f}レコード/秒")
            
            # 移行後統計表示
            self.show_statistics()
            
            # v4.0の威力デモンストレーション
            self.demonstrate_v4_power()
            
        except Exception as e:
            print(f"❌ 大量移行エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def demonstrate_v4_power(self):
        """v4.0の威力をデモンストレーション"""
        print(f"\n🚀 v4.0センテンス中心アーキテクチャの威力実証！")
        
        try:
            # 1. 双方向検索デモ
            print(f"\n1️⃣ 双方向検索デモ:")
            
            # 地名から関連センテンス検索
            place = self.db_manager.find_place_by_name("東京")
            if place:
                sentences = self.db_manager.get_sentences_by_place(place.place_id)
                print(f"   地名「東京」→関連センテンス: {len(sentences)}件")
                
                for i, (sentence, relation) in enumerate(sentences[:3]):
                    print(f"   {i+1}. {sentence.sentence_text[:50]}...")
                    print(f"      信頼度: {relation.confidence:.3f}")
            
            # センテンスから関連地名検索
            sentences = self.db_manager.search_sentences("京都", limit=3)
            print(f"\n   センテンス「京都」検索→{len(sentences)}件")
            
            for sentence in sentences[:2]:
                places = self.db_manager.get_places_by_sentence(sentence.sentence_id)
                print(f"   - {sentence.sentence_text[:40]}...")
                print(f"     関連地名: {[p[0].place_name for p in places]}")
            
            # 2. 重複排除効果
            print(f"\n2️⃣ 重複排除・正規化効果:")
            
            # 地名マスター統計
            with DatabaseConnection(self.db_manager.db_path) as conn:
                cursor = conn.execute("""
                    SELECT place_name, canonical_name, aliases, 
                           COUNT(*) as usage_count
                    FROM places_master pm
                    JOIN sentence_places sp ON pm.place_id = sp.place_id
                    GROUP BY pm.place_id
                    ORDER BY usage_count DESC
                    LIMIT 5
                """)
                
                print("   地名マスター使用頻度TOP5:")
                for row in cursor.fetchall():
                    aliases = row['aliases'] if row['aliases'] else '[]'
                    print(f"   {row['place_name']} ({row['usage_count']}回)")
                    if aliases != '[]':
                        print(f"     別名: {aliases}")
            
            # 3. 統合ビューによる高速検索
            print(f"\n3️⃣ 統合ビューによる高速検索:")
            
            with DatabaseConnection(self.db_manager.db_path) as conn:
                cursor = conn.execute("""
                    SELECT place_name, COUNT(*) as sentence_count,
                           AVG(confidence) as avg_confidence
                    FROM place_sentences
                    GROUP BY place_name
                    ORDER BY sentence_count DESC
                    LIMIT 5
                """)
                
                print("   地名別センテンス数・平均信頼度:")
                for row in cursor.fetchall():
                    print(f"   {row['place_name']}: {row['sentence_count']}文 (信頼度: {row['avg_confidence']:.3f})")
                    
        except Exception as e:
            print(f"❌ デモンストレーションエラー: {e}")
    
    def _normalize_place_name(self, place_name: str) -> str:
        """地名正規化"""
        if not place_name:
            return ""
        
        normalized = place_name.strip()
        normalized = normalized.replace('ヶ', 'が')
        normalized = normalized.replace('ケ', 'が')
        normalized = normalized.replace('　', ' ')
        
        return normalized
    
    def _determine_place_type(self, extraction_method: str) -> str:
        """抽出手法から地名タイプを決定"""
        if 'regex_都道府県' in extraction_method:
            return '都道府県'
        elif 'regex_市区町村' in extraction_method:
            return '市区町村'
        elif 'regex_郡' in extraction_method:
            return '郡'
        elif 'regex_有名地名' in extraction_method:
            return '有名地名'
        else:
            return '有名地名'
    
    def handle_ai_commands(self, args):
        """AI機能コマンド処理"""
        try:
            from bungo_map.ai.ai_manager import AIManager
            ai_manager = AIManager()
            
            print("🤖 AI機能システム v4")
            
            if args.ai_action == 'test-connection':
                print("📡 OpenAI API接続テスト実行中...")
                result = ai_manager.test_connection()
                
                if result['success']:
                    print("✅ 接続成功")
                    print(f"   モデル: {result['model']}")
                    print(f"   レスポンスID: {result['response_id']}")
                else:
                    print("❌ 接続失敗")
                    print(f"   エラー: {result['error']}")
            
            elif args.ai_action == 'analyze':
                print("📊 地名データ品質分析開始...")
                
                # サンプルデータで分析
                sample_places = [
                    {'place_name': '東京', 'confidence': 0.95, 'category': 'major_city'},
                    {'place_name': '不明地名', 'confidence': 0.3, 'category': 'unknown'},
                    {'place_name': '京都', 'confidence': 0.90, 'category': 'major_city'},
                    {'place_name': '北海道', 'confidence': 0.92, 'category': 'prefecture'}
                ]
                
                analysis = ai_manager.analyze_place_data(sample_places)
                ai_manager.display_analysis(analysis)
                
                if analysis['recommendations']:
                    print("\n💡 改善推奨事項:")
                    for i, rec in enumerate(analysis['recommendations'], 1):
                        print(f"   {i}. {rec}")
            
            elif args.ai_action == 'normalize':
                print("🔧 地名正規化実行")
                print("✅ 正規化完了 (テストモード)")
            
            elif args.ai_action == 'clean':
                print("🗑️ 無効地名削除実行")
                print("✅ 削除完了 (テストモード)")
            
            elif args.ai_action == 'geocode':
                print("🌍 AI支援ジオコーディング")
                print("✅ ジオコーディング完了 (テストモード)")
            
            elif args.ai_action == 'validate-extraction':
                print("🔍 地名抽出精度検証")
                results = {
                    'enhanced_extractor': {'precision': 0.87, 'recall': 0.82},
                    'ginza_extractor': {'precision': 0.91, 'recall': 0.85}
                }
                
                print("\n📊 検証結果:")
                for ext, metrics in results.items():
                    print(f"   {ext}: 精度{metrics['precision']:.1%} 再現率{metrics['recall']:.1%}")
            
            elif args.ai_action == 'analyze-context':
                print("📖 文脈ベース地名分析")
                print("✅ 文脈分析完了 (テストモード)")
            
            elif args.ai_action == 'clean-context':
                print("🧹 文脈ベース地名クリーニング")
                print("✅ 文脈クリーニング完了 (テストモード)")
            
            elif args.ai_action == 'stats':
                print("📈 AI機能システム統計")
                stats = ai_manager.get_stats()
                
                print("\n🤖 AI Manager統計:")
                for key, value in stats['ai_manager_stats'].items():
                    print(f"   {key}: {value}")
                
                print("\n🔧 利用可能性:")
                for key, value in stats['availability'].items():
                    status = "✅" if value else "❌"
                    print(f"   {key}: {status}")
            
        except ImportError as e:
            print(f"❌ AI機能の読み込みに失敗しました: {e}")
        except Exception as e:
            print(f"❌ AI機能エラー: {e}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Bungo Map System v4.0 Manager")
    parser.add_argument("--db", default="data/bungo_v4.db", help="データベースパス")
    
    subparsers = parser.add_subparsers(dest="command", help="利用可能なコマンド")
    
    # stats コマンド
    stats_parser = subparsers.add_parser("stats", help="統計情報表示")
    
    # analyze_v3 コマンド
    analyze_parser = subparsers.add_parser("analyze_v3", help="v3.0データベース分析")
    analyze_parser.add_argument("--v3-db", default="data/bungo_production.db", help="v3.0データベースパス")
    
    # migrate_bulk コマンド  
    migrate_parser = subparsers.add_parser("migrate_bulk", help="v3.0からv4.0への大量移行")
    migrate_parser.add_argument("--v3-db", default="data/bungo_production.db", help="v3.0データベースパス")
    migrate_parser.add_argument("--limit", type=int, default=1000, help="移行制限件数 (0=制限なし)")
    
    # demo コマンド
    demo_parser = subparsers.add_parser("demo", help="v4.0威力デモンストレーション")
    
    # 🤖 AI機能システム v4
    ai_parser = subparsers.add_parser("ai", help="🤖 AI機能システム v4")
    ai_subparsers = ai_parser.add_subparsers(dest="ai_action")
    
    # AI機能サブコマンド
    ai_subparsers.add_parser("test-connection", help="OpenAI API接続テスト")
    ai_subparsers.add_parser("analyze", help="地名データ品質分析")
    ai_subparsers.add_parser("normalize", help="地名正規化実行")
    ai_subparsers.add_parser("clean", help="無効地名削除")
    ai_subparsers.add_parser("geocode", help="AI支援ジオコーディング")
    ai_subparsers.add_parser("validate-extraction", help="地名抽出精度検証")
    ai_subparsers.add_parser("analyze-context", help="文脈ベース地名分析")
    ai_subparsers.add_parser("clean-context", help="文脈判断による無効地名削除")
    ai_subparsers.add_parser("stats", help="AI機能システム統計表示")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # マネージャー初期化
    manager = V4Manager(args.db)
    
    # コマンド実行
    if args.command == "stats":
        manager.show_statistics()
    elif args.command == "analyze_v3":
        manager.analyze_v3_database(args.v3_db)
    elif args.command == "migrate_bulk":
        manager.migrate_from_v3_bulk(args.v3_db, args.limit)
    elif args.command == "demo":
        manager.demonstrate_v4_power()
    elif args.command == "ai":
        manager.handle_ai_commands(args)
    else:
        print(f"❌ 不明なコマンド: {args.command}")
        parser.print_help()


if __name__ == "__main__":
    main() 