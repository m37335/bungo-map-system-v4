"""
Bungo Map v4.0 - 文豪地図システム

v3.0基盤システム + v4.0センテンス中心アーキテクチャの統合版

主要機能:
- センテンス中心のデータベース設計
- 複数地名抽出器の統合
- 重複排除・正規化機能
- 双方向検索機能
- 高速クエリ・ビュー提供
"""

# コアシステム
from .core.models import Place
from .core.database import Database as V3Database, BungoDB

# 抽出器システム (v3.0統合)
from .extractors.simple_place_extractor import SimplePlaceExtractor
from .extractors.enhanced_place_extractor import EnhancedPlaceExtractor
from .extractors.sentence_extractor import SentenceBasedExtractor, ExtractedPlace

# データベースシステム (v4.0)
from .database.models import Sentence, PlaceMaster, SentencePlace, DatabaseConnection
from .database.manager import DatabaseManager
from .database.schema_manager import SchemaManager

# ユーティリティ
from .utils.aozora_text_cleaner import clean_aozora_sentence
from .utils.logger import setup_logger

__version__ = "4.0.0"
__author__ = "Bungo Map Team"

__all__ = [
    # v3.0 基盤システム
    "Place",
    "V3Database",
    "BungoDB", 
    "SimplePlaceExtractor",
    "EnhancedPlaceExtractor",
    
    # v4.0 システム
    "Sentence",
    "PlaceMaster",
    "SentencePlace",
    "DatabaseConnection",
    "DatabaseManager",
    "SchemaManager",
    "SentenceBasedExtractor",
    "ExtractedPlace",
    
    # ユーティリティ
    "clean_aozora_sentence",
    "setup_logger",
] 