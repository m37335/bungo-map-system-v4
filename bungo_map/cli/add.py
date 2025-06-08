#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手動データ追加CLI
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from bungo_map.core.database import Database
from bungo_map.utils.logger import setup_logger

console = Console()
logger = setup_logger(__name__)


@click.group()
def add():
    """✏️ 手動データ追加コマンド"""
    pass


@add.command()
@click.option('--name', required=True, help='作者名')
@click.option('--birth-year', type=int, help='生年')
@click.option('--death-year', type=int, help='没年')
@click.option('--wikipedia-url', help='Wikipedia URL')
@click.option('--interactive', '-i', is_flag=True, help='対話式入力')
def author(name: str, birth_year: Optional[int], death_year: Optional[int], 
           wikipedia_url: Optional[str], interactive: bool):
    """👨‍💼 作者を手動追加"""
    
    if interactive:
        console.print("📝 作者情報を入力してください", style="blue")
        name = Prompt.ask("作者名", default=name)
        birth_year = Prompt.ask("生年", default=str(birth_year) if birth_year else "", show_default=False)
        death_year = Prompt.ask("没年", default=str(death_year) if death_year else "", show_default=False)
        wikipedia_url = Prompt.ask("Wikipedia URL", default=wikipedia_url or "", show_default=False)
        
        # Convert to int or None
        birth_year = int(birth_year) if birth_year else None
        death_year = int(death_year) if death_year else None
        wikipedia_url = wikipedia_url if wikipedia_url else None
    
    try:
        db = Database()
        author_id = db.add_author(
            name=name,
            birth_year=birth_year,
            death_year=death_year,
            wikipedia_url=wikipedia_url
        )
        
        if author_id:
            console.print(f"✅ 作者を追加しました: {name} (ID: {author_id})", style="green")
            
            # 追加した作者の詳細表示
            table = Table(title=f"追加された作者情報")
            table.add_column("項目", style="cyan")
            table.add_column("値", style="magenta")
            
            table.add_row("作者ID", str(author_id))
            table.add_row("名前", name)
            table.add_row("生年", str(birth_year) if birth_year else "-")
            table.add_row("没年", str(death_year) if death_year else "-")
            table.add_row("Wikipedia URL", wikipedia_url if wikipedia_url else "-")
            
            console.print(table)
        else:
            console.print(f"❌ 作者の追加に失敗しました", style="red")
            
    except Exception as e:
        console.print(f"❌ エラー: {e}", style="red")
        logger.exception("Author addition failed")


@add.command()
@click.option('--title', required=True, help='作品名')
@click.option('--author', required=True, help='作者名')
@click.option('--publication-year', type=int, help='出版年')
@click.option('--wiki-url', help='Wikipedia URL')
@click.option('--aozora-url', help='青空文庫URL')
@click.option('--text-url', help='テキストファイルURL')
@click.option('--content', help='作品本文（ファイルパス指定）')
@click.option('--interactive', '-i', is_flag=True, help='対話式入力')
def work(title: str, author: str, publication_year: Optional[int], 
         wiki_url: Optional[str], aozora_url: Optional[str], text_url: Optional[str],
         content: Optional[str], interactive: bool):
    """📖 作品を手動追加"""
    
    if interactive:
        console.print("📝 作品情報を入力してください", style="blue")
        title = Prompt.ask("作品名", default=title)
        author = Prompt.ask("作者名", default=author)
        publication_year = Prompt.ask("出版年", default=str(publication_year) if publication_year else "", show_default=False)
        wiki_url = Prompt.ask("Wikipedia URL", default=wiki_url or "", show_default=False)
        aozora_url = Prompt.ask("青空文庫URL", default=aozora_url or "", show_default=False)
        text_url = Prompt.ask("テキストファイルURL", default=text_url or "", show_default=False)
        content = Prompt.ask("作品本文ファイルパス", default=content or "", show_default=False)
        
        # Convert to appropriate types
        publication_year = int(publication_year) if publication_year else None
        wiki_url = wiki_url if wiki_url else None
        aozora_url = aozora_url if aozora_url else None
        text_url = text_url if text_url else None
        content = content if content else None
    
    try:
        db = Database()
        
        # 作者IDを取得
        authors = db.search_authors(author, limit=1)
        if not authors:
            console.print(f"❌ 作者 '{author}' が見つかりません", style="red")
            console.print("💡 まず作者を追加してください: python main.py add author --name '{author}'", style="yellow")
            return
        
        author_id = authors[0]['author_id']
        
        # 作品を追加
        work_id = db.add_work(
            title=title,
            author_id=author_id,
            publication_year=publication_year,
            wiki_url=wiki_url,
            aozora_url=aozora_url,
            text_url=text_url
        )
        
        # 本文を追加（ファイルから読み込み）
        if work_id and content:
            try:
                from pathlib import Path
                content_path = Path(content)
                if content_path.exists():
                    with open(content_path, 'r', encoding='utf-8') as f:
                        content_text = f.read()
                    db.set_work_content(work_id, content_text)
                    console.print(f"📄 本文を追加しました: {content_path}", style="green")
                else:
                    console.print(f"⚠️ ファイルが見つかりません: {content}", style="yellow")
            except Exception as e:
                console.print(f"⚠️ 本文追加エラー: {e}", style="yellow")
        
        if work_id:
            console.print(f"✅ 作品を追加しました: {title} (ID: {work_id})", style="green")
            
            # 追加した作品の詳細表示
            table = Table(title="追加された作品情報")
            table.add_column("項目", style="cyan")
            table.add_column("値", style="magenta")
            
            table.add_row("作品ID", str(work_id))
            table.add_row("タイトル", title)
            table.add_row("作者", author)
            table.add_row("出版年", str(publication_year) if publication_year else "-")
            table.add_row("Wikipedia URL", wiki_url if wiki_url else "-")
            table.add_row("青空文庫URL", aozora_url if aozora_url else "-")
            table.add_row("テキストURL", text_url if text_url else "-")
            table.add_row("本文", "あり" if content else "なし")
            
            console.print(table)
        else:
            console.print(f"❌ 作品の追加に失敗しました", style="red")
            
    except Exception as e:
        console.print(f"❌ エラー: {e}", style="red")
        logger.exception("Work addition failed")


