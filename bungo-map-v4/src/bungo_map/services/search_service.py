"""
Bungo Map v4.0 Search Service

高度な検索機能を提供するサービス層
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from ..database.manager import DatabaseManager
from ..database.models import Sentence, PlaceMaster, SentencePlace
from ..core.config import config


@dataclass
class SearchResult:
    """検索結果データ"""
    sentences: List[Sentence]
    places: List[PlaceMaster] 
    relations: List[SentencePlace]
    total_count: int
    query_time_ms: float


@dataclass
class SearchOptions:
    """検索オプション"""
    limit: int = 50
    offset: int = 0
    min_confidence: float = 0.0
    place_types: Optional[List[str]] = None
    extraction_methods: Optional[List[str]] = None
    work_ids: Optional[List[int]] = None
    author_ids: Optional[List[int]] = None


class SearchService:
    """検索サービス"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager(str(config.get_database_path()))
    
    def search_by_place_name(self, place_name: str, options: SearchOptions = None) -> SearchResult:
        """地名による検索"""
        import time
        start_time = time.time()
        
        options = options or SearchOptions()
        
        # 地名検索
        place = self.db_manager.find_place_by_name(place_name)
        if not place:
            return SearchResult([], [], [], 0, (time.time() - start_time) * 1000)
        
        # 関連センテンス取得
        sentence_relations = self.db_manager.get_sentences_by_place(place.place_id)
        
        # オプション適用
        filtered_relations = self._apply_search_options(sentence_relations, options)
        
        sentences = [relation[0] for relation in filtered_relations]
        relations = [relation[1] for relation in filtered_relations]
        
        query_time = (time.time() - start_time) * 1000
        
        return SearchResult(
            sentences=sentences,
            places=[place],
            relations=relations,
            total_count=len(sentences),
            query_time_ms=query_time
        )
    
    def search_by_sentence_text(self, text: str, options: SearchOptions = None) -> SearchResult:
        """センテンステキストによる検索"""
        import time
        start_time = time.time()
        
        options = options or SearchOptions()
        
        # センテンス検索
        sentences = self.db_manager.search_sentences(text, limit=options.limit)
        
        # 各センテンスの関連地名取得
        all_places = []
        all_relations = []
        
        for sentence in sentences:
            place_relations = self.db_manager.get_places_by_sentence(sentence.sentence_id)
            filtered_relations = self._apply_search_options(place_relations, options)
            
            all_places.extend([relation[0] for relation in filtered_relations])
            all_relations.extend([relation[1] for relation in filtered_relations])
        
        # 重複除去
        unique_places = list({place.place_id: place for place in all_places}.values())
        
        query_time = (time.time() - start_time) * 1000
        
        return SearchResult(
            sentences=sentences,
            places=unique_places,
            relations=all_relations,
            total_count=len(sentences),
            query_time_ms=query_time
        )
    
    def advanced_search(self, 
                       place_name: Optional[str] = None,
                       sentence_text: Optional[str] = None,
                       options: SearchOptions = None) -> SearchResult:
        """高度な複合検索"""
        import time
        start_time = time.time()
        
        options = options or SearchOptions()
        
        if place_name and sentence_text:
            # 両方指定：交差検索
            place_result = self.search_by_place_name(place_name, options)
            text_result = self.search_by_sentence_text(sentence_text, options)
            
            # 交差する結果を取得
            place_sentence_ids = {s.sentence_id for s in place_result.sentences}
            text_sentence_ids = {s.sentence_id for s in text_result.sentences}
            common_ids = place_sentence_ids & text_sentence_ids
            
            # 共通センテンスのみ抽出
            sentences = [s for s in place_result.sentences if s.sentence_id in common_ids]
            relations = [r for r in place_result.relations if r.sentence_id in common_ids]
            
        elif place_name:
            result = self.search_by_place_name(place_name, options)
            sentences, relations = result.sentences, result.relations
            
        elif sentence_text:
            result = self.search_by_sentence_text(sentence_text, options)
            sentences, relations = result.sentences, result.relations
            
        else:
            # 全件取得（制限付き）
            sentences = self.db_manager.search_sentences("", limit=options.limit)
            relations = []
            
        query_time = (time.time() - start_time) * 1000
        
        return SearchResult(
            sentences=sentences,
            places=list({r.place_id: self.db_manager.get_place_by_id(r.place_id) 
                        for r in relations}.values()),
            relations=relations,
            total_count=len(sentences),
            query_time_ms=query_time
        )
    
    def _apply_search_options(self, relations: List[Tuple], options: SearchOptions) -> List[Tuple]:
        """検索オプションを適用"""
        filtered = relations
        
        # 信頼度フィルタ
        if options.min_confidence > 0:
            filtered = [r for r in filtered if r[1].confidence >= options.min_confidence]
        
        # 地名タイプフィルタ
        if options.place_types:
            filtered = [r for r in filtered if r[0].place_type in options.place_types]
        
        # 抽出手法フィルタ
        if options.extraction_methods:
            filtered = [r for r in filtered if r[1].extraction_method in options.extraction_methods]
        
        # 作品IDフィルタ
        if options.work_ids:
            filtered = [r for r in filtered if r[0].work_id in options.work_ids]
        
        # ページング
        start = options.offset
        end = start + options.limit
        
        return filtered[start:end] 