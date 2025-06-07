#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫テキスト抽出器
実際の青空文庫からテキストを取得し、地名抽出可能な形に正規化
"""

import requests
import re
import time
import zipfile
import io
import os
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
import json


class AozoraExtractor:
    """青空文庫テキスト抽出器"""
    
    def __init__(self, cache_dir: str = "data/aozora_cache"):
        self.base_url = "https://www.aozora.gr.jp"
        self.api_url = "https://pubserver1.herokuapp.com/api/v0.1/books"
        self.cache_dir = cache_dir
        
        # セッション設定
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BungoMapBot/2.0 (Educational Research Purpose)'
        })
        
        # キャッシュディレクトリ作成
        os.makedirs(cache_dir, exist_ok=True)
        
        # APIの利用可能性確認
        self.api_available = self._check_api_availability()
        
    def _check_api_availability(self) -> bool:
        """青空文庫APIの利用可能性をチェック"""
        try:
            response = self.session.get(f"{self.api_url}?limit=1", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def search_aozora_work(self, work_title: str, author_name: str) -> Optional[str]:
        """青空文庫で作品のURLを検索"""
        print(f"🔍 青空文庫検索: {author_name} - {work_title}")
        
        # APIが利用可能な場合は使用
        if self.api_available:
            return self._search_via_api(work_title, author_name)
        
        # フォールバック: 直接検索
        return self._search_via_direct(work_title, author_name)
    
    def _search_via_api(self, work_title: str, author_name: str) -> Optional[str]:
        """API経由で作品検索"""
        try:
            # 作者名で検索
            params = {'author': author_name, 'limit': 20}
            response = self.session.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            
            books = response.json()
            
            # 作品名でマッチング
            for book in books:
                book_title = book.get('title', '')
                if work_title in book_title or book_title in work_title:
                    text_url = book.get('text_url')
                    if text_url:
                        print(f"✅ API検索成功: {book_title}")
                        return text_url
            
            print(f"❌ API検索で見つかりません: {work_title}")
            return None
            
        except Exception as e:
            print(f"⚠️ API検索エラー: {e}")
            return None
    
    def _search_via_direct(self, work_title: str, author_name: str) -> Optional[str]:
        """直接検索（フォールバック）"""
        # 簡易的な作品URLパターン
        # 実際の実装では青空文庫のサイト構造に基づく検索が必要
        
        # 一般的な青空文庫のテキストURL形式を試行
        possible_urls = [
            f"https://www.aozora.gr.jp/cards/{author_name}/{work_title}.txt",
            f"https://raw.githubusercontent.com/aozorabunko/aozorabunko/master/cards/{author_name}/{work_title}.txt"
        ]
        
        for url in possible_urls:
            try:
                response = self.session.head(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ 直接検索成功: {url}")
                    return url
            except:
                continue
        
        print(f"❌ 直接検索で見つかりません: {work_title}")
        return None
    
    def download_and_extract_text(self, text_url: str) -> Optional[str]:
        """青空文庫テキストをダウンロードして正規化"""
        if not text_url:
            return None
        
        # キャッシュファイル名生成
        cache_filename = self._get_cache_filename(text_url)
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        # キャッシュ確認
        if os.path.exists(cache_path):
            print(f"📁 キャッシュから読み込み: {cache_filename}")
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        try:
            print(f"📥 テキストダウンロード: {text_url}")
            response = self.session.get(text_url, timeout=30)
            response.raise_for_status()
            
            # コンテンツタイプを確認してHTML/テキストを判定
            content_type = response.headers.get('content-type', '').lower()
            
            if 'html' in content_type or text_url.endswith('.html'):
                # HTMLファイルの場合
                raw_text = self._extract_text_from_html(response.content)
            else:
                # テキストファイルの場合
                raw_text = self._decode_content(response.content)
            
            if not raw_text:
                print(f"❌ テキスト抽出失敗")
                return None
            
            # 青空文庫記法を正規化
            normalized_text = self.normalize_aozora_text(raw_text)
            
            if len(normalized_text) < 100:
                print(f"❌ テキストが短すぎます: {len(normalized_text)}文字")
                return None
            
            # キャッシュ保存
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(normalized_text)
            
            print(f"✅ テキスト取得完了: {len(normalized_text)}文字")
            return normalized_text
            
        except Exception as e:
            print(f"❌ テキストダウンロードエラー: {e}")
            return None
    
    def _extract_text_from_html(self, content: bytes) -> Optional[str]:
        """HTMLファイルからテキストを抽出"""
        try:
            # エンコーディング検出・デコード
            html_text = self._decode_content(content)
            if not html_text:
                return None
            
            # BeautifulSoupでHTMLをパース
            soup = BeautifulSoup(html_text, 'html.parser')
            
            # 青空文庫HTMLの本文部分を抽出
            # 一般的に div.main_text または body内のテキスト
            main_text = soup.find('div', class_='main_text')
            
            if not main_text:
                # 代替: bodyタグから抽出
                main_text = soup.find('body')
                if main_text:
                    # scriptやstyleタグを除去
                    for tag in main_text(['script', 'style', 'nav', 'header', 'footer']):
                        tag.decompose()
            
            if main_text:
                # テキスト抽出
                text = main_text.get_text()
                print(f"✅ HTML→テキスト変換完了: {len(text)}文字")
                return text
            else:
                print(f"❌ HTML本文が見つかりません")
                return None
                
        except Exception as e:
            print(f"❌ HTML解析エラー: {e}")
            return None
    
    def _decode_content(self, content: bytes) -> Optional[str]:
        """コンテンツのエンコーディングを検出してデコード"""
        # 青空文庫は主にShift_JIS
        encodings = ['shift_jis', 'utf-8', 'euc-jp']
        
        for encoding in encodings:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # 最後の手段: エラーを無視してShift_JISでデコード
        try:
            return content.decode('shift_jis', errors='ignore')
        except:
            return None
    
    def normalize_aozora_text(self, raw_text: str) -> str:
        """青空文庫テキストの正規化"""
        text = raw_text
        
        # 1. ヘッダー・フッター除去
        text = self._remove_metadata(text)
        
        # 2. ルビ記法処理
        text = self._process_ruby(text)
        
        # 3. 注記・記法除去
        text = self._remove_annotations(text)
        
        # 4. 改行・空白正規化
        text = self._normalize_whitespace(text)
        
        return text.strip()
    
    def _remove_metadata(self, text: str) -> str:
        """ヘッダー・フッター情報を除去"""
        lines = text.split('\n')
        content_lines = []
        in_content = False
        
        for line in lines:
            line = line.strip()
            
            # ヘッダー終了・本文開始の検出
            if not in_content:
                # メタデータ行をスキップ
                if (line.startswith('底本：') or line.startswith('入力：') or 
                    line.startswith('校正：') or line.startswith('※') or
                    '------' in line or line == '' or 
                    '青空文庫' in line):
                    continue
                else:
                    # 本文開始
                    in_content = True
            
            # フッター検出で終了
            if in_content and ('底本：' in line or '入力：' in line or '校正：' in line):
                break
            
            if in_content:
                content_lines.append(line)
        
        return '\n'.join(content_lines)
    
    def _process_ruby(self, text: str) -> str:
        """ルビ記法を処理"""
        # ｜漢字《かんじ》 → 漢字
        text = re.sub(r'｜([^《]+)《[^》]+》', r'\1', text)
        
        # 漢字《かんじ》 → 漢字
        text = re.sub(r'([一-龯]+)《[^》]+》', r'\1', text)
        
        # 残ったルビ記号除去
        text = re.sub(r'《[^》]*》', '', text)
        text = text.replace('｜', '')
        
        return text
    
    def _remove_annotations(self, text: str) -> str:
        """注記・記法を除去"""
        # ［＃...］記法除去
        text = re.sub(r'［＃[^］]*］', '', text)
        
        # 〔...〕編者注除去
        text = re.sub(r'〔[^〕]*〕', '', text)
        
        # ※注釈行除去
        text = re.sub(r'※[^\n]*\n', '', text)
        
        # その他の記号
        text = re.sub(r'＊', '', text)
        
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """空白・改行を正規化"""
        # Windows改行統一
        text = re.sub(r'\r\n', '\n', text)
        
        # 連続改行を2つまでに制限
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 全角スペースの連続を1つに
        text = re.sub(r'　+', '　', text)
        
        # 行頭・行末のスペース除去
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        
        return '\n'.join(lines)
    
    def _get_cache_filename(self, url: str) -> str:
        """キャッシュファイル名を生成"""
        # URLから安全なファイル名を生成
        filename = re.sub(r'[^\w\-_.]', '_', url.split('/')[-1])
        if not filename.endswith('.txt'):
            filename += '.txt'
        return filename
    
    def get_sample_works(self) -> List[Dict]:
        """テスト用のサンプル作品情報"""
        return [
            {
                'author_name': '夏目漱石',
                'title': '坊っちゃん',
                'text_url': 'https://www.aozora.gr.jp/cards/000148/files/752_14964.html'
            },
            {
                'author_name': '芥川龍之介', 
                'title': '羅生門',
                'text_url': 'https://www.aozora.gr.jp/cards/000879/files/127_15260.html'
            },
            {
                'author_name': '太宰治',
                'title': '走れメロス',
                'text_url': 'https://www.aozora.gr.jp/cards/000035/files/1567_14913.html'
            }
        ]
    
    def get_extended_works(self) -> List[Dict]:
        """拡張版作品リスト - 主要文豪12名・30作品"""
        return [
            # 夏目漱石 (6作品)
            {'author_name': '夏目漱石', 'title': '坊っちゃん', 'text_url': 'https://www.aozora.gr.jp/cards/000148/files/752_14964.html'},
            {'author_name': '夏目漱石', 'title': '吾輩は猫である', 'text_url': 'https://www.aozora.gr.jp/cards/000148/files/789_14547.html'},
            {'author_name': '夏目漱石', 'title': 'こころ', 'text_url': 'https://www.aozora.gr.jp/cards/000148/files/773_14560.html'},
            {'author_name': '夏目漱石', 'title': '三四郎', 'text_url': 'https://www.aozora.gr.jp/cards/000148/files/794_14946.html'},
            {'author_name': '夏目漱石', 'title': 'それから', 'text_url': 'https://www.aozora.gr.jp/cards/000148/files/783_14954.html'},
            {'author_name': '夏目漱石', 'title': '門', 'text_url': 'https://www.aozora.gr.jp/cards/000148/files/784_14965.html'},
            
            # 芥川龍之介 (5作品)
            {'author_name': '芥川龍之介', 'title': '羅生門', 'text_url': 'https://www.aozora.gr.jp/cards/000879/files/127_15260.html'},
            {'author_name': '芥川龍之介', 'title': '鼻', 'text_url': 'https://www.aozora.gr.jp/cards/000879/files/92_15261.html'},
            {'author_name': '芥川龍之介', 'title': '蜘蛛の糸', 'text_url': 'https://www.aozora.gr.jp/cards/000879/files/92_15183.html'},
            {'author_name': '芥川龍之介', 'title': '地獄変', 'text_url': 'https://www.aozora.gr.jp/cards/000879/files/127_15183.html'},
            {'author_name': '芥川龍之介', 'title': '河童', 'text_url': 'https://www.aozora.gr.jp/cards/000879/files/69_15191.html'},
            
            # 太宰治 (4作品)
            {'author_name': '太宰治', 'title': '走れメロス', 'text_url': 'https://www.aozora.gr.jp/cards/000035/files/1567_14913.html'},
            {'author_name': '太宰治', 'title': '人間失格', 'text_url': 'https://www.aozora.gr.jp/cards/000035/files/301_14912.html'},
            {'author_name': '太宰治', 'title': '津軽', 'text_url': 'https://www.aozora.gr.jp/cards/000035/files/2280_15100.html'},
            {'author_name': '太宰治', 'title': '斜陽', 'text_url': 'https://www.aozora.gr.jp/cards/000035/files/1565_8559.html'},
            
            # 樋口一葉 (2作品)
            {'author_name': '樋口一葉', 'title': 'たけくらべ', 'text_url': 'https://www.aozora.gr.jp/cards/000064/files/392_19874.html'},
            {'author_name': '樋口一葉', 'title': 'にごりえ', 'text_url': 'https://www.aozora.gr.jp/cards/000064/files/393_19877.html'},
            
            # 森鴎外 (3作品)
            {'author_name': '森鴎外', 'title': '舞姫', 'text_url': 'https://www.aozora.gr.jp/cards/000129/files/695_19725.html'},
            {'author_name': '森鴎外', 'title': '高瀬舟', 'text_url': 'https://www.aozora.gr.jp/cards/000129/files/645_19728.html'},
            {'author_name': '森鴎外', 'title': '山椒大夫', 'text_url': 'https://www.aozora.gr.jp/cards/000129/files/682_19729.html'},
            
            # 宮沢賢治 (3作品)
            {'author_name': '宮沢賢治', 'title': '銀河鉄道の夜', 'text_url': 'https://www.aozora.gr.jp/cards/000081/files/456_15050.html'},
            {'author_name': '宮沢賢治', 'title': '風の又三郎', 'text_url': 'https://www.aozora.gr.jp/cards/000081/files/1920_18876.html'},
            {'author_name': '宮沢賢治', 'title': '注文の多い料理店', 'text_url': 'https://www.aozora.gr.jp/cards/000081/files/43754_17659.html'},
            
            # 石川啄木 (2作品)
            {'author_name': '石川啄木', 'title': '一握の砂', 'text_url': 'https://www.aozora.gr.jp/cards/000153/files/1235_19874.html'},
            {'author_name': '石川啄木', 'title': '悲しき玩具', 'text_url': 'https://www.aozora.gr.jp/cards/000153/files/1236_19875.html'},
            
            # 与謝野晶子 (2作品)
            {'author_name': '与謝野晶子', 'title': 'みだれ髪', 'text_url': 'https://www.aozora.gr.jp/cards/000885/files/14808_19230.html'},
            {'author_name': '与謝野晶子', 'title': '君死にたまふことなかれ', 'text_url': 'https://www.aozora.gr.jp/cards/000885/files/48864_30332.html'},
            
            # 正岡子規 (2作品)
            {'author_name': '正岡子規', 'title': '病床六尺', 'text_url': 'https://www.aozora.gr.jp/cards/000305/files/1557_19231.html'},
            {'author_name': '正岡子規', 'title': '歌よみに与ふる書', 'text_url': 'https://www.aozora.gr.jp/cards/000305/files/1124_19232.html'},
            
            # 小泉八雲 (1作品) 
            {'author_name': '小泉八雲', 'title': '怪談', 'text_url': 'https://www.aozora.gr.jp/cards/000258/files/42320_30332.html'}
        ]
    
    def test_extraction(self, work_info: Dict = None) -> Dict:
        """抽出機能のテスト"""
        if not work_info:
            work_info = self.get_sample_works()[0]  # 坊っちゃん
        
        author_name = work_info['author_name']
        title = work_info['title']
        
        print(f"\n🧪 青空文庫抽出テスト: {author_name} - {title}")
        
        start_time = time.time()
        
        # URL検索
        text_url = self.search_aozora_work(title, author_name)
        
        if not text_url:
            # サンプルURLを使用
            text_url = work_info.get('text_url')
        
        # テキスト取得
        if text_url:
            text_content = self.download_and_extract_text(text_url)
        else:
            text_content = None
        
        end_time = time.time()
        
        result = {
            'author_name': author_name,
            'title': title,
            'text_url': text_url,
            'text_length': len(text_content) if text_content else 0,
            'success': text_content is not None,
            'extraction_time': round(end_time - start_time, 2),
            'sample_text': text_content[:200] + '...' if text_content else None
        }
        
        print(f"✅ テスト結果: {'成功' if result['success'] else '失敗'}")
        if result['success']:
            print(f"   テキスト長: {result['text_length']}文字")
            print(f"   サンプル: {result['sample_text']}")
        print(f"   実行時間: {result['extraction_time']}秒")
        
        return result 