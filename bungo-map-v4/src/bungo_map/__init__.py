"""
Bungo Map v4.0 - 文豪地図システム

センテンス中心アーキテクチャによる文豪作品の地名抽出・可視化システム

主要機能:
- センテンス中心のデータベース設計
- 複数地名抽出器の統合
- 重複排除・正規化機能
- 双方向検索機能
- 高速クエリ・ビュー提供
"""

# データベースシステム
from .database.models import Sentence, PlaceMaster, SentencePlace, DatabaseConnection
from .database.manager import DatabaseManager
from .database.schema_manager import SchemaManager

# 抽出器システム
from .extractors.aozora_scraper import AozoraScraper

# ユーティリティ
from .utils.aozora_text_cleaner import clean_aozora_sentence
from .utils.logger import setup_logger

__version__ = "4.0.0"
__author__ = "Bungo Map Team"

__all__ = [
    # データベースシステム
    "Sentence",
    "PlaceMaster",
    "SentencePlace",
    "DatabaseConnection",
    "DatabaseManager",
    "SchemaManager",
    
    # 抽出器システム
    "AozoraScraper",
    
    # ユーティリティ
    "clean_aozora_sentence",
    "setup_logger",
] 