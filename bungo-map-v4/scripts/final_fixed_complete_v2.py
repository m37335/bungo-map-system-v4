#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗾 青空文庫5作品追加→完全フロー実行（改良版クリーニング対応）

改良版の特徴:
- 改良版テキストクリーニング（rubyタグ、HTMLタグ、注釈除去）
- v3地名抽出システム統合
- AI Geocoding対応
- データベース制約エラー修正
- 包括的エラーハンドリング
"""

import sys
import sqlite3
import requests
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# v3パスを追加
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/bungo_map')

# v3システムをインポート
from bungo_map.extractors.simple_place_extractor import SimplePlaceExtractor
from bungo_map.ai.context_aware_geocoding import ContextAwareGeocodingService

class ImprovedAozora5WorksProcessor:
    """改良版青空文庫5作品処理システム"""
    
    def __init__(self, db_path: str = '/app/bungo-map-v4/data/databases/bungo_v4.db'):
        self.db_path = db_path
        
        print("🗾 青空文庫5作品追加→完全フロー実行（改良版）")
        print("=" * 80)
        
        # v3システム初期化
        self.simple_extractor = SimplePlaceExtractor()
        try:
            self.ai_geocoding = ContextAwareGeocodingService()
            self.geocoding_available = True
            print("✅ AI Geocodingサービス初期化完了")
        except Exception as e:
            print(f"⚠️ AI Geocodingサービス初期化失敗: {e}")
            self.geocoding_available = False
        
        # 対象作品（確実なURL使用）
        self.target_works = [
            {
                'author': '夏目漱石',
                'title': 'こころ',
                'url': 'https://www.aozora.gr.jp/cards/000148/files/773_14560.html'
            },
            {
                'author': '芥川龍之介',
                'title': '羅生門',
                'url': 'https://www.aozora.gr.jp/cards/000879/files/127_15260.html'
            },
            {
                'author': '太宰治',
                'title': '走れメロス',
                'url': 'https://www.aozora.gr.jp/cards/000035/files/1567_14913.html'
            },
            {
                'author': '宮沢賢治',
                'title': '注文の多い料理店',
                'url': 'https://www.aozora.gr.jp/cards/000081/files/43754_17659.html'
            },
            {
                'author': '樋口一葉',
                'title': 'たけくらべ',
                'url': 'https://www.aozora.gr.jp/cards/000064/files/893_14763.html'
            }
        ]
        
        # 改良版テキストクリーニングパターン
        self.cleanup_patterns = [
            # rubyタグ（読み仮名）の適切な処理
            (r'<ruby><rb>([^<]+)</rb><rp>[（(]</rp><rt>([^<]*)</rt><rp>[）)]</rp></ruby>', r'\1（\2）'),
            (r'<ruby><rb>([^<]+)</rb><rp>（</rp><rt>([^<]*)</rt><rp>）</rp></ruby>', r'\1（\2）'),
            (r'<ruby>([^<]+)<rt>([^<]*)</rt></ruby>', r'\1（\2）'),
            
            # HTMLタグ除去
            (r'<br\s*/?\s*>', ''),
            (r'<[^>]+>', ''),
            
            # 青空文庫注釈記号除去
            (r'《[^》]*》', ''),
            (r'［[^］]*］', ''),
            (r'〔[^〕]*〕', ''),
            (r'［＃[^］]*］', ''),
            
            # 底本情報除去
            (r'底本：[^\n]*\n?', ''),
            (r'入力：[^\n]*\n?', ''),
            (r'校正：[^\n]*\n?', ''),
            (r'※[^\n]*\n?', ''),
            (r'初出：[^\n]*\n?', ''),
            
            # XMLヘッダー除去
            (r'<\?xml[^>]*\?>', ''),
            (r'<!DOCTYPE[^>]*>', ''),
            
            # 多重空白・改行の正規化
            (r'\n\s*\n\s*\n+', '\n\n'),
            (r'[ \t]+', ' '),
            (r'　+', '　'),
        ]
        
        # place_typeマッピング（CHECK制約対応）
        self.place_type_mapping = {
            '都道府県': '都道府県',
            '市区町村': '市区町村',
            '有名地名': '有名地名',
            '郡': '郡',
            '歴史地名': '歴史地名',
            'default': '有名地名'
        }
        
        print("✅ 改良版処理システム初期化完了")
    
    def run_complete_flow(self):
        """完全フロー実行"""
        print(f"\n🚀 完全フロー開始: {len(self.target_works)}作品処理")
        print("=" * 80)
        
        results = {
            'processed_works': [],
            'total_sentences': 0,
            'total_places': 0,
            'geocoded_places': 0,
            'errors': []
        }
        
        # 各作品を順次処理
        for i, work_info in enumerate(self.target_works, 1):
            print(f"\n📖 {i}/{len(self.target_works)}: {work_info['author']} - {work_info['title']}")
            print("-" * 60)
            
            try:
                work_result = self._process_single_work(work_info)
                if work_result:
                    results['processed_works'].append(work_result)
                    results['total_sentences'] += work_result.get('sentences_count', 0)
                    results['total_places'] += work_result.get('places_count', 0)
                    results['geocoded_places'] += work_result.get('geocoded_count', 0)
                else:
                    results['errors'].append(f"{work_info['author']} - {work_info['title']}")
            
            except Exception as e:
                print(f"❌ 作品処理エラー: {e}")
                results['errors'].append(f"{work_info['author']} - {work_info['title']}: {str(e)}")
            
            time.sleep(1)  # レート制限
        
        # 最終結果レポート
        self._generate_final_report(results)
        return results
    
    def _process_single_work(self, work_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """単一作品の完全処理"""
        
        # 1. テキスト取得
        print(f"  📄 テキスト取得中...")
        raw_content = self._fetch_aozora_content(work_info['url'])
        if not raw_content:
            print(f"  ❌ テキスト取得失敗")
            return None
        
        print(f"  📄 生テキスト: {len(raw_content):,}文字")
        
        # 2. 改良版クリーニング
        print(f"  🧹 改良版クリーニング実行...")
        cleaned_content = self._clean_aozora_text(raw_content)
        
        # 3. 文分割
        sentences = self._split_into_sentences(cleaned_content)
        print(f"  📝 文分割: {len(sentences)}文")
        
        # 4. データベース格納
        print(f"  💾 データベース格納...")
        work_id = self._store_work_in_database(work_info, cleaned_content, sentences)
        if not work_id:
            print(f"  ❌ データベース格納失敗")
            return None
        
        print(f"  ✅ データベース格納: work_id={work_id}")
        
        # 5. 地名抽出
        print(f"  🗺️ 地名抽出実行...")
        places_count = self._extract_places_for_work(work_id, sentences[:500])  # 最大500文
        print(f"  🗺️ 地名抽出結果: {places_count}件")
        
        # 6. AI Geocoding
        geocoded_count = 0
        if self.geocoding_available:
            print(f"  🌍 AI Geocoding実行...")
            geocoded_count = self._geocode_places_for_work(work_id)
            print(f"  🌍 Geocoding結果: {geocoded_count}件")
        
        return {
            'work_id': work_id,
            'author': work_info['author'],
            'title': work_info['title'],
            'content_length': len(cleaned_content),
            'sentences_count': len(sentences),
            'places_count': places_count,
            'geocoded_count': geocoded_count
        }
    
    def _clean_aozora_text(self, raw_text: str) -> str:
        """改良版青空文庫テキストクリーニング"""
        text = raw_text
        original_length = len(text)
        
        # パターンマッチング処理
        total_cleaned = 0
        for pattern, replacement in self.cleanup_patterns:
            before_count = len(re.findall(pattern, text))
            text = re.sub(pattern, replacement, text)
            total_cleaned += before_count
        
        # 特殊文字の正規化
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        
        # 前後の空白除去
        text = text.strip()
        
        cleaned_length = len(text)
        reduction = original_length - cleaned_length
        print(f"    ✅ クリーニング完了: {cleaned_length:,}文字（{total_cleaned}要素, {reduction:,}文字除去）")
        
        return text
    
    def _fetch_aozora_content(self, url: str) -> str:
        """青空文庫コンテンツ取得"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Shift_JISでデコード
            content = response.content.decode('shift_jis', errors='ignore')
            
            if len(content) < 1000:
                print(f"    ⚠️ コンテンツが短すぎます: {len(content)}文字")
            
            return content
            
        except Exception as e:
            print(f"    ❌ コンテンツ取得エラー: {e}")
            return ""
    
    def _split_into_sentences(self, content: str) -> List[str]:
        """文分割処理"""
        # 句点・疑問符・感嘆符で分割
        sentences = re.split(r'([。！？])', content)
        
        # 分割結果を再構成
        result = []
        for i in range(0, len(sentences)-1, 2):
            if i+1 < len(sentences):
                sentence = sentences[i] + sentences[i+1]
                sentence = sentence.strip()
                if len(sentence) >= 5:  # 短すぎる文は除外
                    result.append(sentence)
        
        return result
    
    def _store_work_in_database(self, work_info: Dict[str, str], content: str, sentences: List[str]) -> Optional[int]:
        """作品をデータベースに格納"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 作家取得/作成
                author_id = self._get_or_create_author(conn, work_info['author'])
                
                # 重複確認
                cursor = conn.execute(
                    "SELECT work_id FROM works WHERE title = ? AND author_id = ?",
                    (work_info['title'], author_id)
                )
                existing = cursor.fetchone()
                if existing:
                    print(f"    ⚠️ 既存作品を更新: work_id={existing[0]}")
                    work_id = existing[0]
                    
                    # 既存データ削除
                    conn.execute("DELETE FROM sentence_places WHERE sentence_id IN (SELECT sentence_id FROM sentences WHERE work_id = ?)", (work_id,))
                    conn.execute("DELETE FROM sentences WHERE work_id = ?", (work_id,))
                    
                    # 作品情報更新
                    conn.execute("""
                        UPDATE works 
                        SET aozora_url = ?, content_length = ?, sentence_count = ?, updated_at = ?
                        WHERE work_id = ?
                    """, (work_info['url'], len(content), len(sentences), datetime.now().isoformat(), work_id))
                else:
                    # 新規作品追加
                    cursor = conn.execute("""
                        INSERT INTO works (title, author_id, aozora_url, content_length, sentence_count, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (work_info['title'], author_id, work_info['url'], len(content), len(sentences), datetime.now().isoformat()))
                    work_id = cursor.lastrowid
                
                # センテンス追加
                for i, sentence_text in enumerate(sentences):
                    before_text = sentences[i-1] if i > 0 else ""
                    after_text = sentences[i+1] if i < len(sentences)-1 else ""
                    
                    conn.execute("""
                        INSERT INTO sentences (
                            sentence_text, work_id, author_id, before_text, after_text,
                            position_in_work, created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        sentence_text, work_id, author_id,
                        before_text[:200], after_text[:200],
                        i + 1, datetime.now().isoformat()
                    ))
                
                conn.commit()
                return work_id
                
        except Exception as e:
            print(f"    ❌ データベース格納エラー: {e}")
            return None
    
    def _get_or_create_author(self, conn: sqlite3.Connection, author_name: str) -> int:
        """作家取得/作成"""
        cursor = conn.execute("SELECT author_id FROM authors WHERE name = ?", (author_name,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        cursor = conn.execute(
            "INSERT INTO authors (name, created_at) VALUES (?, ?)",
            (author_name, datetime.now().isoformat())
        )
        return cursor.lastrowid
    
    def _extract_places_for_work(self, work_id: int, sentences: List[str]) -> int:
        """作品の地名抽出"""
        total_places = 0
        
        try:
            # センテンス情報取得
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT sentence_id, sentence_text, before_text, after_text
                    FROM sentences WHERE work_id = ?
                    ORDER BY position_in_work
                    LIMIT ?
                """, (work_id, len(sentences)))
                sentence_records = cursor.fetchall()
            
            # 地名抽出処理
            for sentence_id, sentence_text, before_text, after_text in sentence_records:
                try:
                    places = self.simple_extractor.extract_places_from_text(work_id, sentence_text)
                    
                    if places:
                        with sqlite3.connect(self.db_path) as conn:
                            for place in places:
                                # place_type決定
                                category = getattr(place, 'category', 'default')
                                place_type = self.place_type_mapping.get(category, '有名地名')
                                
                                # places_masterに追加/取得
                                cursor = conn.execute(
                                    "SELECT place_id FROM places_master WHERE place_name = ?",
                                    (place.place_name,)
                                )
                                result = cursor.fetchone()
                                
                                if result:
                                    place_id = result[0]
                                else:
                                    cursor = conn.execute("""
                                        INSERT INTO places_master (place_name, canonical_name, place_type, confidence)
                                        VALUES (?, ?, ?, ?)
                                    """, (
                                        place.place_name, place.place_name, place_type,
                                        getattr(place, 'confidence', 0.8)
                                    ))
                                    place_id = cursor.lastrowid
                                
                                # sentence_placesに追加（重複チェック）
                                cursor = conn.execute("""
                                    SELECT 1 FROM sentence_places 
                                    WHERE sentence_id = ? AND place_id = ?
                                """, (sentence_id, place_id))
                                
                                if not cursor.fetchone():
                                    conn.execute("""
                                        INSERT INTO sentence_places (
                                            sentence_id, place_id, extraction_method, confidence,
                                            context_before, context_after, matched_text, created_at
                                        )
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        sentence_id, place_id, 'simple',
                                        getattr(place, 'confidence', 0.8),
                                        before_text[:200], after_text[:200], place.place_name,
                                        datetime.now().isoformat()
                                    ))
                                    total_places += 1
                            
                            conn.commit()
                
                except Exception as e:
                    print(f"    ⚠️ センテンス地名抽出エラー: {e}")
                    continue
        
        except Exception as e:
            print(f"    ❌ 地名抽出エラー: {e}")
        
        return total_places
    
    def _geocode_places_for_work(self, work_id: int) -> int:
        """作品関連地名のGeocoding"""
        if not self.geocoding_available:
            return 0
        
        geocoded_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 作品関連の未処理地名取得
                cursor = conn.execute("""
                    SELECT DISTINCT pm.place_id, pm.place_name
                    FROM places_master pm
                    JOIN sentence_places sp ON pm.place_id = sp.place_id
                    JOIN sentences s ON sp.sentence_id = s.sentence_id
                    WHERE s.work_id = ? 
                    AND (pm.latitude IS NULL OR pm.longitude IS NULL)
                    LIMIT 15
                """, (work_id,))
                places_to_geocode = cursor.fetchall()
                
                for place_id, place_name in places_to_geocode:
                    try:
                        # 文脈情報取得
                        cursor = conn.execute("""
                            SELECT s.sentence_text, sp.context_before, sp.context_after
                            FROM sentences s
                            JOIN sentence_places sp ON s.sentence_id = sp.sentence_id
                            WHERE sp.place_id = ? AND s.work_id = ?
                            ORDER BY sp.confidence DESC
                            LIMIT 1
                        """, (place_id, work_id))
                        
                        context = cursor.fetchone()
                        if context:
                            sentence_text, before_text, after_text = context
                        else:
                            sentence_text = before_text = after_text = ""
                        
                        # AI Geocoding実行
                        result = self.ai_geocoding.geocode_place_sync(
                            place_name, sentence_text, before_text, after_text
                        )
                        
                        if result and result.latitude is not None:
                            conn.execute("""
                                UPDATE places_master 
                                SET latitude = ?, longitude = ?, verification_status = 'verified'
                                WHERE place_id = ?
                            """, (result.latitude, result.longitude, place_id))
                            
                            geocoded_count += 1
                            print(f"    🌍 {place_name}: ({result.latitude:.4f}, {result.longitude:.4f})")
                        
                        time.sleep(0.2)  # API制限
                        
                    except Exception as e:
                        print(f"    ⚠️ Geocodingエラー ({place_name}): {e}")
                        continue
                
                conn.commit()
        
        except Exception as e:
            print(f"    ❌ Geocodingエラー: {e}")
        
        return geocoded_count
    
    def _generate_final_report(self, results: Dict[str, Any]):
        """最終結果レポート生成"""
        print(f"\n🎉 完全フロー実行完了!")
        print("=" * 80)
        
        print(f"📊 処理結果:")
        print(f"  ✅ 処理成功: {len(results['processed_works'])}作品")
        print(f"  ❌ 処理失敗: {len(results['errors'])}作品")
        print(f"  📝 総センテンス: {results['total_sentences']:,}")
        print(f"  🗺️ 総地名抽出: {results['total_places']:,}")
        print(f"  🌍 総Geocoding: {results['geocoded_places']:,}")
        
        if results['total_places'] > 0:
            success_rate = (results['geocoded_places'] / results['total_places']) * 100
            print(f"  📈 Geocoding成功率: {success_rate:.1f}%")
        
        if results['processed_works']:
            print(f"\n📖 処理済み作品:")
            for work in results['processed_works']:
                print(f"  • {work['author']} - {work['title']}: {work['sentences_count']}文, {work['places_count']}地名, {work['geocoded_count']}座標")
        
        if results['errors']:
            print(f"\n❌ エラー:")
            for error in results['errors']:
                print(f"  • {error}")
        
        # データベース統計表示
        self._show_database_statistics()
    
    def _show_database_statistics(self):
        """データベース統計表示"""
        print(f"\n📊 データベース統計:")
        print("-" * 40)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 基本統計
                cursor = conn.execute("SELECT COUNT(*) FROM authors")
                authors_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM works")
                works_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM sentences")
                sentences_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM places_master")
                places_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM places_master WHERE latitude IS NOT NULL")
                geocoded_count = cursor.fetchone()[0]
                
                # 頻出地名TOP5
                cursor = conn.execute("""
                    SELECT pm.place_name, COUNT(sp.sentence_id) as mention_count
                    FROM places_master pm
                    LEFT JOIN sentence_places sp ON pm.place_id = sp.place_id
                    GROUP BY pm.place_id
                    HAVING mention_count > 0
                    ORDER BY mention_count DESC
                    LIMIT 5
                """)
                top_places = cursor.fetchall()
                
                print(f"  👥 作家数: {authors_count}")
                print(f"  📚 作品数: {works_count}")
                print(f"  📝 センテンス数: {sentences_count:,}")
                print(f"  🗺️ 地名数: {places_count}")
                print(f"  🌍 座標付き地名: {geocoded_count}")
                
                if top_places:
                    print(f"\n🗺️ 頻出地名TOP5:")
                    for place_name, count in top_places:
                        print(f"  • {place_name}: {count}回")
        
        except Exception as e:
            print(f"❌ 統計表示エラー: {e}")


def main():
    """メイン実行"""
    processor = ImprovedAozora5WorksProcessor()
    results = processor.run_complete_flow()
    
    print(f"\n🏁 全処理完了!")
    return results


if __name__ == "__main__":
    main()