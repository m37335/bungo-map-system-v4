from typing import Any, Optional, Dict, List
import json
import redis
from datetime import datetime, timedelta
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class CacheManager:
    """キャッシュ管理クラス"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 3600  # デフォルトの有効期限（秒）
    ):
        self.redis = redis.from_url(redis_url)
        self.default_ttl = default_ttl
        
        # キャッシュキーのプレフィックス
        self.key_prefixes = {
            "author": "author:",
            "work": "work:",
            "sentence": "sentence:",
            "place": "place:",
            "stats": "stats:"
        }
    
    def _get_key(self, prefix: str, identifier: Any) -> str:
        """キャッシュキーの生成"""
        return f"{self.key_prefixes[prefix]}{identifier}"
    
    def get(self, prefix: str, identifier: Any) -> Optional[Dict]:
        """キャッシュからのデータ取得"""
        try:
            key = self._get_key(prefix, identifier)
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"キャッシュ取得エラー: {str(e)}")
            return None
    
    def set(
        self,
        prefix: str,
        identifier: Any,
        data: Dict,
        ttl: Optional[int] = None
    ) -> bool:
        """データのキャッシュ保存"""
        try:
            key = self._get_key(prefix, identifier)
            ttl = ttl or self.default_ttl
            return self.redis.setex(
                key,
                ttl,
                json.dumps(data)
            )
        except Exception as e:
            logger.error(f"キャッシュ保存エラー: {str(e)}")
            return False
    
    def delete(self, prefix: str, identifier: Any) -> bool:
        """キャッシュの削除"""
        try:
            key = self._get_key(prefix, identifier)
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"キャッシュ削除エラー: {str(e)}")
            return False
    
    def clear_prefix(self, prefix: str) -> bool:
        """特定のプレフィックスを持つキャッシュの一括削除"""
        try:
            pattern = f"{self.key_prefixes[prefix]}*"
            keys = self.redis.keys(pattern)
            if keys:
                return bool(self.redis.delete(*keys))
            return True
        except Exception as e:
            logger.error(f"キャッシュ一括削除エラー: {str(e)}")
            return False
    
    def get_many(self, prefix: str, identifiers: List[Any]) -> Dict[Any, Optional[Dict]]:
        """複数のキャッシュデータの取得"""
        try:
            pipeline = self.redis.pipeline()
            keys = [self._get_key(prefix, id_) for id_ in identifiers]
            
            # パイプラインで一括取得
            for key in keys:
                pipeline.get(key)
            results = pipeline.execute()
            
            # 結果の整形
            return {
                id_: json.loads(data) if data else None
                for id_, data in zip(identifiers, results)
            }
        except Exception as e:
            logger.error(f"複数キャッシュ取得エラー: {str(e)}")
            return {id_: None for id_ in identifiers}
    
    def set_many(
        self,
        prefix: str,
        data_dict: Dict[Any, Dict],
        ttl: Optional[int] = None
    ) -> bool:
        """複数のデータのキャッシュ保存"""
        try:
            pipeline = self.redis.pipeline()
            ttl = ttl or self.default_ttl
            
            for identifier, data in data_dict.items():
                key = self._get_key(prefix, identifier)
                pipeline.setex(key, ttl, json.dumps(data))
            
            results = pipeline.execute()
            return all(results)
        except Exception as e:
            logger.error(f"複数キャッシュ保存エラー: {str(e)}")
            return False

def cache_result(
    prefix: str,
    ttl: Optional[int] = None,
    key_func: Optional[callable] = None
):
    """キャッシュデコレータ"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # キャッシュマネージャーの取得
            cache_manager = kwargs.get('cache_manager')
            if not cache_manager:
                return await func(*args, **kwargs)
            
            # キャッシュキーの生成
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = str(args[0]) if args else str(kwargs)
            
            # キャッシュからの取得を試みる
            cached_data = cache_manager.get(prefix, cache_key)
            if cached_data is not None:
                return cached_data
            
            # キャッシュになければ関数を実行
            result = await func(*args, **kwargs)
            
            # 結果をキャッシュに保存
            if result is not None:
                cache_manager.set(prefix, cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator 