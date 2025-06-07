#!/usr/bin/env python3
"""
改良版青空文庫クライアント - 404エラー解決版
成功率30%問題を解決するため、公式カタログを使用
"""

import requests
import zipfile
import io
import csv
import time
import re
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ImprovedAozoraWork:
    """改良版青空文庫作品情報"""
    work_id: str
    title: str
    author: str
    author_id: str
    text_url: Optional[str] = None
    html_url: Optional[str] = None
    first_published: Optional[str] = None
    file_size: Optional[int] = None

class ImprovedAozoraClient:
    """改良版青空文庫クライアント - 404エラー解決版"""
    
    def __init__(self):
        # 青空文庫公式カタログURL
        self.catalog_url = 'https://www.aozora.gr.jp/index_pages/list_person_all_extended_utf8.zip'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (文豪地図システム v3.0 - 404エラー解決版)'
        })
        
        # キャッシュ
        self._catalog_cache = None
        self._works_cache = {}
        
    def fetch_catalog(self) -> List[Dict]:
        """青空文庫公式カタログを取得"""
        if self._catalog_cache:
            return self._catalog_cache
            
        print("📚 青空文庫公式カタログ取得中...")
        
        try:
            response = self.session.get(self.catalog_url, timeout=30)
            response.raise_for_status()
            
            # ZIPファイルを解凍
            zip_data = zipfile.ZipFile(io.BytesIO(response.content))
            
            # CSVファイルを抽出
            csv_filename = 'list_person_all_extended_utf8.csv'
            csv_content = zip_data.read(csv_filename).decode('utf-8')
            
            # CSVパース
            csv_data = io.StringIO(csv_content)
            reader = csv.DictReader(csv_data)
            
            catalog = []
            for row in reader:
                catalog.append({
                    'work_id': row.get('作品ID', ''),
                    'title': row.get('作品名', ''),
                    'author': row.get('姓', '') + row.get('名', ''),
                    'author_id': row.get('人物ID', ''),
                    'first_published': row.get('初出', ''),
                    'text_url': row.get('テキストファイルURL', ''),
                    'html_url': row.get('XHTML/HTMLファイルURL', ''),
                    'file_size': row.get('ファイルサイズ', 0)
                })
            
            self._catalog_cache = catalog
            print(f"✅ カタログ取得完了: {len(catalog)} 作品")
            return catalog
            
        except Exception as e:
            print(f"❌ カタログ取得エラー: {e}")
            raise
    
    def search_work_by_title(self, title: str, author: str = None) -> Optional[ImprovedAozoraWork]:
        """作品名（＋作者名）で作品を検索"""
        catalog = self.fetch_catalog()
        
        for item in catalog:
            # タイトル一致チェック
            title_match = (title in item['title'] or item['title'] in title)
            
            # 作者名チェック（指定されている場合）
            author_match = True
            if author:
                author_match = (author in item['author'] or item['author'] in author)
            
            if title_match and author_match:
                return ImprovedAozoraWork(
                    work_id=item['work_id'],
                    title=item['title'],
                    author=item['author'],
                    author_id=item['author_id'],
                    text_url=item['text_url'],
                    html_url=item['html_url'],
                    first_published=item['first_published'],
                    file_size=int(item['file_size']) if item['file_size'] else 0
                )
        
        print(f"⚠️ 作品が見つかりません: {title} ({author})")
        return None
    
    def get_work_text(self, title: str, author: str) -> Optional[str]:
        """作品テキストを取得（404エラー解決版）"""
        # キャッシュチェック
        cache_key = f"{author}_{title}"
        if cache_key in self._works_cache:
            return self._works_cache[cache_key]
        
        # 作品検索
        work = self.search_work_by_title(title, author)
        if not work:
            return None
        
        # テキストURL優先、なければHTMLURL
        download_url = work.text_url or work.html_url
        if not download_url:
            print(f"❌ ダウンロードURLが見つかりません: {title}")
            return None
        
        print(f"📖 テキストダウンロード中: {title} from {download_url}")
        
        try:
            response = self.session.get(download_url, timeout=30)
            response.raise_for_status()
            
            # エンコーディング検出・変換
            text = self._detect_and_decode(response.content)
            
            # 青空文庫記法の除去
            cleaned_text = self._clean_aozora_text(text)
            
            # キャッシュに保存
            self._works_cache[cache_key] = cleaned_text
            
            print(f"✅ テキスト取得成功: {title} ({len(cleaned_text)} 文字)")
            return cleaned_text
            
        except Exception as e:
            print(f"❌ テキストダウンロードエラー: {e}")
            return None
    
    def _detect_and_decode(self, content: bytes) -> str:
        """エンコーディング検出・デコード"""
        # 青空文庫は通常Shift-JIS
        encodings = ['shift_jis', 'utf-8', 'euc-jp', 'iso-2022-jp']
        
        for encoding in encodings:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # 最後の手段：エラー無視
        return content.decode('shift_jis', errors='ignore')
    
    def _clean_aozora_text(self, text: str) -> str:
        """青空文庫記法を除去"""
        # ヘッダ情報削除（「作品名」まで）
        lines = text.split('\n')
        start_index = 0
        for i, line in enumerate(lines):
            if '-----' in line or '底本：' in line:
                start_index = i + 1
                break
        
        content_lines = lines[start_index:]
        content = '\n'.join(content_lines)
        
        # 青空文庫記法の除去
        # 注記: ［＃...］
        content = re.sub(r'［＃[^］]*］', '', content)
        
        # ルビ: 《...》
        content = re.sub(r'《[^》]*》', '', content)
        
        # 傍点: ○○○○
        content = re.sub(r'［[^］]*］', '', content)  
        
        # 改行の正規化
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = content.strip()
        
        return content
    
    def test_404_fix(self) -> Dict:
        """404エラー解決テスト"""
        print('🚀 404エラー解決テスト開始')
        print('='*60)
        
        # 旧システムで失敗した作品をテスト
        test_works = [
            ('夏目漱石', 'それから'),
            ('夏目漱石', '門'),
            ('芥川龍之介', '鼻'),
            ('芥川龍之介', '蜘蛛の糸'),
            ('芥川龍之介', '地獄変'),
            ('芥川龍之介', '河童'),
            ('太宰治', '津軽'),
            ('樋口一葉', 'たけくらべ'),
            ('樋口一葉', 'にごりえ'),
            ('森鴎外', '舞姫'),
            ('森鴎外', '高瀬舟'),
            ('森鴎外', '山椒大夫'),
            ('宮沢賢治', '風の又三郎'),
            ('石川啄木', '一握の砂'),
            ('石川啄木', '悲しき玩具'),
            ('与謝野晶子', 'みだれ髪'),
            ('与謝野晶子', '君死にたまふことなかれ'),
            ('正岡子規', '病床六尺'),
            ('正岡子規', '歌よみに与ふる書'),
            ('小泉八雲', '怪談')
        ]
        
        successful_downloads = 0
        start_time = time.time()
        
        for i, (author, title) in enumerate(test_works, 1):
            print(f'[{i:2d}/20] {title} ({author}) ', end='')
            
            try:
                text = self.get_work_text(title, author)
                if text and len(text) > 100:
                    print('✅')
                    successful_downloads += 1
                else:
                    print('❌')
            except:
                print('💥')
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 結果サマリー
        success_rate = (successful_downloads / len(test_works)) * 100
        
        result = {
            'total_tests': len(test_works),
            'successful': successful_downloads,
            'success_rate': success_rate,
            'processing_time': processing_time,
            'old_success_rate': 30.0,
            'improvement': success_rate - 30.0
        }
        
        print(f'\n🎯 404エラー解決テスト結果:')
        print(f'   📊 成功率: {success_rate:.1f}% ({successful_downloads}/{len(test_works)})')
        print(f'   ⏱️ 処理時間: {processing_time:.1f}秒')
        print(f'   🔴 旧システム: 30.0% (404エラー多発)')
        print(f'   🟢 新システム: {success_rate:.1f}%')
        
        if success_rate > 30:
            print(f'   🚀 改善効果: +{result["improvement"]:.1f}ポイント!')
            
            if success_rate >= 80:
                print(f'   🏆 優秀！404問題を完全解決!')
            elif success_rate >= 60:
                print(f'   👍 良好！大幅な改善を達成!')
            else:
                print(f'   📈 改善中！さらなる最適化が必要')
        
        return result

def main():
    """メイン実行関数"""
    client = ImprovedAozoraClient()
    
    # 404エラー解決テスト実行
    result = client.test_404_fix()
    
    print(f'\n🎉 改良版青空文庫クライアント テスト完了!')
    print(f'📈 成功率改善: {result["old_success_rate"]:.1f}% → {result["success_rate"]:.1f}%')

if __name__ == '__main__':
    main() 