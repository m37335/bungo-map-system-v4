"""
センテンスベースの地名抽出器

文単位での地名抽出を実装
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .ginza_place_extractor import GinzaPlaceExtractor
from .simple_place_extractor import SimplePlaceExtractor
from .enhanced_place_extractor import EnhancedPlaceExtractor


@dataclass
class ExtractedPlace:
    """抽出された地名データ"""
    work_id: int
    place_name: str
    sentence: str
    before_text: str
    after_text: str
    confidence: float
    extraction_method: str
    author_id: Optional[int] = None
    metadata: Dict[str, Any] = None


class SentenceBasedExtractor:
    """センテンスベースの地名抽出器"""
    
    def __init__(self):
        self.ginza_extractor = GinzaPlaceExtractor()
        self.simple_extractor = SimplePlaceExtractor()
        self.enhanced_extractor = EnhancedPlaceExtractor()
    
    def extract_places_from_sentence(self, sentence_text: str, work_id: int = None, author_id: int = None) -> List[ExtractedPlace]:
        """センテンスから地名を抽出"""
        places = []
        
        # 1. GiNZA抽出
        ginza_places = self.ginza_extractor.extract_places_from_text(
            work_id, sentence_text
        )
        for place in ginza_places:
            places.append(ExtractedPlace(
                work_id=work_id,
                place_name=place.place_name,
                sentence=sentence_text,
                before_text=place.before_text,
                after_text=place.after_text,
                confidence=place.confidence,
                extraction_method="ginza_nlp",
                author_id=author_id
            ))
        
        # 2. Simple抽出
        simple_places = self.simple_extractor.extract_places_from_text(
            work_id, sentence_text
        )
        for place in simple_places:
            places.append(ExtractedPlace(
                work_id=work_id,
                place_name=place.place_name,
                sentence=sentence_text,
                before_text=place.before_text,
                after_text=place.after_text,
                confidence=place.confidence,
                extraction_method="simple_regex",
                author_id=author_id
            ))
        
        # 3. Enhanced抽出
        enhanced_places = self.enhanced_extractor.extract_places_from_text(
            work_id, sentence_text
        )
        for place in enhanced_places:
            places.append(ExtractedPlace(
                work_id=work_id,
                place_name=place.place_name,
                sentence=sentence_text,
                before_text=place.before_text,
                after_text=place.after_text,
                confidence=place.confidence,
                extraction_method="enhanced",
                author_id=author_id
            ))
        
        # 重複除去
        return self._deduplicate_places(places)
    
    def _deduplicate_places(self, places: List[ExtractedPlace]) -> List[ExtractedPlace]:
        """重複地名の除去"""
        seen = set()
        unique_places = []
        
        for place in places:
            # 地名と文の組み合わせで重複チェック
            key = (place.place_name, place.sentence)
            if key not in seen:
                seen.add(key)
                unique_places.append(place)
        
        return unique_places

    def split_into_sentences(self, text: str) -> List[str]:
        """テキストを文単位に分割"""
        import re
        sentences = re.split(r'[。！？]', text)
        return [s.strip() for s in sentences if s.strip()] 