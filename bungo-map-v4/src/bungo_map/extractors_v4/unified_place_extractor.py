#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統合地名抽出システム v4
複数の抽出エンジンを統合し、高精度な地名抽出を実現
"""

import logging
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from datetime import datetime

from .enhanced_place_extractor import EnhancedPlaceExtractor
from .advanced_place_extractor import AdvancedPlaceExtractor
from .improved_place_extractor import ImprovedPlaceExtractor
from .ginza_place_extractor import GinzaPlaceExtractor
from .place_normalizer import PlaceNormalizer, NormalizedPlace

logger = logging.getLogger(__name__)

@dataclass
class UnifiedPlace:
    """統合地名データ"""
    work_id: int
    place_name: str
    canonical_name: str
    place_type: str
    prefecture: Optional[str]
    confidence: float
    extraction_method: str
    context_before: str
    context_after: str
    created_at: str
    updated_at: str

class UnifiedPlaceExtractor:
    """統合地名抽出システム v4"""
    
    def __init__(self):
        """初期化"""
        # 各抽出エンジンの初期化
        self.enhanced_extractor = EnhancedPlaceExtractor()
        self.advanced_extractor = AdvancedPlaceExtractor()
        self.improved_extractor = ImprovedPlaceExtractor()
        self.ginza_extractor = GinzaPlaceExtractor()
        
        # 地名正規化システムの初期化
        self.normalizer = PlaceNormalizer()
        
        logger.info("🌟 統合地名抽出システムv4初期化完了")
    
    def extract_places(self, work_id: int, text: str, context_before: str = '', context_after: str = ''):
        """
        テキストから地名を抽出し、正規化・統合して返す
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # 各エンジンで抽出
        enhanced_places = self.enhanced_extractor.extract_places(text)
        advanced_places = self.advanced_extractor.extract_places(text)
        improved_places = self.improved_extractor.extract_places(text)
        ginza_places = self.ginza_extractor.extract_places(text)
        
        # 抽出結果の統合
        all_places = []
        
        # Enhanced抽出結果の処理
        for place in enhanced_places:
            normalized = self.normalizer.normalize_place(place.place_name)
            all_places.append(UnifiedPlace(
                work_id=work_id,
                place_name=place.place_name,
                canonical_name=normalized.canonical_name,
                place_type=normalized.place_type,
                prefecture=normalized.prefecture,
                confidence=place.confidence * normalized.confidence,
                extraction_method='enhanced',
                context_before=context_before,
                context_after=context_after,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ))
        
        # Advanced抽出結果の処理
        for place in advanced_places:
            normalized = self.normalizer.normalize_place(place.place_name)
            all_places.append(UnifiedPlace(
                work_id=work_id,
                place_name=place.place_name,
                canonical_name=normalized.canonical_name,
                place_type=normalized.place_type,
                prefecture=normalized.prefecture,
                confidence=place.confidence * normalized.confidence,
                extraction_method='advanced',
                context_before=context_before,
                context_after=context_after,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ))
        
        # Improved抽出結果の処理
        for place in improved_places:
            normalized = self.normalizer.normalize_place(place.place_name)
            all_places.append(UnifiedPlace(
                work_id=work_id,
                place_name=place.place_name,
                canonical_name=normalized.canonical_name,
                place_type=normalized.place_type,
                prefecture=normalized.prefecture,
                confidence=place.confidence * normalized.confidence,
                extraction_method='improved',
                context_before=context_before,
                context_after=context_after,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ))
        
        # GiNZA抽出結果の処理
        for place in ginza_places:
            normalized = self.normalizer.normalize_place(place.place_name)
            all_places.append(UnifiedPlace(
                work_id=work_id,
                place_name=place.place_name,
                canonical_name=normalized.canonical_name,
                place_type=normalized.place_type,
                prefecture=normalized.prefecture,
                confidence=place.confidence * normalized.confidence,
                extraction_method='ginza',
                context_before=context_before,
                context_after=context_after,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ))
        
        # 重複の除去と信頼度による統合
        unified_places = self._unify_places(all_places)
        
        return unified_places
    
    def _unify_places(self, places: List[UnifiedPlace]) -> List[UnifiedPlace]:
        """抽出結果の統合"""
        # 正規名でグループ化
        place_groups: Dict[str, List[UnifiedPlace]] = {}
        for place in places:
            if place.canonical_name not in place_groups:
                place_groups[place.canonical_name] = []
            place_groups[place.canonical_name].append(place)
        
        # 各グループから最適な結果を選択
        unified_places = []
        for canonical_name, group in place_groups.items():
            # 信頼度が最も高い結果を選択
            best_place = max(group, key=lambda p: p.confidence)
            
            # 重複を除去
            if not any(p.canonical_name == best_place.canonical_name for p in unified_places):
                unified_places.append(best_place)
        
        return unified_places
    
    def test_extraction(self, test_texts: List[Dict[str, str]]) -> Dict:
        """抽出機能のテスト"""
        logger.info("🧪 統合地名抽出システムテスト開始")
        
        results = []
        for test in test_texts:
            work_id = test.get('work_id', 0)
            text = test.get('text', '')
            context_before = test.get('context_before', '')
            context_after = test.get('context_after', '')
            
            places = self.extract_places(work_id, text, context_before=context_before, context_after=context_after)
            
            results.append({
                'text': text,
                'places': [
                    {
                        'name': p.place_name,
                        'canonical': p.canonical_name,
                        'type': p.place_type,
                        'prefecture': p.prefecture,
                        'confidence': p.confidence,
                        'method': p.extraction_method
                    }
                    for p in places
                ]
            })
        
        return {
            'total_texts': len(results),
            'total_places': sum(len(r['places']) for r in results),
            'results': results,
            'success': len(results) > 0
        }

if __name__ == "__main__":
    # 簡単なテスト
    extractor = UnifiedPlaceExtractor()
    
    test_texts = [
        {
            'work_id': 1,
            'text': '東京の銀座で買い物をした後、新宿へ移動した。',
            'context_before': '主人公は',
            'context_after': 'という一日を過ごした。'
        },
        {
            'work_id': 2,
            'text': '富士山の頂上から見る朝日は格別だった。',
            'context_before': '登山の翌日、',
            'context_after': 'という感動的な体験をした。'
        }
    ]
    
    result = extractor.test_extraction(test_texts)
    
    print("✅ 統合地名抽出システムv4テスト完了")
    print(f"📊 テストテキスト数: {result['total_texts']}")
    print(f"🗺️ 抽出地名数: {result['total_places']}")
    
    for i, test_result in enumerate(result['results'], 1):
        print(f"\n📝 テスト{i}:")
        print(f"  テキスト: {test_result['text']}")
        for place in test_result['places']:
            print(f"  • {place['name']} → {place['canonical']} (タイプ: {place['type']}, 信頼度: {place['confidence']:.2f})")
            if place['prefecture']:
                print(f"    都道府県: {place['prefecture']}") 