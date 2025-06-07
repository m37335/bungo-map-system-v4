#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪ゆかり地図システム v2.0
日本の文豪とその作品に登場する地名を体系的に収集・管理し、地図上で可視化するためのシステム

主要機能:
- Wikipedia + 青空文庫からの自動データ抽出
- GiNZA NLP + MeCab による高精度地名認識  
- Google Maps API による緯度経度取得
- 作者・作品・地名の相互検索
- GeoJSON、CSV、Excel形式でのデータエクスポート
- FastAPI による高性能REST API提供
"""

__version__ = "2.0.0"
__author__ = "Masa"
__email__ = "masa@example.com"
__description__ = "文豪ゆかり地図システム - 作家・作品・舞台地名の3階層データ管理システム"

# パッケージレベルの公開API
from bungo_map.core.database import Database
from bungo_map.core.models import Author, Work, Place

__all__ = [
    "Database",
    "Author", 
    "Work",
    "Place",
    "__version__",
] 