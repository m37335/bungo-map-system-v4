#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データモデル定義
作者・作品・地名の3階層構造
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Author:
    """作者モデル"""
    author_id: Optional[int] = None
    name: str = ""
    wikipedia_url: Optional[str] = None
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class Work:
    """作品モデル"""
    work_id: Optional[int] = None
    author_id: Optional[int] = None
    title: str = ""
    wiki_url: Optional[str] = None
    aozora_url: Optional[str] = None
    content: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Place:
    """地名モデル"""
    place_id: Optional[int] = None
    work_id: Optional[int] = None
    place_name: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    before_text: Optional[str] = None
    sentence: Optional[str] = None
    after_text: Optional[str] = None
    aozora_url: Optional[str] = None
    confidence: float = 0.0
    extraction_method: Optional[str] = None
    created_at: Optional[datetime] = None 