"""
Bungo Map System v4.0 Data Models

センテンス中心アーキテクチャのデータモデル定義
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Sentence:
    """センテンスモデル - メインエンティティ"""
    sentence_id: Optional[int] = None
    sentence_text: str = ""
    work_id: int = 0
    author_id: int = 0
    before_text: Optional[str] = None
    after_text: Optional[str] = None
    source_info: Optional[str] = None
    chapter: Optional[str] = None
    page_number: Optional[int] = None
    position_in_work: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'sentence_id': self.sentence_id,
            'sentence_text': self.sentence_text,
            'work_id': self.work_id,
            'author_id': self.author_id,
            'before_text': self.before_text,
            'after_text': self.after_text,
            'source_info': self.source_info,
            'chapter': self.chapter,
            'page_number': self.page_number,
            'position_in_work': self.position_in_work,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class PlaceMaster:
    """地名マスターモデル - 正規化済み地名情報"""
    place_id: Optional[int] = None
    place_name: str = ""
    canonical_name: str = ""
    aliases: List[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_type: str = "有名地名"  # 都道府県/市区町村/有名地名/郡/歴史地名
    confidence: float = 0.0
    description: Optional[str] = None
    wikipedia_url: Optional[str] = None
    image_url: Optional[str] = None
    prefecture: Optional[str] = None
    municipality: Optional[str] = None
    district: Optional[str] = None
    source_system: str = "v4.0"
    verification_status: str = "pending"  # pending/verified/rejected
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
        if not self.canonical_name:
            self.canonical_name = self.place_name
    
    def get_aliases_json(self) -> str:
        """別名をJSON文字列で取得"""
        return json.dumps(self.aliases, ensure_ascii=False)
    
    def set_aliases_from_json(self, aliases_json: str):
        """JSON文字列から別名を設定"""
        try:
            self.aliases = json.loads(aliases_json) if aliases_json else []
        except json.JSONDecodeError:
            self.aliases = []
    
    def add_alias(self, alias: str):
        """別名を追加"""
        if alias and alias not in self.aliases and alias != self.place_name:
            self.aliases.append(alias)
    
    def matches_name(self, name: str) -> bool:
        """名前が一致するかチェック（本名・別名両方）"""
        return (name == self.place_name or 
                name == self.canonical_name or 
                name in self.aliases)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'place_id': self.place_id,
            'place_name': self.place_name,
            'canonical_name': self.canonical_name,
            'aliases': self.aliases,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'place_type': self.place_type,
            'confidence': self.confidence,
            'description': self.description,
            'wikipedia_url': self.wikipedia_url,
            'image_url': self.image_url,
            'prefecture': self.prefecture,
            'municipality': self.municipality,
            'district': self.district,
            'source_system': self.source_system,
            'verification_status': self.verification_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class SentencePlace:
    """センテンス-地名関連モデル - N:N関係"""
    id: Optional[int] = None
    sentence_id: int = 0
    place_id: int = 0
    extraction_method: str = ""
    confidence: float = 0.0
    position_in_sentence: Optional[int] = None
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    matched_text: Optional[str] = None
    verification_status: str = "auto"  # auto/manual_verified/manual_rejected
    quality_score: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'id': self.id,
            'sentence_id': self.sentence_id,
            'place_id': self.place_id,
            'extraction_method': self.extraction_method,
            'confidence': self.confidence,
            'position_in_sentence': self.position_in_sentence,
            'context_before': self.context_before,
            'context_after': self.context_after,
            'matched_text': self.matched_text,
            'verification_status': self.verification_status,
            'quality_score': self.quality_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DatabaseConnection:
    """v4.0データベース接続管理"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
    
    def __enter__(self):
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()


def row_to_sentence(row: sqlite3.Row) -> Sentence:
    """SQLiteロウからSentenceオブジェクトに変換"""
    return Sentence(
        sentence_id=row['sentence_id'],
        sentence_text=row['sentence_text'],
        work_id=row['work_id'],
        author_id=row['author_id'],
        before_text=row['before_text'],
        after_text=row['after_text'],
        source_info=row['source_info'],
        chapter=row['chapter'],
        page_number=row['page_number'],
        position_in_work=row['position_in_work'],
        created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
        updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
    )


def row_to_place_master(row: sqlite3.Row) -> PlaceMaster:
    """SQLiteロウからPlaceMasterオブジェクトに変換"""
    place = PlaceMaster(
        place_id=row['place_id'],
        place_name=row['place_name'],
        canonical_name=row['canonical_name'],
        latitude=row['latitude'],
        longitude=row['longitude'],
        place_type=row['place_type'],
        confidence=row['confidence'],
        description=row['description'],
        wikipedia_url=row['wikipedia_url'],
        image_url=row['image_url'],
        prefecture=row['prefecture'],
        municipality=row['municipality'],
        district=row['district'],
        source_system=row['source_system'],
        verification_status=row['verification_status'],
        created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
        updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
    )
    
    # 別名をJSONから復元
    if row['aliases']:
        place.set_aliases_from_json(row['aliases'])
    
    return place


def row_to_sentence_place(row: sqlite3.Row) -> SentencePlace:
    """SQLiteロウからSentencePlaceオブジェクトに変換"""
    return SentencePlace(
        id=row['id'],
        sentence_id=row['sentence_id'],
        place_id=row['place_id'],
        extraction_method=row['extraction_method'],
        confidence=row['confidence'],
        position_in_sentence=row['position_in_sentence'],
        context_before=row['context_before'],
        context_after=row['context_after'],
        matched_text=row['matched_text'],
        verification_status=row['verification_status'],
        quality_score=row['quality_score'],
        created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
        updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
    ) 