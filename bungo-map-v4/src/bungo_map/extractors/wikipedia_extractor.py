#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wikipedia 作者・作品情報抽出器
強化版 - 実際にWikipediaから情報を取得
"""

import re
import requests
import wikipedia
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime

from ..database.models import Author, Work


class WikipediaExtractor:
    """Wikipedia から作者・作品情報を抽出"""
    
    def __init__(self):
        # Wikipedia言語設定
        wikipedia.set_lang("ja")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BungoMapBot/2.0 (bungo-map@example.com)'
        })
        
        # 日本の著名文豪リスト
        self.famous_authors = [
            "夏目漱石", "森鴎外", "芥川龍之介", "太宰治", "川端康成", 
            "三島由紀夫", "谷崎潤一郎", "志賀直哉", "島崎藤村", "樋口一葉",
            "正岡子規", "石川啄木", "与謝野晶子", "宮沢賢治", "中島敦",
            "永井荷風", "田山花袋", "国木田独歩", "尾崎紅葉", "坪内逍遥",
            "二葉亭四迷", "幸田露伴", "泉鏡花", "德冨蘆花", "有島武郎",
            "武者小路実篤", "白樺派", "新美南吉", "小林多喜二", "横光利一"
        ]
        
    def search_author(self, author_name: str) -> Optional[Dict]:
        """作者のWikipedia情報を詳細検索"""
        try:
            print(f"🔍 {author_name} の情報を検索中...")
            
            # Wikipedia検索
            page = wikipedia.page(author_name)
            
            # 基本情報抽出
            extract = page.summary
            birth_year, death_year = self._extract_life_years(extract, page.content)
            
            return {
                'title': page.title,
                'url': page.url,
                'extract': extract[:500],  # 要約（500文字）
                'content': page.content,
                'birth_year': birth_year,
                'death_year': death_year,
                'categories': page.categories if hasattr(page, 'categories') else []
            }
            
        except wikipedia.exceptions.DisambiguationError as e:
            # 曖昧さ回避ページの場合、最初の候補を試す
            try:
                page = wikipedia.page(e.options[0])
                extract = page.summary
                birth_year, death_year = self._extract_life_years(extract, page.content)
                
                return {
                    'title': page.title,
                    'url': page.url,
                    'extract': extract[:500],
                    'content': page.content,
                    'birth_year': birth_year,
                    'death_year': death_year,
                    'categories': page.categories if hasattr(page, 'categories') else []
                }
            except Exception as e2:
                print(f"⚠️ 曖昧さ回避エラー ({author_name}): {e2}")
                
        except wikipedia.exceptions.PageError:
            print(f"⚠️ ページが見つかりません: {author_name}")
            
        except Exception as e:
            print(f"⚠️ Wikipedia検索エラー ({author_name}): {e}")
            
        return None
    
    def _extract_life_years(self, summary: str, content: str) -> Tuple[Optional[int], Optional[int]]:
        """テキストから生年・没年を抽出（改良版）"""
        # より多様なパターンに対応
        text = summary + " " + content[:2000]  # 最初の部分のみ使用
        
        birth_patterns = [
            r'(\d{4})年.*?月.*?日.*?生',
            r'(\d{4})年.*?生まれ',
            r'生年.*?(\d{4})年',
            r'（(\d{4})年.*?-',
            r'(\d{4})年.*?誕生',
            r'明治(\d+)年',  # 明治年号
            r'大正(\d+)年',  # 大正年号
            r'昭和(\d+)年.*?生',  # 昭和年号
        ]
        
        death_patterns = [
            r'(\d{4})年.*?月.*?日.*?没',
            r'(\d{4})年.*?死去',
            r'没年.*?(\d{4})年',
            r'-.*?(\d{4})年',
            r'(\d{4})年.*?逝去',
            r'昭和(\d+)年.*?没',  # 昭和年号
        ]
        
        birth_year = self._extract_year_from_patterns(text, birth_patterns)
        death_year = self._extract_year_from_patterns(text, death_patterns)
        
        return birth_year, death_year
    
    def _extract_year_from_patterns(self, text: str, patterns: List[str]) -> Optional[int]:
        """パターンリストから年を抽出"""
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    year_str = match.group(1)
                    year = int(year_str)
                    
                    # 年号変換（簡易版）
                    if pattern.startswith(r'明治'):
                        year = 1867 + year
                    elif pattern.startswith(r'大正'):
                        year = 1911 + year
                    elif pattern.startswith(r'昭和'):
                        year = 1925 + year
                    
                    # 妥当な年の範囲チェック
                    if 1800 <= year <= 2100:
                        return year
                except (ValueError, IndexError):
                    continue
        return None
    
    def extract_works_from_wikipedia(self, author_name: str, content: str) -> List[Dict]:
        """Wikipedia本文から作品リストを抽出（制作年代付き）"""
        works = []
        
        # 作品セクションを探す
        content_lower = content.lower()
        sections_to_check = ['作品', '主要作品', '代表作', '著作', '小説', '作品一覧']
        
        for section in sections_to_check:
            if section in content:
                # セクション以降のテキストを取得
                start_idx = content.find(section)
                section_text = content[start_idx:start_idx + 3000]  # 3000文字まで
                
                # 作品名と年代を抽出（複数パターン）
                patterns = [
                    r'『([^』]+)』.*?(\d{4})年',  # 『作品名』...1234年
                    r'(\d{4})年.*?『([^』]+)』',  # 1234年...『作品名』
                    r'『([^』]+)』.*?（(\d{4})年.*?）',  # 『作品名』...（1234年...）
                    r'『([^』]+)』'  # 年代なしの作品名
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
                                if 1800 <= pub_year <= 2100 and len(title) > 1 and len(title) < 50:
                                    works.append({
                                        'title': title,
                                        'wiki_url': f"https://ja.wikipedia.org/wiki/{title}",
                                        'publication_year': pub_year
                                    })
                            except ValueError:
                                continue
                                
                        elif len(match) == 1:
                            # 年代なしマッチ
                            title = match if isinstance(match, str) else match[0]
                            if len(title) > 1 and len(title) < 50:
                                works.append({
                                    'title': title,
                                    'wiki_url': f"https://ja.wikipedia.org/wiki/{title}",
                                    'publication_year': None
                                })
        
        # 重複除去と制限
        seen = set()
        unique_works = []
        for work in works:
            if work['title'] not in seen:
                seen.add(work['title'])
                unique_works.append(work)
                if len(unique_works) >= 15:  # 最大15作品
                    break
        
        print(f"📚 {author_name} の作品を {len(unique_works)} 作品抽出しました")
        return unique_works
    
    def _extract_publication_year_from_text(self, work_title: str, content: str) -> Optional[int]:
        """作品の制作年代をWikipediaから抽出"""
        # 作品名周辺のテキストから年代を抽出
        patterns = [
            rf'{re.escape(work_title)}.*?(\d{{4}})年',
            rf'(\d{{4}})年.*?{re.escape(work_title)}',
            rf'『{re.escape(work_title)}』.*?(\d{{4}})年',
            rf'(\d{{4}})年.*?『{re.escape(work_title)}』'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                try:
                    year = int(match.group(1))
                    if 1800 <= year <= 2100:
                        return year
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def get_author_works(self, author_name: str, content: str = "", limit: int = 10) -> List[Dict]:
        """作者の作品リストを取得（Wikipedia から実際に抽出）"""
        # Wikipedia本文から抽出を試行
        if content:
            extracted_works = self.extract_works_from_wikipedia(author_name, content)
            if extracted_works:
                return extracted_works[:limit]
        
        # フォールバック: 既知の作品データ
        fallback_works = self._get_fallback_works(author_name)
        return fallback_works[:limit]
    
    def _get_fallback_works(self, author_name: str) -> List[Dict]:
        """フォールバック用の既知作品データ（制作年代付き）"""
        famous_works = {
            "夏目漱石": [
                {"title": "坊っちゃん", "wiki_url": "https://ja.wikipedia.org/wiki/坊っちゃん", "publication_year": 1906},
                {"title": "吾輩は猫である", "wiki_url": "https://ja.wikipedia.org/wiki/吾輩は猫である", "publication_year": 1905},
                {"title": "こころ", "wiki_url": "https://ja.wikipedia.org/wiki/こころ_(小説)", "publication_year": 1914},
                {"title": "三四郎", "wiki_url": "https://ja.wikipedia.org/wiki/三四郎_(小説)", "publication_year": 1908},
                {"title": "それから", "wiki_url": "https://ja.wikipedia.org/wiki/それから", "publication_year": 1909},
                {"title": "門", "wiki_url": "https://ja.wikipedia.org/wiki/門_(小説)", "publication_year": 1910},
            ],
            "森鴎外": [
                {"title": "舞姫", "wiki_url": "https://ja.wikipedia.org/wiki/舞姫", "publication_year": 1890},
                {"title": "高瀬舟", "wiki_url": "https://ja.wikipedia.org/wiki/高瀬舟", "publication_year": 1916},
                {"title": "阿部一族", "wiki_url": "https://ja.wikipedia.org/wiki/阿部一族", "publication_year": 1913},
                {"title": "山椒大夫", "wiki_url": "https://ja.wikipedia.org/wiki/山椒大夫_(森鴎外)", "publication_year": 1915},
                {"title": "雁", "wiki_url": "https://ja.wikipedia.org/wiki/雁_(小説)", "publication_year": 1911},
            ],
            "芥川龍之介": [
                {"title": "羅生門", "wiki_url": "https://ja.wikipedia.org/wiki/羅生門_(小説)", "publication_year": 1915},
                {"title": "鼻", "wiki_url": "https://ja.wikipedia.org/wiki/鼻_(芥川龍之介)", "publication_year": 1916},
                {"title": "地獄変", "wiki_url": "https://ja.wikipedia.org/wiki/地獄変", "publication_year": 1918},
                {"title": "蜘蛛の糸", "wiki_url": "https://ja.wikipedia.org/wiki/蜘蛛の糸", "publication_year": 1918},
                {"title": "杜子春", "wiki_url": "https://ja.wikipedia.org/wiki/杜子春_(小説)", "publication_year": 1920},
                {"title": "河童", "wiki_url": "https://ja.wikipedia.org/wiki/河童_(小説)", "publication_year": 1927},
            ],
            "太宰治": [
                {"title": "人間失格", "wiki_url": "https://ja.wikipedia.org/wiki/人間失格", "publication_year": 1948},
                {"title": "走れメロス", "wiki_url": "https://ja.wikipedia.org/wiki/走れメロス", "publication_year": 1940},
                {"title": "津軽", "wiki_url": "https://ja.wikipedia.org/wiki/津軽_(小説)", "publication_year": 1944},
                {"title": "斜陽", "wiki_url": "https://ja.wikipedia.org/wiki/斜陽_(小説)", "publication_year": 1947},
                {"title": "ヴィヨンの妻", "wiki_url": "https://ja.wikipedia.org/wiki/ヴィヨンの妻", "publication_year": 1947},
                {"title": "お伽草紙", "wiki_url": "https://ja.wikipedia.org/wiki/お伽草紙", "publication_year": 1945},
            ],
            "川端康成": [
                {"title": "雪国", "wiki_url": "https://ja.wikipedia.org/wiki/雪国_(小説)", "publication_year": 1935},
                {"title": "伊豆の踊子", "wiki_url": "https://ja.wikipedia.org/wiki/伊豆の踊子", "publication_year": 1926},
                {"title": "古都", "wiki_url": "https://ja.wikipedia.org/wiki/古都_(小説)", "publication_year": 1962},
                {"title": "千羽鶴", "wiki_url": "https://ja.wikipedia.org/wiki/千羽鶴_(小説)", "publication_year": 1952},
                {"title": "山の音", "wiki_url": "https://ja.wikipedia.org/wiki/山の音", "publication_year": 1954},
            ],
            "三島由紀夫": [
                {"title": "金閣寺", "wiki_url": "https://ja.wikipedia.org/wiki/金閣寺_(小説)", "publication_year": 1956},
                {"title": "仮面の告白", "wiki_url": "https://ja.wikipedia.org/wiki/仮面の告白", "publication_year": 1949},
                {"title": "潮騒", "wiki_url": "https://ja.wikipedia.org/wiki/潮騒_(三島由紀夫)", "publication_year": 1954},
                {"title": "豊饒の海", "wiki_url": "https://ja.wikipedia.org/wiki/豊饒の海", "publication_year": 1970},
                {"title": "憂国", "wiki_url": "https://ja.wikipedia.org/wiki/憂国", "publication_year": 1961},
            ]
        }
        
        return famous_works.get(author_name, [])
    
    def extract_author_data(self, author_name: str) -> Optional[Author]:
        """作者データを抽出してAuthorオブジェクトを返す"""
        wiki_info = self.search_author(author_name)
        
        if wiki_info:
            return Author(
                name=author_name,
                wikipedia_url=wiki_info['url'],
                birth_year=wiki_info['birth_year'],
                death_year=wiki_info['death_year']
            )
        
        # Wikipedia情報が取得できない場合でも基本情報は返す
        print(f"⚠️ {author_name} のWikipedia情報を取得できませんでした（基本情報のみ登録）")
        return Author(name=author_name)
    
    def extract_works_data(self, author_id: int, author_name: str, limit: int = 10) -> List[Work]:
        """作品データを抽出してWorkオブジェクトのリストを返す（制作年代付き）"""
        # Wikipedia情報を再取得（キャッシュ的な使用）
        wiki_info = self.search_author(author_name)
        content = wiki_info['content'] if wiki_info else ""
        
        works_data = self.get_author_works(author_name, content, limit)
        
        works = []
        for work_data in works_data:
            work = Work(
                author_id=author_id,
                title=work_data['title'],
                wiki_url=work_data['wiki_url'],
                publication_year=work_data.get('publication_year')
            )
            works.append(work)
        
        return works
    
    def get_famous_authors_list(self) -> List[str]:
        """日本の著名文豪リストを返す"""
        return self.famous_authors.copy()
    
    def test_extraction(self, author_name: str) -> Dict:
        """抽出機能のテスト"""
        print(f"\n🧪 {author_name} の抽出テスト開始...")
        
        start_time = time.time()
        
        # 作者情報抽出
        author_data = self.extract_author_data(author_name)
        
        # 作品情報抽出（仮のauthor_id=1で実行）
        works_data = self.extract_works_data(1, author_name)
        
        end_time = time.time()
        
        result = {
            'author_name': author_name,
            'extraction_time': round(end_time - start_time, 2),
            'author_data': {
                'name': author_data.name if author_data else None,
                'wikipedia_url': author_data.wikipedia_url if author_data else None,
                'birth_year': author_data.birth_year if author_data else None,
                'death_year': author_data.death_year if author_data else None
            },
            'works_count': len(works_data),
            'works': [work.title for work in works_data]
        }
        
        print(f"✅ 抽出完了: {result['works_count']} 作品, {result['extraction_time']}秒")
        return result 