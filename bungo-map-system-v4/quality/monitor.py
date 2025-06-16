from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import json
from prometheus_client import Counter, Gauge, Histogram
import redis

logger = logging.getLogger(__name__)

class QualityMonitor:
    """品質モニタリング管理クラス"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        # Redis接続
        self.redis = redis.from_url(redis_url)
        
        # Prometheusメトリクス
        self.sentence_counter = Counter(
            'sentence_processed_total',
            '処理されたセンテンスの総数'
        )
        self.place_counter = Counter(
            'place_extracted_total',
            '抽出された地名の総数'
        )
        self.quality_score = Gauge(
            'quality_score',
            '品質スコア',
            ['type']  # sentence, place, sentence_place
        )
        self.processing_time = Histogram(
            'processing_time_seconds',
            '処理時間（秒）',
            ['operation']  # extraction, validation, geocoding
        )
        
        # キャッシュの有効期限（秒）
        self.cache_ttl = 3600  # 1時間

    def record_sentence_processing(
        self,
        sentence_id: int,
        quality_score: float,
        processing_time: float
    ):
        """センテンス処理の記録"""
        try:
            # Prometheusメトリクスの更新
            self.sentence_counter.inc()
            self.quality_score.labels(type='sentence').set(quality_score)
            self.processing_time.labels(operation='extraction').observe(processing_time)
            
            # Redisへの記録
            key = f"sentence:{sentence_id}"
            data = {
                "quality_score": quality_score,
                "processing_time": processing_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.redis.setex(key, self.cache_ttl, json.dumps(data))
            
        except Exception as e:
            logger.error(f"センテンス処理記録エラー: {str(e)}")

    def record_place_extraction(
        self,
        place_id: int,
        quality_score: float,
        processing_time: float
    ):
        """地名抽出の記録"""
        try:
            # Prometheusメトリクスの更新
            self.place_counter.inc()
            self.quality_score.labels(type='place').set(quality_score)
            self.processing_time.labels(operation='validation').observe(processing_time)
            
            # Redisへの記録
            key = f"place:{place_id}"
            data = {
                "quality_score": quality_score,
                "processing_time": processing_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.redis.setex(key, self.cache_ttl, json.dumps(data))
            
        except Exception as e:
            logger.error(f"地名抽出記録エラー: {str(e)}")

    def get_quality_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """品質メトリクスの取得"""
        try:
            if not start_time:
                start_time = datetime.utcnow() - timedelta(hours=24)
            if not end_time:
                end_time = datetime.utcnow()
                
            # Redisからデータを取得
            sentence_keys = self.redis.keys("sentence:*")
            place_keys = self.redis.keys("place:*")
            
            # センテンスの統計
            sentence_scores = []
            sentence_times = []
            for key in sentence_keys:
                data = json.loads(self.redis.get(key))
                if start_time <= datetime.fromisoformat(data["timestamp"]) <= end_time:
                    sentence_scores.append(data["quality_score"])
                    sentence_times.append(data["processing_time"])
                    
            # 地名の統計
            place_scores = []
            place_times = []
            for key in place_keys:
                data = json.loads(self.redis.get(key))
                if start_time <= datetime.fromisoformat(data["timestamp"]) <= end_time:
                    place_scores.append(data["quality_score"])
                    place_times.append(data["processing_time"])
                    
            return {
                "sentence_metrics": {
                    "count": len(sentence_scores),
                    "avg_quality_score": sum(sentence_scores) / len(sentence_scores) if sentence_scores else 0,
                    "avg_processing_time": sum(sentence_times) / len(sentence_times) if sentence_times else 0
                },
                "place_metrics": {
                    "count": len(place_scores),
                    "avg_quality_score": sum(place_scores) / len(place_scores) if place_scores else 0,
                    "avg_processing_time": sum(place_times) / len(place_times) if place_times else 0
                },
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"品質メトリクス取得エラー: {str(e)}")
            return {}

    def check_alerts(self) -> List[Dict[str, Any]]:
        """アラートのチェック"""
        alerts = []
        try:
            # 品質スコアのアラート
            sentence_score = self.quality_score.labels(type='sentence').get()
            place_score = self.quality_score.labels(type='place').get()
            
            if sentence_score < 0.7:
                alerts.append({
                    "type": "low_sentence_quality",
                    "message": "センテンスの品質スコアが低すぎます",
                    "value": sentence_score,
                    "threshold": 0.7
                })
                
            if place_score < 0.7:
                alerts.append({
                    "type": "low_place_quality",
                    "message": "地名の品質スコアが低すぎます",
                    "value": place_score,
                    "threshold": 0.7
                })
                
            # 処理時間のアラート
            sentence_time = self.processing_time.labels(operation='extraction').get()
            place_time = self.processing_time.labels(operation='validation').get()
            
            if sentence_time > 5.0:  # 5秒以上
                alerts.append({
                    "type": "high_sentence_processing_time",
                    "message": "センテンスの処理時間が長すぎます",
                    "value": sentence_time,
                    "threshold": 5.0
                })
                
            if place_time > 3.0:  # 3秒以上
                alerts.append({
                    "type": "high_place_processing_time",
                    "message": "地名の処理時間が長すぎます",
                    "value": place_time,
                    "threshold": 3.0
                })
                
        except Exception as e:
            logger.error(f"アラートチェックエラー: {str(e)}")
            
        return alerts 