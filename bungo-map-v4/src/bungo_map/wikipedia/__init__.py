# -*- coding: utf-8 -*-
"""
Wikipedia統合システム v4
作者情報自動抽出・補完機能
"""

from .wikipedia_extractor import WikipediaExtractor
from .wikipedia_data_completion import WikipediaDataCompletion

__all__ = [
    'WikipediaExtractor',
    'WikipediaDataCompletion'
] 