from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Author(Base):
    """作者モデル"""
    __tablename__ = "authors"

    author_id = Column(Integer, primary_key=True, index=True)
    author_name = Column(String(255), unique=True, nullable=False, index=True)
    author_name_kana = Column(String(255))
    birth_year = Column(Integer)
    death_year = Column(Integer)
    period = Column(String(50))  # 明治・大正・昭和・平成
    wikipedia_url = Column(String(512))
    description = Column(Text)
    portrait_url = Column(String(512))
    
    # 統計情報
    works_count = Column(Integer, default=0)
    total_sentences = Column(Integer, default=0)
    
    # メタデータ
    source_system = Column(String(50), default="v4.0")
    verification_status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ
    works = relationship("Work", back_populates="author")
    sentences = relationship("Sentence", back_populates="author")

class Work(Base):
    """作品モデル"""
    __tablename__ = "works"

    work_id = Column(Integer, primary_key=True, index=True)
    work_title = Column(String(255), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("authors.author_id"), nullable=False)
    publication_year = Column(Integer)
    genre = Column(String(50))  # 小説、随筆、詩、戯曲
    aozora_url = Column(String(512))
    file_path = Column(String(512))
    content_length = Column(Integer, default=0)
    sentence_count = Column(Integer, default=0)
    place_count = Column(Integer, default=0)
    
    # 青空文庫情報
    aozora_work_id = Column(String(50))
    card_id = Column(String(50))
    copyright_status = Column(String(50))
    input_person = Column(String(100))
    proof_person = Column(String(100))
    
    # メタデータ
    source_system = Column(String(50), default="v4.0")
    processing_status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ
    author = relationship("Author", back_populates="works")
    sentences = relationship("Sentence", back_populates="work")

class Sentence(Base):
    """センテンスモデル"""
    __tablename__ = "sentences"

    sentence_id = Column(Integer, primary_key=True, index=True)
    sentence_text = Column(Text, nullable=False)
    work_id = Column(Integer, ForeignKey("works.work_id"), nullable=False)
    author_id = Column(Integer, ForeignKey("authors.author_id"), nullable=False)
    before_text = Column(Text)
    after_text = Column(Text)
    source_info = Column(String(255))
    sentence_length = Column(Integer, default=0)
    
    # 品質情報
    quality_score = Column(Float, default=0.0)
    place_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ
    work = relationship("Work", back_populates="sentences")
    author = relationship("Author", back_populates="sentences")
    places = relationship("SentencePlace", back_populates="sentence")

class Place(Base):
    """地名モデル"""
    __tablename__ = "places"

    place_id = Column(Integer, primary_key=True, index=True)
    place_name = Column(String(255), unique=True, nullable=False, index=True)
    canonical_name = Column(String(255), nullable=False)
    aliases = Column(JSON)  # JSON配列: ["京都府","京都","みやこ"]
    latitude = Column(Float)
    longitude = Column(Float)
    place_type = Column(String(50))  # 都道府県、市区町村、有名地名、郡、歴史地名、外国、架空地名
    confidence = Column(Float, default=0.0)
    description = Column(Text)
    wikipedia_url = Column(String(512))
    image_url = Column(String(512))
    
    # 地理情報
    country = Column(String(100), default="日本")
    prefecture = Column(String(100))
    municipality = Column(String(100))
    district = Column(String(100))
    
    # 統計情報
    mention_count = Column(Integer, default=0)
    author_count = Column(Integer, default=0)
    work_count = Column(Integer, default=0)
    
    # メタデータ
    source_system = Column(String(50), default="v4.0")
    verification_status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ
    sentence_places = relationship("SentencePlace", back_populates="place")

class SentencePlace(Base):
    """センテンス-地名関連モデル"""
    __tablename__ = "sentence_places"

    id = Column(Integer, primary_key=True, index=True)
    sentence_id = Column(Integer, ForeignKey("sentences.sentence_id"), nullable=False)
    place_id = Column(Integer, ForeignKey("places.place_id"), nullable=False)
    
    # 抽出情報
    extraction_method = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.0)
    position_in_sentence = Column(Integer)
    
    # 文脈情報
    context_before = Column(Text)
    context_after = Column(Text)
    matched_text = Column(String(255))
    
    # 品質管理
    verification_status = Column(String(20), default="auto")
    quality_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ
    sentence = relationship("Sentence", back_populates="places")
    place = relationship("Place", back_populates="sentence_places")

    # ユニーク制約
    __table_args__ = (
        UniqueConstraint('sentence_id', 'place_id', name='uix_sentence_place'),
    )