@add.command()
@click.option('--name', required=True, help='地名')
@click.option('--work-title', required=True, help='作品名')
@click.option('--author', required=True, help='作者名')
@click.option('--lat', type=float, help='緯度')
@click.option('--lng', type=float, help='経度')
@click.option('--context', help='文脈（前後の文章）')
@click.option('--confidence', type=float, default=0.8, help='信頼度 (0.0-1.0)')
@click.option('--interactive', '-i', is_flag=True, help='対話式入力')
def place(name: str, work_title: str, author: str, lat: Optional[float], lng: Optional[float],
          context: Optional[str], confidence: float, interactive: bool):
    """🗺️ 地名を手動追加"""
    
    if interactive:
        console.print("📝 地名情報を入力してください", style="blue")
        name = Prompt.ask("地名", default=name)
        work_title = Prompt.ask("作品名", default=work_title)
        author = Prompt.ask("作者名", default=author)
        lat = Prompt.ask("緯度", default=str(lat) if lat else "", show_default=False)
        lng = Prompt.ask("経度", default=str(lng) if lng else "", show_default=False)
        context = Prompt.ask("文脈", default=context or "", show_default=False)
        confidence = Prompt.ask("信頼度(0.0-1.0)", default=str(confidence), show_default=False)
        
        # Convert to appropriate types
        lat = float(lat) if lat else None
        lng = float(lng) if lng else None
        context = context if context else None
        confidence = float(confidence) if confidence else 0.8
    
    try:
        db = Database()
        
        # 作品IDを取得
        works = db.search_works(f"{author} {work_title}", limit=5)
        matching_work = None
        
        for work in works:
            if work['author_name'] == author and work['title'] == work_title:
                matching_work = work
                break
        
        if not matching_work:
            console.print(f"❌ 作品 '{work_title}' (作者: {author}) が見つかりません", style="red")
            console.print("💡 まず作品を追加してください", style="yellow")
            return
        
        work_id = matching_work['work_id']
        
        # 地名を追加（直接SQL実行）
        with db.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO places (work_id, place_name, lat, lng, sentence, confidence, extraction_method)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (work_id, name, lat, lng, context, confidence, "manual")
            )
            conn.commit()
            place_id = cursor.lastrowid
        
        if place_id:
            console.print(f"✅ 地名を追加しました: {name} (ID: {place_id})", style="green")
            
            # 追加した地名の詳細表示
            table = Table(title="追加された地名情報")
            table.add_column("項目", style="cyan")
            table.add_column("値", style="magenta")
            
            table.add_row("地名ID", str(place_id))
            table.add_row("地名", name)
            table.add_row("作品", work_title)
            table.add_row("作者", author)
            table.add_row("緯度", str(lat) if lat else "-")
            table.add_row("経度", str(lng) if lng else "-")
            table.add_row("文脈", context if context else "-")
            table.add_row("信頼度", str(confidence))
            
            console.print(table)
        else:
            console.print(f"❌ 地名の追加に失敗しました", style="red")
            
    except Exception as e:
        console.print(f"❌ エラー: {e}", style="red")
        logger.exception("Place addition failed")


@add.command()
def template():
    """📋 追加用テンプレートを表示"""
    
    console.print("📋 データ追加テンプレート", style="blue")
    
    console.print("\n1️⃣ 作者追加:", style="green")
    console.print("python main.py add author --name '新作者名' --birth-year 1900 --death-year 1970")
    console.print("python main.py add author --interactive  # 対話式")
    
    console.print("\n2️⃣ 作品追加:", style="green")
    console.print("python main.py add work --title '新作品名' --author '作者名' --publication-year 1950")
    console.print("python main.py add work --interactive  # 対話式")
    
    console.print("\n3️⃣ 地名追加:", style="green")
    console.print("python main.py add place --name '地名' --work-title '作品名' --author '作者名' --lat 35.6762 --lng 139.6503")
    console.print("python main.py add place --interactive  # 対話式")
    
    console.print("\n📝 使用例:", style="yellow")
    console.print("# 1. 作者追加")
    console.print("python main.py add author --name '田中太郎' --birth-year 1920 --death-year 1980")
    console.print("\n# 2. 作品追加") 
    console.print("python main.py add work --title '新しい物語' --author '田中太郎' --publication-year 1955")
    console.print("\n# 3. 地名追加")
    console.print("python main.py add place --name '東京駅' --work-title '新しい物語' --author '田中太郎' --lat 35.6812 --lng 139.7671")


if __name__ == '__main__':
    add() 