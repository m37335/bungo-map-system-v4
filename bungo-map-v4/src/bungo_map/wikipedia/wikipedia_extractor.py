#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wikipedia 作者・作品情報抽出器 v4
v3からの移植・改良版
"""

import re
import requests
import wikipedia
from typing import List, Dict, Optional, Tuple, Any
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
import sqlite3
from pathlib import Path

try:
    # v4のモデルとユーティリティをインポート（オプショナル）
    from ..core.models import Author, Work
    from ..utils.logger import get_logger
    from ..database.connection import DatabaseConnection
    logger = get_logger(__name__)
except ImportError:
    # フォールバック：標準ライブラリのログ使用
    import logging
    logger = logging.getLogger(__name__)


class WikipediaExtractor:
    """Wikipedia から作者・作品情報を抽出 v4"""
    
    def __init__(self, db_path: Optional[str] = None):
        # Wikipedia言語設定
        wikipedia.set_lang("ja")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BungoMapV4/1.0 (https://github.com/bungo-map-v4)'
        })
        
        # データベース接続（オプショナル）
        self.db_path = db_path
        
        # 日本の著名文豪リスト（拡張版）
        self.famous_authors = [
            "夏目漱石", "森鴎外", "芥川龍之介", "太宰治", "川端康成", 
            "三島由紀夫", "谷崎潤一郎", "志賀直哉", "島崎藤村", "樋口一葉",
            "正岡子規", "石川啄木", "与謝野晶子", "宮沢賢治", "中島敦",
            "永井荷風", "田山花袋", "国木田独歩", "尾崎紅葉", "坪内逍遥",
            "二葉亭四迷", "幸田露伴", "泉鏡花", "徳冨蘆花", "有島武郎",
            "武者小路実篤", "新美南吉", "小林多喜二", "横光利一",
            "室生犀星", "萩原朔太郎", "高村光太郎", "佐藤春夫", "菊池寛",
            "直木三十五", "江戸川乱歩", "坂口安吾", "梶井基次郎", "中原中也"
        ]
        
        # 年号変換テーブル
        self.era_conversion = {
            '明治': 1867,
            '大正': 1911,
            '昭和': 1925,
            '平成': 1988,
            '令和': 2018
        }
        
    def search_author(self, author_name: str) -> Optional[Dict[str, Any]]:
        """作者のWikipedia情報を詳細検索（改良版）"""
        try:
            logger.info(f"🔍 {author_name} の情報を検索中...")
            
            # Wikipedia検索
            page = wikipedia.page(author_name)
            
            # 基本情報抽出
            extract = page.summary
            birth_year, death_year = self._extract_life_years(extract, page.content)
            
            # 画像URL抽出
            image_url = self._extract_image_url(page)
            
            # カテゴリー抽出
            categories = self._extract_relevant_categories(
                page.categories if hasattr(page, 'categories') else []
            )
            
            return {
                'title': page.title,
                'url': page.url,
                'extract': extract[:500],  # 要約（500文字）
                'content': page.content,
                'birth_year': birth_year,
                'death_year': death_year,
                'categories': categories,
                'image_url': image_url,
                'last_updated': datetime.now().isoformat()
            }
            
        except wikipedia.exceptions.DisambiguationError as e:
            # 曖昧さ回避ページの場合、最適な候補を選択
            return self._handle_disambiguation(author_name, e.options)
            
        except wikipedia.exceptions.PageError:
            logger.warning(f"⚠️ ページが見つかりません: {author_name}")
            
        except Exception as e:
            logger.error(f"⚠️ Wikipedia検索エラー ({author_name}): {e}")
            
        return None
    
    def _handle_disambiguation(self, author_name: str, options: List[str]) -> Optional[Dict[str, Any]]:
        """曖昧さ回避処理（改良版）"""
        # 作家・文学関連のキーワードで候補を絞り込み
        literary_keywords = ['作家', '小説家', '詩人', '文学', '作者', '著者', '歌人', '俳人']
        
        best_option = None
        best_score = 0
        
        for option in options[:5]:  # 最初の5候補のみチェック
            score = 0
            option_lower = option.lower()
            
            # 文学関連キーワードのスコアリング
            for keyword in literary_keywords:
                if keyword in option_lower:
                    score += 2
            
            # 作者名の一致度チェック
            if author_name in option:
                score += 3
            
            if score > best_score:
                best_score = score
                best_option = option
        
        # 最適候補で再検索
        if best_option:
            try:
                logger.info(f"📍 曖昧さ回避: {author_name} → {best_option}")
                page = wikipedia.page(best_option)
                extract = page.summary
                birth_year, death_year = self._extract_life_years(extract, page.content)
                
                return {
                    'title': page.title,
                    'url': page.url,
                    'extract': extract[:500],
                    'content': page.content,
                    'birth_year': birth_year,
                    'death_year': death_year,
                    'categories': self._extract_relevant_categories(
                        page.categories if hasattr(page, 'categories') else []
                    ),
                    'image_url': self._extract_image_url(page),
                    'disambiguation_resolved': True,
                    'last_updated': datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"⚠️ 曖昧さ回避エラー ({best_option}): {e}")
        
        return None
    
    def _extract_life_years(self, summary: str, content: str) -> Tuple[Optional[int], Optional[int]]:
        """テキストから生年・没年を抽出（強化版）"""
        # より多様なパターンに対応
        text = summary + " " + content[:3000]  # 最初の部分のみ使用
        
        birth_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日.*?[生誕]',
            r'(\d{4})年.*?生まれ',
            r'生年.*?(\d{4})年',
            r'（(\d{4})年.*?-',
            r'(\d{4})年.*?誕生',
            r'明治(\d+)年',  # 明治年号
            r'大正(\d+)年',  # 大正年号
            r'昭和(\d+)年.*?[生誕]',  # 昭和年号
            r'平成(\d+)年.*?[生誕]',  # 平成年号
            r'(\d{4})年\s*-',  # 年-年 形式
        ]
        
        death_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日.*?[没死]',
            r'(\d{4})年.*?死去',
            r'没年.*?(\d{4})年',
            r'-\s*(\d{4})年',
            r'(\d{4})年.*?逝去',
            r'昭和(\d+)年.*?[没死]',  # 昭和年号
            r'平成(\d+)年.*?[没死]',  # 平成年号
            r'(\d{4})年.*?歿',
        ]
        
        birth_year = self._extract_year_from_patterns(text, birth_patterns)
        death_year = self._extract_year_from_patterns(text, death_patterns)
        
        return birth_year, death_year
    
    def _extract_year_from_patterns(self, text: str, patterns: List[str]) -> Optional[int]:
        """パターンリストから年を抽出（改良版）"""
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    year_str = match.group(1)
                    year = int(year_str)
                    
                    # 年号変換（拡張版）
                    if '明治' in pattern:
                        year = self.era_conversion['明治'] + year
                    elif '大正' in pattern:
                        year = self.era_conversion['大正'] + year
                    elif '昭和' in pattern:
                        year = self.era_conversion['昭和'] + year
                    elif '平成' in pattern:
                        year = self.era_conversion['平成'] + year
                    
                    # 妥当な年の範囲チェック
                    if 1600 <= year <= 2100:
                        return year
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_image_url(self, page) -> Optional[str]:
        """Wikipedia画像URLを抽出"""
        try:
            if hasattr(page, 'images') and page.images:
                # 最初の画像を使用（通常は肖像画）
                return page.images[0]
        except Exception as e:
            logger.debug(f"画像URL抽出エラー: {e}")
        return None
    
    def _extract_relevant_categories(self, categories: List[str]) -> List[str]:
        """関連性の高いカテゴリーのみを抽出"""
        relevant_keywords = [
            '文学', '作家', '小説家', '詩人', '歌人', '俳人', 
            '日本', '明治', '大正', '昭和', '平成', '作品'
        ]
        
        relevant_categories = []
        for category in categories:
            if any(keyword in category for keyword in relevant_keywords):
                relevant_categories.append(category)
        
        return relevant_categories[:10]  # 最大10個まで
    
    def complete_author_data(self, author_name: str, existing_data: Optional[Dict] = None) -> Dict[str, Any]:
        """作者データの自動補完（メイン機能）"""
        logger.info(f"📚 {author_name} のデータ自動補完開始")
        
        # Wikipedia検索
        wiki_data = self.search_author(author_name)
        
        if not wiki_data:
            return existing_data or {}
        
        # 既存データとWikipediaデータをマージ
        completed_data = existing_data.copy() if existing_data else {}
        
        # 基本情報補完
        if not completed_data.get('birth_year') and wiki_data.get('birth_year'):
            completed_data['birth_year'] = wiki_data['birth_year']
        
        if not completed_data.get('death_year') and wiki_data.get('death_year'):
            completed_data['death_year'] = wiki_data['death_year']
        
        if not completed_data.get('wikipedia_url'):
            completed_data['wikipedia_url'] = wiki_data.get('url')
        
        if not completed_data.get('description'):
            completed_data['description'] = wiki_data.get('extract')
        
        # メタデータ追加
        completed_data['wikipedia_data'] = {
            'categories': wiki_data.get('categories', []),
            'image_url': wiki_data.get('image_url'),
            'last_updated': wiki_data.get('last_updated')
        }
        
        logger.info(f"✅ {author_name} のデータ補完完了")
        
        return completed_data
    
    def get_famous_authors_list(self) -> List[str]:
        """著名作家リストを取得"""
        return self.famous_authors.copy()
    
    def test_extraction(self, author_name: str) -> Dict[str, Any]:
        """抽出テスト実行"""
        logger.info(f"🧪 {author_name} の抽出テスト開始")
        
        start_time = time.time()
        result = self.complete_author_data(author_name)
        end_time = time.time()
        
        test_result = {
            'author_name': author_name,
            'extraction_time': round(end_time - start_time, 2),
            'success': bool(result),
            'data_quality': self._assess_data_quality(result),
            'extracted_data': result
        }
        
        logger.info(f"🧪 テスト完了: {test_result['data_quality']}/10点")
        
        return test_result
    
    def _assess_data_quality(self, data: Dict) -> int:
        """データ品質を10点満点で評価"""
        score = 0
        
        if data.get('birth_year'):
            score += 2
        if data.get('death_year'):
            score += 1
        if data.get('wikipedia_url'):
            score += 1
        if data.get('description'):
            score += 2
        if data.get('wikipedia_data', {}).get('image_url'):
            score += 1
        
        return min(score, 7)  # 現在は7点満点（作品データは別途実装）