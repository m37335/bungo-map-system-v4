from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from .database.config import get_db
from .database.crud import DatabaseManager
from .extractors.place_extractor import PlaceExtractor, ExtractedPlace
from .core.models import (
    AuthorCreate,
    AuthorResponse,
    WorkCreate,
    WorkResponse,
    SentenceCreate,
    SentenceResponse,
    PlaceResponse,
    AuthorStats, WorkStats
)
from .core.cache import CacheManager, cache_result

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="文豪ゆかり地図API",
    description="文豪作品の地名情報を管理するAPI",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# キャッシュマネージャーのインスタンス化
cache_manager = CacheManager()

# 依存関係
def get_db_manager(db: Session = Depends(get_db)) -> DatabaseManager:
    return DatabaseManager(db)

def get_place_extractor() -> PlaceExtractor:
    return PlaceExtractor()

# 作者関連のエンドポイント
@app.post("/authors/", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(
    author: AuthorCreate,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """作者の作成"""
    try:
        result = db_manager.create_author(author.dict())
        # キャッシュのクリア
        cache_manager.clear_prefix("author")
        return result
    except Exception as e:
        logger.error(f"作者作成エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="作者の作成に失敗しました"
        )

@app.get("/authors/{author_id}", response_model=AuthorResponse)
@cache_result(prefix="author", ttl=3600)
async def get_author(
    author_id: int,
    db_manager: DatabaseManager = Depends(get_db_manager),
    cache_manager: CacheManager = Depends(lambda: cache_manager)
):
    """作者の取得"""
    try:
        result = db_manager.get_author(author_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="作者が見つかりません"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"作者取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="作者の取得に失敗しました"
        )

# 作品関連のエンドポイント
@app.post("/works/", response_model=WorkResponse, status_code=status.HTTP_201_CREATED)
async def create_work(
    work: WorkCreate,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """作品の作成"""
    try:
        result = db_manager.create_work(work.dict())
        # キャッシュのクリア
        cache_manager.clear_prefix("work")
        cache_manager.clear_prefix("author")
        return result
    except Exception as e:
        logger.error(f"作品作成エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="作品の作成に失敗しました"
        )

@app.get("/works/{work_id}", response_model=WorkResponse)
@cache_result(prefix="work", ttl=3600)
async def get_work(
    work_id: int,
    db_manager: DatabaseManager = Depends(get_db_manager),
    cache_manager: CacheManager = Depends(lambda: cache_manager)
):
    """作品の取得"""
    try:
        result = db_manager.get_work(work_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="作品が見つかりません"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"作品取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="作品の取得に失敗しました"
        )

# センテンス関連のエンドポイント
@app.post("/sentences/", response_model=SentenceResponse, status_code=status.HTTP_201_CREATED)
async def create_sentence(
    sentence: SentenceCreate,
    db_manager: DatabaseManager = Depends(get_db_manager),
    place_extractor: PlaceExtractor = Depends(get_place_extractor)
):
    """センテンスの作成と地名抽出"""
    try:
        # センテンスの作成
        result = db_manager.create_sentence(sentence.dict())
        
        # キャッシュのクリア
        cache_manager.clear_prefix("sentence")
        cache_manager.clear_prefix("work")
        
        return result
        
    except Exception as e:
        logger.error(f"センテンス作成エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="センテンスの作成に失敗しました"
        )

@app.get("/sentences/{sentence_id}", response_model=SentenceResponse)
@cache_result(prefix="sentence", ttl=3600)
async def get_sentence(
    sentence_id: int,
    db_manager: DatabaseManager = Depends(get_db_manager),
    cache_manager: CacheManager = Depends(lambda: cache_manager)
):
    """センテンスの取得"""
    try:
        result = db_manager.get_sentence(sentence_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="センテンスが見つかりません"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"センテンス取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="センテンスの取得に失敗しました"
        )

# 地名関連のエンドポイント
@app.get("/places/", response_model=List[PlaceResponse])
def get_places(db: Session = Depends(get_db)):
    db_manager = DatabaseManager(db)
    places = db_manager.get_all_places()
    return [PlaceResponse(**place.__dict__) for place in places]

@app.get("/places/{place_id}", response_model=PlaceResponse)
@cache_result(prefix="place", ttl=3600)
async def get_place(
    place_id: int,
    db_manager: DatabaseManager = Depends(get_db_manager),
    cache_manager: CacheManager = Depends(lambda: cache_manager)
):
    """地名の取得"""
    try:
        result = db_manager.get_place(place_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="地名が見つかりません"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"地名取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="地名の取得に失敗しました"
        )

# 統計情報のエンドポイント
@app.get("/authors/{author_id}/stats", response_model=AuthorStats)
@cache_result(prefix="stats", ttl=1800)
async def get_author_stats(
    author_id: int,
    db_manager: DatabaseManager = Depends(get_db_manager),
    cache_manager: CacheManager = Depends(lambda: cache_manager)
):
    """作者の統計情報取得"""
    try:
        result = db_manager.get_author_stats(author_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="作者の統計情報が見つかりません"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"著者統計取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="著者の統計情報の取得に失敗しました"
        )

@app.get("/works/{work_id}/stats", response_model=WorkStats)
@cache_result(prefix="stats", ttl=1800)
async def get_work_stats(
    work_id: int,
    db_manager: DatabaseManager = Depends(get_db_manager),
    cache_manager: CacheManager = Depends(lambda: cache_manager)
):
    """作品の統計情報取得"""
    try:
        result = db_manager.get_work_stats(work_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="作品の統計情報が見つかりません"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"作品統計取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="作品の統計情報の取得に失敗しました"
        )
