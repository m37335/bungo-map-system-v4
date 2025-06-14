"""
Bungo Map System v4.0 Extraction Pipeline

センテンス中心のエンドツーエンド抽出パイプライン
"""

from typing import List, Dict, Any, Optional
from .sentence_extractor import SentenceBasedExtractor, ExtractedPlace
from .place_normalizer import PlaceNameNormalizer


class ExtractionPipeline:
    """v4.0抽出パイプライン"""
    
    def __init__(self):
        self.sentence_extractor = SentenceBasedExtractor()
        self.place_normalizer = PlaceNameNormalizer()
    
    def process_sentence(self, sentence_text: str, work_id: int = None, author_id: int = None) -> Dict[str, Any]:
        """センテンス処理"""
        # 1. 地名抽出
        places = self.sentence_extractor.extract_places_from_sentence(
            sentence_text, work_id, author_id
        )
        
        # 2. 地名正規化
        normalized_places = []
        for place in places:
            normalized = self._normalize_extracted_place(place)
            normalized_places.append(normalized)
        
        # 3. 結果統合
        result = {
            'sentence_text': sentence_text,
            'work_id': work_id,
            'author_id': author_id,
            'places': [place.__dict__ for place in normalized_places],
            'place_count': len(normalized_places),
            'processing_status': 'completed'
        }
        
        return result
    
    def _normalize_extracted_place(self, place: ExtractedPlace) -> ExtractedPlace:
        """抽出地名の正規化"""
        # 地名正規化
        normalized_name = self.place_normalizer.normalize(place.place_name)
        
        # タイプ判定
        place_type = self.place_normalizer.determine_place_type(place.place_name)
        
        # 別名生成
        aliases = self.place_normalizer.generate_aliases(place.place_name)
        
        # ExtractedPlaceを拡張
        place.place_name = normalized_name
        
        # 新しい属性を追加（辞書として）
        if not hasattr(place, 'metadata'):
            place.metadata = {}
        
        place.metadata.update({
            'place_type': place_type,
            'aliases': aliases,
            'original_name': place.place_name if normalized_name != place.place_name else None
        })
        
        return place 