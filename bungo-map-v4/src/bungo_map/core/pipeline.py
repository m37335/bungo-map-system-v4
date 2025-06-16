#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪ゆかり地図システム v4.0
メインパイプライン統合クラス
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..aozora.aozora_client import AozoraClient
from ..aozora.aozora_cleaner import AozoraCleaner
from ..extractors.extraction_pipeline import ExtractionPipeline
from ..ai.geocoder.context_aware_geocoder import ContextAwareGeocoder
from ..database.manager import DatabaseManager

logger = logging.getLogger(__name__)

@dataclass
class PipelineResult:
    """パイプライン実行結果"""
    success: bool
    work_id: Optional[int] = None
    author_id: Optional[int] = None
    extracted_places: List[Dict] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None

class MainPipeline:
    """メインパイプライン統合クラス"""
    
    def __init__(self, db_path: str):
        """初期化"""
        self.db_path = db_path
        self.db = DatabaseManager(db_path)
        self.aozora_client = AozoraClient()
        self.aozora_cleaner = AozoraCleaner()
        self.extraction_pipeline = ExtractionPipeline()
        self.geocoder = ContextAwareGeocoder()
        
        logger.info("🔧 メインパイプライン初期化完了")
    
    def process_work(self, author_name: str, work_title: str) -> PipelineResult:
        """作品の完全処理"""
        start_time = datetime.now()
        result = PipelineResult(success=False)
        
        try:
            # 1. 青空文庫から作品取得
            work_content = self.aozora_client.get_work_content(author_name, work_title)
            if not work_content:
                result.error_message = "作品の取得に失敗しました"
                return result
            
            # 2. テキストクリーニング
            cleaned = self.aozora_cleaner.clean_and_normalize(work_content)
            
            # 3. データベースに作品登録
            author_id = self.db.get_or_create_author(author_name)
            work_id = self.db.create_work(author_id, work_title, cleaned.text)
            result.work_id = work_id
            result.author_id = author_id
            
            # 4. 地名抽出
            extracted_places = []
            for sentence in cleaned.text.split('。'):
                if not sentence.strip():
                    continue
                
                place_result = self.extraction_pipeline.process_sentence(
                    sentence, work_id, author_id
                )
                if place_result['places']:
                    extracted_places.extend(place_result['places'])
            
            # 5. ジオコーディング
            for place in extracted_places:
                if not place.get('latitude'):
                    geocode_result = self.geocoder.geocode_place(
                        place['place_name'],
                        place.get('context_before', ''),
                        place.get('context_after', '')
                    )
                    if geocode_result:
                        place.update({
                            'latitude': geocode_result.latitude,
                            'longitude': geocode_result.longitude,
                            'confidence': geocode_result.confidence
                        })
            
            # 6. 結果をデータベースに保存
            self.db.save_places(work_id, extracted_places)
            
            result.success = True
            result.extracted_places = extracted_places
            
        except Exception as e:
            logger.error(f"パイプライン処理エラー: {e}")
            result.error_message = str(e)
        
        finally:
            result.processing_time = (datetime.now() - start_time).total_seconds()
        
        return result
    
    def process_batch(self, works: List[Dict[str, str]]) -> List[PipelineResult]:
        """複数作品の一括処理"""
        results = []
        total = len(works)
        
        for i, work in enumerate(works, 1):
            logger.info(f"処理中: {i}/{total} - {work['author']} - {work['title']}")
            result = self.process_work(work['author'], work['title'])
            results.append(result)
            
            if not result.success:
                logger.warning(f"処理失敗: {work['author']} - {work['title']} - {result.error_message}")
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """処理統計情報の取得"""
        return {
            'authors': self.db.count_authors(),
            'works': self.db.count_works(),
            'places': self.db.count_places(),
            'geocoded_places': self.db.count_geocoded_places(),
            'processing_time': self.db.get_average_processing_time()
        } 