#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Wikipedia Extractor v4 - v3完全移植版
作者・作品情報自動抽出システム
"""

import re
import json
import time
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Wikipedia APIの動的インポート
try:
    import wikipedia
    import requests
    from bs4 import BeautifulSoup
    WIKIPEDIA_AVAILABLE = True
    logger.info("✅ Wikipedia API利用可能")
except ImportError:
    WIKIPEDIA_AVAILABLE = False
    logger.warning("⚠️ Wikipedia未インストール - フォールバック機能で動作")

@dataclass
class AuthorInfo:
    """作者情報"""
    name: str
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    wikipedia_url: str = ""
    summary: str = ""
    biography: str = ""
    image_url: str = ""
    categories: List[str] = None
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = []

@dataclass
class WorkInfo:
    """作品情報"""
    title: str
    author: str
    publication_year: Optional[int] = None
    wikipedia_url: str = ""
    summary: str = ""
    genre: str = ""
    aozora_url: str = ""

class EnhancedWikipediaExtractor:
    """Enhanced Wikipedia Extractor v4 - v3完全移植版"""
    
    def __init__(self):
        """初期化"""
        # Wikipedia設定
        if WIKIPEDIA_AVAILABLE:
            wikipedia.set_lang("ja")
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'BungoMapBot/4.0 (bungo-map-v4@example.com)'
            })
        else:
            self.session = None
        
        # 日本の著名文豪リスト（v3から拡張）
        self.famous_authors = [
            # 明治期
            "夏目漱石", "森鴎外", "樋口一葉", "正岡子規", "石川啄木",
            "尾崎紅葉", "坪内逍遥", "二葉亭四迷", "幸田露伴", "泉鏡花",
            "德冨蘆花", "国木田独歩", "田山花袋", "島崎藤村",
            
            # 大正期
            "芥川龍之介", "谷崎潤一郎", "志賀直哉", "武者小路実篤",
            "有島武郎", "白樺派", "永井荷風", "与謝野晶子", "宮沢賢治",
            
            # 昭和期
            "太宰治", "川端康成", "三島由紀夫", "中島敦", "新美南吉",
            "小林多喜二", "横光利一", "井伏鱒二", "坂口安吾", "織田作之助",
            
            # 現代
            "大江健三郎", "村上春樹", "村上龍", "よしもとばなな", "江國香織"
        ]
        
        # 統計情報
        self.stats = {
            'authors_processed': 0,
            'authors_found': 0,
            'works_extracted': 0,
            'api_requests': 0,
            'errors': 0
        }
        
        logger.info("🚀 Enhanced Wikipedia Extractor v4 初期化完了")
    
    # =============================================================================
    # 1. 作者情報抽出
    # =============================================================================
    
    def extract_author_info(self, author_name: str) -> Optional[AuthorInfo]:
        """作者のWikipedia情報を詳細抽出"""
        if not WIKIPEDIA_AVAILABLE:
            return self._fallback_author_info(author_name)
        
        try:
            logger.info(f"🔍 {author_name} の情報を検索中...")
            self.stats['authors_processed'] += 1
            self.stats['api_requests'] += 1
            
            # Wikipedia検索
            page = wikipedia.page(author_name)
            
            # 基本情報抽出
            summary = page.summary
            birth_year, death_year = self._extract_life_years(summary, page.content)
            image_url = self._extract_image_url(page)
            
            author_info = AuthorInfo(
                name=author_name,
                birth_year=birth_year,
                death_year=death_year,
                wikipedia_url=page.url,
                summary=summary[:500],  # 要約（500文字）
                biography=page.content[:2000],  # 詳細（2000文字）
                image_url=image_url,
                categories=getattr(page, 'categories', [])[:10]  # カテゴリ（最大10個）
            )
            
            self.stats['authors_found'] += 1
            logger.info(f"✅ {author_name} の情報取得成功")
            
            return author_info
            
        except wikipedia.exceptions.DisambiguationError as e:
            # 曖昧さ回避ページの場合、最初の候補を試す
            try:
                logger.info(f"🔄 {author_name} 曖昧さ回避 - 最初の候補を試行")
                page = wikipedia.page(e.options[0])
                
                summary = page.summary
                birth_year, death_year = self._extract_life_years(summary, page.content)
                image_url = self._extract_image_url(page)
                
                author_info = AuthorInfo(
                    name=author_name,
                    birth_year=birth_year,
                    death_year=death_year,
                    wikipedia_url=page.url,
                    summary=summary[:500],
                    biography=page.content[:2000],
                    image_url=image_url,
                    categories=getattr(page, 'categories', [])[:10]
                )
                
                self.stats['authors_found'] += 1
                return author_info
                
            except Exception as e2:
                logger.error(f"⚠️ 曖昧さ回避エラー ({author_name}): {e2}")
                self.stats['errors'] += 1
                
        except wikipedia.exceptions.PageError:
            logger.warning(f"⚠️ ページが見つかりません: {author_name}")
            self.stats['errors'] += 1
            
        except Exception as e:
            logger.error(f"⚠️ Wikipedia検索エラー ({author_name}): {e}")
            self.stats['errors'] += 1
            
        return self._fallback_author_info(author_name)
    
    def _extract_life_years(self, summary: str, content: str) -> Tuple[Optional[int], Optional[int]]:
        """テキストから生年・没年を抽出（v3改良版）"""
        text = summary + " " + content[:2000]  # 最初の部分のみ使用
        
        # より多様なパターンに対応（v3から拡張）
        birth_patterns = [
            r'(\d{4})年.*?月.*?日.*?生',
            r'(\d{4})年.*?生まれ',
            r'生年.*?(\d{4})年',
            r'（(\d{4})年.*?-',
            r'(\d{4})年.*?誕生',
            r'明治(\d+)年.*?生',  # 明治年号
            r'大正(\d+)年.*?生',  # 大正年号
            r'昭和(\d+)年.*?生',  # 昭和年号
            r'(\d{4})年.*?出生',
            r'(\d{4})年.*?月.*?日生',
        ]
        
        death_patterns = [
            r'(\d{4})年.*?月.*?日.*?没',
            r'(\d{4})年.*?死去',
            r'没年.*?(\d{4})年',
            r'-.*?(\d{4})年',
            r'(\d{4})年.*?逝去',
            r'昭和(\d+)年.*?没',  # 昭和年号
            r'(\d{4})年.*?月.*?日没',
            r'(\d{4})年.*?永眠',
        ]
        
        birth_year = self._extract_year_from_patterns(text, birth_patterns)
        death_year = self._extract_year_from_patterns(text, death_patterns)
        
        return birth_year, death_year
    
    def _extract_year_from_patterns(self, text: str, patterns: List[str]) -> Optional[int]:
        """パターンリストから年を抽出（v3改良版）"""
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    year_str = match.group(1)
                    year = int(year_str)
                    
                    # 年号変換（改良版）
                    if '明治' in pattern:
                        year = 1867 + year
                    elif '大正' in pattern:
                        year = 1911 + year
                    elif '昭和' in pattern:
                        year = 1925 + year
                    
                    # 妥当な年の範囲チェック（拡張）
                    if 1800 <= year <= 2100:
                        return year
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_image_url(self, page) -> str:
        """Wikipedia画像URLを抽出"""
        try:
            if hasattr(page, 'images') and page.images:
                # 最初の画像を使用
                return page.images[0]
        except Exception as e:
            logger.debug(f"画像URL抽出エラー: {e}")
        return ""
    
    def _fallback_author_info(self, author_name: str) -> AuthorInfo:
        """フォールバック作者情報"""
        return AuthorInfo(
            name=author_name,
            summary=f"{author_name}の詳細情報は現在取得できません。",
            biography="Wikipedia APIが利用できないため、詳細な経歴情報は取得できません。"
        )
    
    # =============================================================================
    # 2. 作品情報抽出
    # =============================================================================
    
    def extract_works_from_wikipedia(self, author_name: str, content: str = "") -> List[WorkInfo]:
        """Wikipedia本文から作品リストを抽出（v3改良版）"""
        if not content and WIKIPEDIA_AVAILABLE:
            # コンテンツが提供されていない場合、Wikipedia から取得
            try:
                page = wikipedia.page(author_name)
                content = page.content
                self.stats['api_requests'] += 1
            except Exception as e:
                logger.error(f"作品抽出用コンテンツ取得エラー ({author_name}): {e}")
                return self._fallback_works(author_name)
        
        if not content:
            return self._fallback_works(author_name)
        
        works = []
        
        # 作品セクションを探す（v3から拡張）
        sections_to_check = [
            '作品', '主要作品', '代表作', '著作', '小説', '作品一覧',
            '主な作品', '代表的作品', '文学作品', '創作', '著書'
        ]
        
        for section in sections_to_check:
            if section in content:
                # セクション以降のテキストを取得
                start_idx = content.find(section)
                section_text = content[start_idx:start_idx + 3000]  # 3000文字まで
                
                # 作品名と年代を抽出（複数パターン、v3から拡張）
                patterns = [
                    r'『([^』]+)』.*?(\d{4})年',  # 『作品名』...1234年
                    r'(\d{4})年.*?『([^』]+)』',  # 1234年...『作品名』
                    r'『([^』]+)』.*?（(\d{4})年.*?）',  # 『作品名』...（1234年...）
                    r'「([^」]+)」.*?(\d{4})年',  # 「作品名」...1234年
                    r'(\d{4})年.*?「([^」]+)」',  # 1234年...「作品名」
                    r'『([^』]+)』',  # 年代なしの作品名（『』）
                    r'「([^」]+)」'   # 年代なしの作品名（「」）
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, section_text)
                    
                    for match in matches:
                        if len(match) == 2:
                            # 年代付きマッチ
                            if pattern.startswith(r'(\d{4})'):
                                # 年が先の場合
                                year, title = match
                            else:
                                # 作品名が先の場合
                                title, year = match
                            
                            try:
                                pub_year = int(year)
                                if 1800 <= pub_year <= 2100 and self._is_valid_work_title(title):
                                    works.append(WorkInfo(
                                        title=title,
                                        author=author_name,
                                        publication_year=pub_year,
                                        wikipedia_url=f"https://ja.wikipedia.org/wiki/{title}",
                                        genre=self._guess_genre(title)
                                    ))
                                    self.stats['works_extracted'] += 1
                            except ValueError:
                                continue
                                
                        elif len(match) == 1:
                            # 年代なしマッチ
                            title = match if isinstance(match, str) else match[0]
                            if self._is_valid_work_title(title):
                                works.append(WorkInfo(
                                    title=title,
                                    author=author_name,
                                    wikipedia_url=f"https://ja.wikipedia.org/wiki/{title}",
                                    genre=self._guess_genre(title)
                                ))
                                self.stats['works_extracted'] += 1
        
        # 重複除去
        unique_works = []
        seen_titles = set()
        for work in works:
            if work.title not in seen_titles:
                unique_works.append(work)
                seen_titles.add(work.title)
        
        logger.info(f"✅ {author_name} の作品 {len(unique_works)}件を抽出")
        return unique_works[:20]  # 最大20作品
    
    def _is_valid_work_title(self, title: str) -> bool:
        """有効な作品タイトルかチェック"""
        if not title or len(title) < 2 or len(title) > 50:
            return False
        
        # 除外パターン
        exclude_patterns = [
            r'^\d+年$',  # 年のみ
            r'^第\d+',   # 第○章など
            r'参考文献',
            r'外部リンク',
            r'関連項目',
            r'脚注',
            r'出典'
        ]
        
        for pattern in exclude_patterns:
            if re.match(pattern, title):
                return False
        
        return True
    
    def _guess_genre(self, title: str) -> str:
        """作品タイトルからジャンルを推測"""
        genre_keywords = {
            '小説': ['物語', '記', '伝', '譚'],
            '詩': ['詩', '歌', '句'],
            '戯曲': ['劇', '芝居'],
            '随筆': ['随筆', '日記', '手記', '記録'],
            '評論': ['論', '評', '批評', '研究']
        }
        
        for genre, keywords in genre_keywords.items():
            for keyword in keywords:
                if keyword in title:
                    return genre
        
        return '小説'  # デフォルト
    
    def _fallback_works(self, author_name: str) -> List[WorkInfo]:
        """フォールバック作品情報"""
        # 著名作家の代表作（簡易版）
        famous_works = {
            '夏目漱石': ['吾輩は猫である', 'こころ', '坊っちゃん', '三四郎'],
            '芥川龍之介': ['羅生門', '鼻', '蜘蛛の糸', '地獄変'],
            '太宰治': ['人間失格', '走れメロス', '津軽', '斜陽'],
            '川端康成': ['雪国', '伊豆の踊子', '古都', '山の音'],
            '三島由紀夫': ['金閣寺', '仮面の告白', '潮騒', '豊饒の海']
        }
        
        if author_name in famous_works:
            works = []
            for title in famous_works[author_name]:
                works.append(WorkInfo(
                    title=title,
                    author=author_name,
                    genre='小説'
                ))
            return works
        
        return []
    
    # =============================================================================
    # 3. バッチ処理・統計機能
    # =============================================================================
    
    def process_authors_batch(self, author_names: List[str], 
                            include_works: bool = True,
                            delay: float = 1.0) -> Dict[str, Any]:
        """作者リストのバッチ処理"""
        results = {
            'authors': [],
            'works': [],
            'statistics': {},
            'errors': []
        }
        
        logger.info(f"📚 {len(author_names)}名の作者をバッチ処理開始")
        
        for i, author_name in enumerate(author_names, 1):
            try:
                logger.info(f"処理中 ({i}/{len(author_names)}): {author_name}")
                
                # 作者情報取得
                author_info = self.extract_author_info(author_name)
                if author_info:
                    results['authors'].append(asdict(author_info))
                
                # 作品情報取得（オプション）
                if include_works and author_info:
                    works = self.extract_works_from_wikipedia(author_name)
                    for work in works:
                        results['works'].append(asdict(work))
                
                # API制限対策
                if WIKIPEDIA_AVAILABLE and delay > 0:
                    time.sleep(delay)
                
            except Exception as e:
                error_msg = f"{author_name}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(f"バッチ処理エラー: {error_msg}")
        
        # 統計情報
        results['statistics'] = self.get_stats()
        
        logger.info(f"✅ バッチ処理完了: 作者{len(results['authors'])}名、作品{len(results['works'])}件")
        
        return results
    
    def get_famous_authors_list(self) -> List[str]:
        """著名作家リストを取得"""
        return self.famous_authors.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報取得"""
        return {
            'extractor_stats': self.stats.copy(),
            'availability': {
                'wikipedia_api': WIKIPEDIA_AVAILABLE,
                'requests_session': bool(self.session)
            },
            'famous_authors_count': len(self.famous_authors)
        }
    
    # =============================================================================
    # 4. テスト・検証機能
    # =============================================================================
    
    def test_extraction(self, author_name: str = "夏目漱石") -> Dict[str, Any]:
        """抽出機能のテスト"""
        logger.info(f"🧪 Wikipedia抽出テスト開始: {author_name}")
        
        test_results = {
            'author_name': author_name,
            'author_info': None,
            'works': [],
            'success': False,
            'error': None
        }
        
        try:
            # 作者情報テスト
            author_info = self.extract_author_info(author_name)
            if author_info:
                test_results['author_info'] = asdict(author_info)
                
                # 作品情報テスト
                works = self.extract_works_from_wikipedia(author_name)
                test_results['works'] = [asdict(work) for work in works]
                
                test_results['success'] = True
                logger.info(f"✅ テスト成功: 作者情報取得、作品{len(works)}件抽出")
            else:
                test_results['error'] = "作者情報の取得に失敗"
                logger.warning(f"⚠️ テスト部分失敗: 作者情報取得失敗")
        
        except Exception as e:
            test_results['error'] = str(e)
            logger.error(f"❌ テストエラー: {e}")
        
        return test_results

