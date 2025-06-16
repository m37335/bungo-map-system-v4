#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗺️ 強化版地名抽出器
改善された青空文庫処理 + AI文脈判断 + 適切な文脈取得

Features:
- 青空文庫コンテンツの適切な処理
- 自然な文分割と文脈取得
- 地名周辺の正確な前後文脈
- SimplePlaceExtractorとの統合
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from ..processors.aozora_content_processor import AozoraContentProcessor
from .simple_place_extractor import SimplePlaceExtractor

logger = logging.getLogger(__name__)

@dataclass
class EnhancedPlace:
    """強化版地名データ"""
    work_id: int
    place_name: str
    sentence: str           # クリーンな文
    before_text: str        # 前文脈
    after_text: str         # 後文脈
    sentence_index: int     # 文番号
    char_position: int      # 文字位置
    confidence: float       # 信頼度
    extraction_method: str  # 抽出手法
    aozora_url: str = ""

class EnhancedPlaceExtractor:
    """強化版地名抽出器"""
    
    def __init__(self):
        """初期化"""
        self.content_processor = AozoraContentProcessor()
        self.simple_extractor = SimplePlaceExtractor()
        
        print("🗺️ 強化版地名抽出器初期化完了")
    
    def extract_places_from_work(self, work_id: int, raw_content: str, aozora_url: str = "") -> List[EnhancedPlace]:
        """作品からの地名抽出（完全版）"""
        
        if not raw_content or len(raw_content) < 100:
            logger.warning(f"⚠️ 作品{work_id}: コンテンツが短すぎます")
            return []
        
        # 1. 青空文庫コンテンツ処理
        result = self.content_processor.process_work_content(work_id, raw_content)
        
        if not result['success']:
            logger.warning(f"⚠️ 作品{work_id}: コンテンツ処理失敗 - {result['error']}")
            return []
        
        sentences = result['sentences']
        main_content = result['main_content']
        
        # 2. 各文から地名抽出
        all_places = []
        
        for sentence_index, sentence in enumerate(sentences):
            # 文脈取得
            context = self.content_processor.get_sentence_context(
                sentences, sentence_index, context_length=1
            )
            
            # 基本地名抽出（この文のみ）
            sentence_places = self.simple_extractor.extract_places_from_text(
                work_id, sentence, aozora_url
            )
            
            # EnhancedPlaceに変換
            for place in sentence_places:
                enhanced_place = EnhancedPlace(
                    work_id=work_id,
                    place_name=place.place_name,
                    sentence=context.sentence,
                    before_text=context.before_text,
                    after_text=context.after_text,
                    sentence_index=context.sentence_index,
                    char_position=context.char_position,
                    confidence=place.confidence,
                    extraction_method=place.extraction_method,
                    aozora_url=aozora_url
                )
                
                all_places.append(enhanced_place)
        
        logger.info(f"✅ 作品{work_id}: {len(all_places)}件の地名抽出完了")
        return all_places
    
    def convert_to_simple_places(self, enhanced_places: List[EnhancedPlace]) -> List:
        """SimplePlaceと互換性のあるフォーマットに変換"""
        from bungo_map.extractors.simple_place_extractor import Place
        
        simple_places = []
        for enhanced in enhanced_places:
            simple_place = Place(
                work_id=enhanced.work_id,
                place_name=enhanced.place_name,
                before_text=enhanced.before_text,
                sentence=enhanced.sentence,
                after_text=enhanced.after_text,
                aozora_url=enhanced.aozora_url,
                confidence=enhanced.confidence,
                extraction_method=enhanced.extraction_method
            )
            simple_places.append(simple_place)
        
        return simple_places

# テスト用関数
def test_enhanced_extractor():
    """強化版抽出器のテスト"""
    import sqlite3
    
    extractor = EnhancedPlaceExtractor()
    
    # データベースから長いコンテンツの作品をテスト
    with sqlite3.connect('data/bungo_production.db') as conn:
        cursor = conn.execute("""
            SELECT work_id, title, content 
            FROM works 
            WHERE length(content) > 30000 
            LIMIT 2
        """)
        
        for work_id, title, content in cursor.fetchall():
            print(f"\n{'='*50}")
            print(f"📚 作品: {title}")
            print(f"📊 元データ: {len(content):,}文字")
            
            enhanced_places = extractor.extract_places_from_work(work_id, content)
            
            print(f"✅ 抽出結果: {len(enhanced_places)}件")
            
            # 地名サンプル表示
            for i, place in enumerate(enhanced_places[:5]):
                print(f"\n🗺️ 地名{i+1}: {place.place_name}")
                print(f"  📝 文: {place.sentence[:80]}...")
                print(f"  ⬅️ 前: {place.before_text[:30]}...")
                print(f"  ➡️ 後: {place.after_text[:30]}...")
                print(f"  📊 位置: 文{place.sentence_index}, 文字{place.char_position}")
            
            # 簡易統計
            methods = {}
            for place in enhanced_places:
                method = place.extraction_method
                methods[method] = methods.get(method, 0) + 1
            
            print(f"\n📋 抽出手法別統計:")
            for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
                print(f"  {method}: {count}件")

if __name__ == "__main__":
    test_enhanced_extractor() 