from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from datetime import datetime

from .models import Author, Work, Sentence, Place, SentencePlace

class DatabaseManager:
    """データベース操作マネージャー"""
    
    def __init__(self, session: Session):
        self.session = session

    # Author CRUD
    def create_author(self, author_data: Dict[str, Any]) -> Author:
        """作者を作成"""
        author = Author(**author_data)
        self.session.add(author)
        self.session.commit()
        self.session.refresh(author)
        return author

    def get_author(self, author_id: int) -> Optional[Author]:
        """作者を取得"""
        return self.session.get(Author, author_id)

    def get_author_by_name(self, author_name: str) -> Optional[Author]:
        """作者名で作者を取得"""
        return self.session.query(Author).filter(Author.author_name == author_name).first()

    def update_author(self, author_id: int, author_data: Dict[str, Any]) -> Optional[Author]:
        """作者を更新"""
        author = self.get_author(author_id)
        if author:
            for key, value in author_data.items():
                setattr(author, key, value)
            author.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(author)
        return author

    # Work CRUD
    def create_work(self, work_data: Dict[str, Any]) -> Work:
        """作品を作成"""
        work = Work(**work_data)
        self.session.add(work)
        self.session.commit()
        self.session.refresh(work)
        return work

    def get_work(self, work_id: int) -> Optional[Work]:
        """作品を取得"""
        return self.session.get(Work, work_id)

    def get_works_by_author(self, author_id: int) -> List[Work]:
        """作者の作品一覧を取得"""
        return self.session.query(Work).filter(Work.author_id == author_id).all()

    def update_work(self, work_id: int, work_data: Dict[str, Any]) -> Optional[Work]:
        """作品を更新"""
        work = self.get_work(work_id)
        if work:
            for key, value in work_data.items():
                setattr(work, key, value)
            work.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(work)
        return work

    # Sentence CRUD
    def create_sentence(self, sentence_data: Dict[str, Any]) -> Sentence:
        """センテンスを作成"""
        sentence = Sentence(**sentence_data)
        self.session.add(sentence)
        self.session.commit()
        self.session.refresh(sentence)
        return sentence

    def get_sentence(self, sentence_id: int) -> Optional[Sentence]:
        """センテンスを取得"""
        return self.session.get(Sentence, sentence_id)

    def get_sentences_by_work(self, work_id: int) -> List[Sentence]:
        """作品のセンテンス一覧を取得"""
        return self.session.query(Sentence).filter(Sentence.work_id == work_id).all()

    # Place CRUD
    def create_place(self, place_data: Dict[str, Any]) -> Place:
        """地名を作成"""
        place = Place(**place_data)
        self.session.add(place)
        self.session.commit()
        self.session.refresh(place)
        return place

    def get_place(self, place_id: int) -> Optional[Place]:
        """地名を取得"""
        return self.session.get(Place, place_id)

    def get_place_by_name(self, place_name: str) -> Optional[Place]:
        """地名で地名を取得"""
        return self.session.query(Place).filter(Place.place_name == place_name).first()

    def update_place(self, place_id: int, place_data: Dict[str, Any]) -> Optional[Place]:
        """地名を更新"""
        place = self.get_place(place_id)
        if place:
            for key, value in place_data.items():
                setattr(place, key, value)
            place.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(place)
        return place

    # SentencePlace CRUD
    def create_sentence_place(self, sentence_place_data: Dict[str, Any]) -> SentencePlace:
        """センテンス-地名関連を作成"""
        sentence_place = SentencePlace(**sentence_place_data)
        self.session.add(sentence_place)
        self.session.commit()
        self.session.refresh(sentence_place)
        return sentence_place

    def get_sentence_places_by_sentence(self, sentence_id: int) -> List[SentencePlace]:
        """センテンスの地名関連一覧を取得"""
        return self.session.query(SentencePlace).filter(
            SentencePlace.sentence_id == sentence_id
        ).all()

    def get_sentence_places_by_place(self, place_id: int) -> List[SentencePlace]:
        """地名のセンテンス関連一覧を取得"""
        return self.session.query(SentencePlace).filter(
            SentencePlace.place_id == place_id
        ).all()

    # 統計情報更新
    def update_author_stats(self, author_id: int):
        """作者の統計情報を更新"""
        author = self.get_author(author_id)
        if author:
            works = self.get_works_by_author(author_id)
            author.works_count = len(works)
            author.total_sentences = sum(work.sentence_count for work in works)
            self.session.commit()

    def update_work_stats(self, work_id: int):
        """作品の統計情報を更新"""
        work = self.get_work(work_id)
        if work:
            sentences = self.get_sentences_by_work(work_id)
            work.sentence_count = len(sentences)
            work.place_count = sum(sentence.place_count for sentence in sentences)
            self.session.commit()

    def update_place_stats(self, place_id: int):
        """地名の統計情報を更新"""
        place = self.get_place(place_id)
        if place:
            sentence_places = self.get_sentence_places_by_place(place_id)
            place.mention_count = len(sentence_places)
            place.author_count = len(set(sp.sentence.author_id for sp in sentence_places))
            place.work_count = len(set(sp.sentence.work_id for sp in sentence_places))
            self.session.commit()

    def get_all_places(self):
        return self.session.query(Place).all()
