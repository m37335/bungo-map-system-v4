"""
データベースモデル

データベースのモデルクラスを定義
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Author:
    """作者モデル"""
    author_name: str
    source_system: str
    author_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Work:
    """作品モデル"""
    work_title: str
    author_id: int
    aozora_url: str
    source_system: str
    work_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Sentence:
    """センテンスモデル"""
    sentence_text: str
    work_id: int
    author_id: int
    position_in_work: int
    sentence_length: int
    sentence_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None 