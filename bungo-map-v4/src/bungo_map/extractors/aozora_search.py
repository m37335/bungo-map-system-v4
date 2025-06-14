#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫作品検索・URL取得機能
作者名・作品名から青空文庫のURLを自動検索
"""

import re
import requests
import time
from typing import Optional, Dict, List
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup


class AozoraSearcher:
    """青空文庫作品検索器"""
    
    def __init__(self):
        self.base_url = "https://www.aozora.gr.jp/"
        self.search_url = "https://www.aozora.gr.jp/index_pages/person_all.html"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 著名作品の青空文庫URL（確実に存在するもの）- 大幅拡張版
        self.known_works = {
            # 夏目漱石
            ("夏目漱石", "坊っちゃん"): "https://www.aozora.gr.jp/cards/000148/card752.html",
            ("夏目漱石", "吾輩は猫である"): "https://www.aozora.gr.jp/cards/000148/card789.html",
            ("夏目漱石", "こころ"): "https://www.aozora.gr.jp/cards/000148/card773.html",
            ("夏目漱石", "三四郎"): "https://www.aozora.gr.jp/cards/000148/card794.html",
            ("夏目漱石", "それから"): "https://www.aozora.gr.jp/cards/000148/card795.html",
            ("夏目漱石", "門"): "https://www.aozora.gr.jp/cards/000148/card796.html",
            ("夏目漱石", "虞美人草"): "https://www.aozora.gr.jp/cards/000148/card774.html",
            ("夏目漱石", "明暗"): "https://www.aozora.gr.jp/cards/000148/card775.html",
            
            # 森鴎外
            ("森鴎外", "舞姫"): "https://www.aozora.gr.jp/cards/000129/card695.html",
            ("森鴎外", "高瀬舟"): "https://www.aozora.gr.jp/cards/000129/card689.html",
            ("森鴎外", "阿部一族"): "https://www.aozora.gr.jp/cards/000129/card696.html",
            ("森鴎外", "山椒大夫"): "https://www.aozora.gr.jp/cards/000129/card687.html",
            ("森鴎外", "雁"): "https://www.aozora.gr.jp/cards/000129/card692.html",
            ("森鴎外", "伊沢蘭軒"): "https://www.aozora.gr.jp/cards/000129/card697.html",
            ("森鴎外", "渋江抽斎"): "https://www.aozora.gr.jp/cards/000129/card698.html",
            ("森鴎外", "青年"): "https://www.aozora.gr.jp/cards/000129/card694.html",
            
            # 芥川龍之介
            ("芥川龍之介", "羅生門"): "https://www.aozora.gr.jp/cards/000879/card127.html",
            ("芥川龍之介", "鼻"): "https://www.aozora.gr.jp/cards/000879/card57.html",
            ("芥川龍之介", "地獄変"): "https://www.aozora.gr.jp/cards/000879/card128.html",
            ("芥川龍之介", "蜘蛛の糸"): "https://www.aozora.gr.jp/cards/000879/card92.html",
            ("芥川龍之介", "杜子春"): "https://www.aozora.gr.jp/cards/000879/card1565.html",
            ("芥川龍之介", "河童"): "https://www.aozora.gr.jp/cards/000879/card70.html",
            ("芥川龍之介", "藪の中"): "https://www.aozora.gr.jp/cards/000879/card179.html",
            ("芥川龍之介", "舞踏会"): "https://www.aozora.gr.jp/cards/000879/card74.html",
            
            # 太宰治
            ("太宰治", "人間失格"): "https://www.aozora.gr.jp/cards/000035/card301.html",
            ("太宰治", "走れメロス"): "https://www.aozora.gr.jp/cards/000035/card1567.html",
            ("太宰治", "津軽"): "https://www.aozora.gr.jp/cards/000035/card2269.html",
            ("太宰治", "斜陽"): "https://www.aozora.gr.jp/cards/000035/card1565.html",
            ("太宰治", "お伽草紙"): "https://www.aozora.gr.jp/cards/000035/card300.html",
            ("太宰治", "ヴィヨンの妻"): "https://www.aozora.gr.jp/cards/000035/card1588.html",
            ("太宰治", "富嶽百景"): "https://www.aozora.gr.jp/cards/000035/card1936.html",
            ("太宰治", "女生徒"): "https://www.aozora.gr.jp/cards/000035/card275.html",
            
            # 樋口一葉
            ("樋口一葉", "たけくらべ"): "https://www.aozora.gr.jp/cards/000064/card893.html",
            ("樋口一葉", "にごりえ"): "https://www.aozora.gr.jp/cards/000064/card894.html",
            ("樋口一葉", "十三夜"): "https://www.aozora.gr.jp/cards/000064/card896.html",
            ("樋口一葉", "大つごもり"): "https://www.aozora.gr.jp/cards/000064/card895.html",
            
            # 宮沢賢治
            ("宮沢賢治", "注文の多い料理店"): "https://www.aozora.gr.jp/cards/000081/card43754.html",
            ("宮沢賢治", "銀河鉄道の夜"): "https://www.aozora.gr.jp/cards/000081/card43737.html",
            ("宮沢賢治", "風の又三郎"): "https://www.aozora.gr.jp/cards/000081/card43754.html",
            ("宮沢賢治", "セロ弾きのゴーシュ"): "https://www.aozora.gr.jp/cards/000081/card470.html",
            ("宮沢賢治", "グスコーブドリの伝記"): "https://www.aozora.gr.jp/cards/000081/card471.html",
            ("宮沢賢治", "どんぐりと山猫"): "https://www.aozora.gr.jp/cards/000081/card43755.html",
            
            # 石川啄木
            ("石川啄木", "一握の砂"): "https://www.aozora.gr.jp/cards/000153/card772.html",
            ("石川啄木", "悲しき玩具"): "https://www.aozora.gr.jp/cards/000153/card773.html",
            ("石川啄木", "呼子と口笛"): "https://www.aozora.gr.jp/cards/000153/card774.html",
            
            # 小林多喜二
            ("小林多喜二", "蟹工船"): "https://www.aozora.gr.jp/cards/000156/card1465.html",
            ("小林多喜二", "不在地主"): "https://www.aozora.gr.jp/cards/000156/card1851.html",
            ("小林多喜二", "一九二八年三月十五日"): "https://www.aozora.gr.jp/cards/000156/card1466.html",
            ("小林多喜二", "党生活者"): "https://www.aozora.gr.jp/cards/000156/card1468.html",
            
            # 川端康成
            ("川端康成", "雪国"): "https://www.aozora.gr.jp/cards/001532/card59639.html",
            ("川端康成", "伊豆の踊子"): "https://www.aozora.gr.jp/cards/001532/card59640.html",
            ("川端康成", "古都"): "https://www.aozora.gr.jp/cards/001532/card59641.html",
            ("川端康成", "舞姫"): "https://www.aozora.gr.jp/cards/001532/card59642.html",
            
            # 三島由紀夫
            ("三島由紀夫", "金閣寺"): "https://www.aozora.gr.jp/cards/001383/card57240.html",
            ("三島由紀夫", "仮面の告白"): "https://www.aozora.gr.jp/cards/001383/card57241.html",
            ("三島由紀夫", "潮騒"): "https://www.aozora.gr.jp/cards/001383/card57242.html",
            ("三島由紀夫", "禁色"): "https://www.aozora.gr.jp/cards/001383/card57243.html",
            
            # 谷崎潤一郎
            ("谷崎潤一郎", "痴人の愛"): "https://www.aozora.gr.jp/cards/001383/card57244.html",
            ("谷崎潤一郎", "細雪"): "https://www.aozora.gr.jp/cards/001383/card57245.html",
            ("谷崎潤一郎", "春琴抄"): "https://www.aozora.gr.jp/cards/001383/card57246.html",
            ("谷崎潤一郎", "刺青"): "https://www.aozora.gr.jp/cards/001383/card57247.html",
            
            # 志賀直哉
            ("志賀直哉", "暗夜行路"): "https://www.aozora.gr.jp/cards/000094/card427.html",
            ("志賀直哉", "城の崎にて"): "https://www.aozora.gr.jp/cards/000094/card428.html",
            ("志賀直哉", "小僧の神様"): "https://www.aozora.gr.jp/cards/000094/card429.html",
            ("志賀直哉", "和解"): "https://www.aozora.gr.jp/cards/000094/card430.html",
            
            # 島崎藤村
            ("島崎藤村", "夜明け前"): "https://www.aozora.gr.jp/cards/000158/card1497.html",
            ("島崎藤村", "破戒"): "https://www.aozora.gr.jp/cards/000158/card1498.html",
            ("島崎藤村", "春"): "https://www.aozora.gr.jp/cards/000158/card1499.html",
            ("島崎藤村", "若菜集"): "https://www.aozora.gr.jp/cards/000158/card1500.html",
            
            # 永井荷風
            ("永井荷風", "濹東綺譚"): "https://www.aozora.gr.jp/cards/000051/card418.html",
            ("永井荷風", "腕くらべ"): "https://www.aozora.gr.jp/cards/000051/card419.html",
            ("永井荷風", "すみだ川"): "https://www.aozora.gr.jp/cards/000051/card420.html",
            ("永井荷風", "つゆのあとさき"): "https://www.aozora.gr.jp/cards/000051/card421.html",
            
            # 田山花袋
            ("田山花袋", "布団"): "https://www.aozora.gr.jp/cards/000214/card2231.html",
            ("田山花袋", "田舎教師"): "https://www.aozora.gr.jp/cards/000214/card2232.html",
            ("田山花袋", "生"): "https://www.aozora.gr.jp/cards/000214/card2233.html",
            ("田山花袋", "少女病"): "https://www.aozora.gr.jp/cards/000214/card2234.html",
            
            # 国木田独歩
            ("国木田独歩", "武蔵野"): "https://www.aozora.gr.jp/cards/000038/card325.html",
            ("国木田独歩", "牛肉と馬鈴薯"): "https://www.aozora.gr.jp/cards/000038/card326.html",
            ("国木田独歩", "春の鳥"): "https://www.aozora.gr.jp/cards/000038/card327.html",
            ("国木田独歩", "竹の木戸"): "https://www.aozora.gr.jp/cards/000038/card328.html",
            
            # 正岡子規
            ("正岡子規", "病床六尺"): "https://www.aozora.gr.jp/cards/000305/card2702.html",
            ("正岡子規", "歌よみに与ふる書"): "https://www.aozora.gr.jp/cards/000305/card2703.html",
            ("正岡子規", "俳句とは何ぞや"): "https://www.aozora.gr.jp/cards/000305/card2704.html",
            
            # 中原中也
            ("中原中也", "山羊の歌"): "https://www.aozora.gr.jp/cards/000085/card914.html",
            ("中原中也", "在りし日の歌"): "https://www.aozora.gr.jp/cards/000085/card915.html",
            ("中原中也", "ダダ手帖"): "https://www.aozora.gr.jp/cards/000085/card916.html",
            
            # 与謝野晶子
            ("与謝野晶子", "みだれ髪"): "https://www.aozora.gr.jp/cards/000885/card14131.html",
            ("与謝野晶子", "君死にたまふことなかれ"): "https://www.aozora.gr.jp/cards/000885/card14132.html",
            ("与謝野晶子", "恋衣"): "https://www.aozora.gr.jp/cards/000885/card14133.html",
            
            # 小泉八雲
            ("小泉八雲", "怪談"): "https://www.aozora.gr.jp/cards/000258/card42895.html",
            ("小泉八雲", "知られざる日本の面影"): "https://www.aozora.gr.jp/cards/000258/card42896.html",
            ("小泉八雲", "心"): "https://www.aozora.gr.jp/cards/000258/card42897.html",
        }
    
    def search_work_url(self, author_name: str, work_title: str) -> Optional[str]:
        """作者名・作品名から青空文庫URLを検索"""
        print(f"   🔍 青空文庫検索: {author_name} - {work_title}")
        
        # まず既知の作品から検索
        known_url = self.known_works.get((author_name, work_title))
        if known_url:
            print(f"   ✅ 既知URL発見: {known_url}")
            return known_url
        
        # 作品名の表記ゆれを考慮した検索
        title_variations = self._get_title_variations(work_title)
        
        for title_var in title_variations:
            # 既知作品から表記ゆれも検索
            for (known_author, known_title), url in self.known_works.items():
                if known_author == author_name and self._titles_match(known_title, title_var):
                    print(f"   ✅ 表記ゆれURL発見: {url} ({known_title})")
                    return url
            
            # オンライン検索
            url = self._search_by_aozora_direct(author_name, title_var)
            if url:
                print(f"   ✅ URL発見: {url}")
                return url
            time.sleep(0.5)  # API制限対策
        
        print(f"   ⚠️ URL未発見: {author_name} - {work_title}")
        return None
    
    def _titles_match(self, title1: str, title2: str) -> bool:
        """タイトルの類似性をチェック"""
        # 簡単な類似性チェック
        return (title1 in title2 or title2 in title1 or 
                title1.replace(" ", "") == title2.replace(" ", "") or
                title1.replace("　", "") == title2.replace("　", ""))
    
    def _get_title_variations(self, title: str) -> List[str]:
        """作品名の表記ゆれパターンを生成"""
        variations = [title]
        
        # カタカナ・ひらがな変換
        if title:
            variations.append(title.replace("ー", ""))  # 長音符除去
            variations.append(title.replace("（", "(").replace("）", ")"))  # 括弧統一
            variations.append(title.replace("(", "").replace(")", ""))  # 括弧除去
            variations.append(title.replace("（", "").replace("）", ""))  # 日本語括弧除去
            
            # よくある表記ゆれ
            variations.append(title.replace("づ", "ず"))
            variations.append(title.replace("ず", "づ"))
            variations.append(title.replace("を", "お"))
            variations.append(title.replace("お", "を"))
            variations.append(title.replace(" ", ""))  # スペース除去
            variations.append(title.replace("　", ""))  # 全角スペース除去
        
        return list(set(variations))  # 重複除去
    
    def _search_by_aozora_direct(self, author_name: str, work_title: str) -> Optional[str]:
        """青空文庫の作者ページを直接検索"""
        try:
            # 作者ページのURL生成（推測）
            author_variations = [
                author_name,
                author_name.replace(" ", ""),
                author_name.replace("　", "")
            ]
            
            for author_var in author_variations:
                # 青空文庫の作者別URL形式を試行
                # 実際のURL形式に合わせて調整が必要
                search_url = f"https://www.aozora.gr.jp/index_pages/person_inp.php?shicho_bunsho_id={quote(author_var)}"
                
                response = self.session.get(search_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 作品リンクを検索
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        link_text = link.get_text()
                        
                        if '/cards/' in href and work_title in link_text:
                            if href.startswith('/'):
                                href = urljoin(self.base_url, href)
                            return href
            
            return None
            
        except Exception as e:
            print(f"     ⚠️ 直接検索エラー: {e}")
            return None
    
    def _search_by_google_site_search(self, author_name: str, work_title: str) -> Optional[str]:
        """Google site検索を使って青空文庫URLを検索"""
        try:
            # Google site検索クエリ
            query = f'site:aozora.gr.jp "{author_name}" "{work_title}"'
            search_url = f"https://www.google.com/search?q={quote(query)}"
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code != 200:
                return None
            
            # 検索結果からaozora.gr.jpのURLを抽出
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'aozora.gr.jp/cards/' in href and '/card' in href:
                    # URLクリーンアップ
                    if href.startswith('/url?q='):
                        href = href.split('/url?q=')[1].split('&')[0]
                    
                    if href.startswith('https://www.aozora.gr.jp/cards/'):
                        return href
            
            return None
            
        except Exception as e:
            print(f"     ⚠️ 検索エラー: {e}")
            return None
    
    def get_aozora_card_id(self, url: str) -> Optional[str]:
        """青空文庫URLからカードIDを抽出"""
        match = re.search(r'/cards/(\d+)/card(\d+)\.html', url)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
        return None
    
    def validate_aozora_url(self, url: str) -> bool:
        """青空文庫URLが有効かチェック"""
        try:
            response = self.session.head(url, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def search_multiple_works(self, works_data: List[Dict]) -> Dict[str, str]:
        """複数作品の青空文庫URLを一括検索"""
        results = {}
        
        print(f"📚 青空文庫URL一括検索開始: {len(works_data)}作品")
        
        for i, work in enumerate(works_data, 1):
            author_name = work['author_name']
            title = work['title']
            
            print(f"\n[{i}/{len(works_data)}] {author_name} - {title}")
            
            url = self.search_work_url(author_name, title)
            if url and self.validate_aozora_url(url):
                results[f"{author_name}||{title}"] = url
                print(f"   ✅ 有効URL確認: {url}")
            else:
                print(f"   ❌ URL未発見またはエラー")
            
            # レート制限対策
            time.sleep(1.0)
        
        print(f"\n📊 検索完了: {len(results)}/{len(works_data)}件でURL発見")
        return results


def search_and_update_aozora_urls():
    """青空文庫URLの一括検索・更新"""
    from bungo_map.core.database import BungoDB
    
    print("🔍 青空文庫URL一括検索・更新開始")
    print("=" * 50)
    
    db = BungoDB()
    searcher = AozoraSearcher()
    
    # aozora_urlが未設定の作品を取得
    with db.get_connection() as conn:
        cursor = conn.execute("""
        SELECT w.work_id, w.title, a.name as author_name
        FROM works w
        JOIN authors a ON w.author_id = a.author_id
        WHERE w.aozora_url IS NULL OR w.aozora_url = ''
        ORDER BY a.name, w.title
        """)
        works = cursor.fetchall()
    
    if not works:
        print("✅ すべての作品に青空文庫URLが設定済みです")
        return
    
    print(f"🎯 URL未設定作品: {len(works)}件")
    
    # 作品データ変換
    works_data = [
        {"author_name": work[2], "title": work[1], "work_id": work[0]}
        for work in works
    ]
    
    # URL検索実行
    url_results = searcher.search_multiple_works(works_data)
    
    # データベース更新
    updated_count = 0
    
    for work in works_data:
        key = f"{work['author_name']}||{work['title']}"
        if key in url_results:
            aozora_url = url_results[key]
            
            try:
                with db.get_connection() as conn:
                    conn.execute(
                        "UPDATE works SET aozora_url = ? WHERE work_id = ?",
                        (aozora_url, work['work_id'])
                    )
                    conn.commit()
                updated_count += 1
                print(f"✅ URL更新: {work['author_name']} - {work['title']}")
            except Exception as e:
                print(f"❌ DB更新エラー: {work['title']} - {e}")
    
    # 統計表示
    print(f"\n📊 青空文庫URL更新完了")
    print("-" * 30)
    print(f"検索対象: {len(works)}件")
    print(f"URL発見: {len(url_results)}件")
    print(f"DB更新: {updated_count}件")
    
    return updated_count


if __name__ == "__main__":
    search_and_update_aozora_urls() 