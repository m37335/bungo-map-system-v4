import click
from ..database.schema_manager import SchemaManager
from ..utils.database_utils import get_database_path
from ..aozora.aozora_scraper import AozoraScraper
from ..database.manager import DatabaseManager
from ..database.models import Sentence
import re

@click.group()
def cli():
    pass

@cli.command()
@click.option('--author', required=True, help='著者名（例: 梶井 基次郎）')
def process_author(author):
    db_path = get_database_path()
    schema_manager = SchemaManager(db_path)
    scraper = AozoraScraper()
    db_manager = DatabaseManager(db_path)

    click.echo(f"🔍 作者の作品を検索中: {author}")
    works = scraper.get_author_works(author)
    
    if not works:
        click.echo("❌ 作品が見つかりませんでした")
        return

    # 作品の保存
    for work in works:
        db_manager.save_work(work)
    
    click.echo(f"✅ 作者の処理が完了しました")
    click.echo(f"📚 保存された作品数: {len(works)}")
    
    # センテンスの取得と保存
    click.echo("🔍 センテンスを抽出中...")
    total_sentences = 0
    
    for work in works:
        # テキストの取得と正規化
        text = scraper.download_and_extract_text(work.url)
        if not text:
            continue
            
        # 文の分割（句点、感嘆符、疑問符で分割）
        sentences = re.split(r'[。！？]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for i, sentence_text in enumerate(sentences):
            sentence = Sentence(
                sentence_text=sentence_text,
                work_id=work.id,
                author_id=work.author_id,
                position_in_work=i,
                sentence_length=len(sentence_text)
            )
            db_manager.save_sentence(sentence)
        total_sentences += len(sentences)
    
    click.echo(f"✅ センテンスの抽出が完了しました")
    click.echo(f"📝 抽出されたセンテンス数: {total_sentences}")
    
    # 統計情報の表示
    stats = db_manager.get_author_stats(author)
    click.echo("\n📊 作者の統計情報")
    click.echo(f"📝 総センテンス数: {stats['total_sentences']}")
    click.echo(f"🗺️ 抽出地名数: {stats['extracted_places']}")
    click.echo(f"🌍 ジオコーディング済み: {stats['geocoded_places']}")

if __name__ == '__main__':
    cli() 