def main():
    """テスト実行"""
    print("🚀 Enhanced Wikipedia Extractor v4 テスト開始")
    
    # 抽出器初期化
    extractor = EnhancedWikipediaExtractor()
    
    # 単一作者テスト
    print("\n📚 単一作者テスト")
    test_result = extractor.test_extraction("夏目漱石")
    
    if test_result['success']:
        print("✅ 単一作者テスト成功")
        author_info = test_result['author_info']
        print(f"   作者: {author_info['name']}")
        print(f"   生年: {author_info['birth_year']}")
        print(f"   没年: {author_info['death_year']}")
        print(f"   作品数: {len(test_result['works'])}")
        
        if test_result['works']:
            print("   代表作:")
            for work in test_result['works'][:3]:
                year = f"({work['publication_year']}年)" if work['publication_year'] else ""
                print(f"     - {work['title']} {year}")
    else:
        print(f"❌ 単一作者テスト失敗: {test_result['error']}")
    
    # バッチ処理テスト
    print("\n📚 バッチ処理テスト")
    test_authors = ["芥川龍之介", "太宰治", "川端康成"]
    batch_result = extractor.process_authors_batch(test_authors, include_works=True, delay=0.5)
    
    print(f"✅ バッチ処理完了")
    print(f"   処理作者数: {len(batch_result['authors'])}")
    print(f"   抽出作品数: {len(batch_result['works'])}")
    print(f"   エラー数: {len(batch_result['errors'])}")
    
    # 統計表示
    print("\n📊 統計情報")
    stats = extractor.get_stats()
    for key, value in stats['extractor_stats'].items():
        print(f"   {key}: {value}")
    
    print("\n🎉 Enhanced Wikipedia Extractor v4 テスト完了")

if __name__ == "__main__":
    main() 