from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# 作者関連のモデル
class AuthorBase(BaseModel):
    """作者の基本情報"""
    author_name: str = Field(..., description="作者名")
    birth_year: Optional[int] = Field(None, description="生年")
    death_year: Optional[int] = Field(None, description="没年")
    period: Optional[str] = Field(None, description="時代（明治・大正・昭和・平成）")
    wikipedia_url: Optional[str] = Field(None, description="WikipediaのURL")
    description: Optional[str] = Field(None, description="説明")

class AuthorCreate(AuthorBase):
    """作者作成用のモデル"""
    pass

class AuthorResponse(AuthorBase):
    """作者レスポンス用のモデル"""
    author_id: int
    works_count: int = 0
    total_sentences: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# 作品関連のモデル
class WorkBase(BaseModel):
    """作品の基本情報"""
    work_title: str = Field(..., description="作品名")
    author_id: int = Field(..., description="作者ID")
    publication_year: Optional[int] = Field(None, description="出版年")
    genre: Optional[str] = Field(None, description="ジャンル")
    description: Optional[str] = Field(None, description="説明")

class WorkCreate(WorkBase):
    """作品作成用のモデル"""
    pass

class WorkResponse(WorkBase):
    """作品レスポンス用のモデル"""
    work_id: int
    sentence_count: int = 0
    place_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# センテンス関連のモデル
class SentenceBase(BaseModel):
    """センテンスの基本情報"""
    text: str = Field(..., description="テキスト")
    work_id: int = Field(..., description="作品ID")
    author_id: int = Field(..., description="作者ID")
    before_text: Optional[str] = Field(None, description="前の文脈")
    after_text: Optional[str] = Field(None, description="後の文脈")
    source_info: Optional[str] = Field(None, description="出典情報")
    sentence_length: int = Field(0, description="文の長さ")

class SentenceCreate(SentenceBase):
    """センテンス作成用のモデル"""
    work_title: str = Field(..., description="作品名")
    author_name: str = Field(..., description="作者名")

class SentenceResponse(SentenceBase):
    """センテンスレスポンス用のモデル"""
    sentence_id: int
    place_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# 地名関連のモデル
class PlaceBase(BaseModel):
    """地名の基本情報"""
    place_name: str = Field(..., description="地名")
    latitude: Optional[float] = Field(None, description="緯度")
    longitude: Optional[float] = Field(None, description="経度")
    confidence: float = Field(0.0, description="信頼度")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="メタデータ")

class PlaceResponse(PlaceBase):
    """地名レスポンス用のモデル"""
    place_id: int
    mention_count: int = 0
    author_count: int = 0
    work_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# 統計情報のモデル
class AuthorStats(BaseModel):
    """作者の統計情報"""
    works_count: int
    total_sentences: int
    total_places: int
    unique_places: int

class WorkStats(BaseModel):
    """作品の統計情報"""
    sentence_count: int
    place_count: int
    unique_places: int
    average_confidence: float
