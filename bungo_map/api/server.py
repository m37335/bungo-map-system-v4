#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪ゆかり地図システム v2.0 - FastAPI サーバー
"""

from fastapi import FastAPI
import click
import uvicorn
from bungo_map.core.database import init_db

app = FastAPI(
    title="文豪ゆかり地図システム API",
    description="作家・作品・舞台地名の3階層データ管理システム",
    version="2.0.0"
)


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "🌟 文豪ゆかり地図システム v2.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/status")
async def status():
    """システム状況"""
    try:
        db = init_db()
        stats = db.get_stats()
        
        return {
            "status": "ok",
            "database": {
                "authors": stats["authors"],
                "works": stats["works"],
                "places": stats["places"]
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@click.command()
@click.option('--host', default='127.0.0.1', help='ホスト')
@click.option('--port', default=8000, help='ポート番号')
@click.option('--reload', is_flag=True, help='自動リロード')
def main(host: str, port: int, reload: bool):
    """🌐 API サーバー起動"""
    click.echo(f"🌐 API サーバー起動中: http://{host}:{port}")
    click.echo(f"📖 API ドキュメント: http://{host}:{port}/docs")
    
    uvicorn.run(
        "bungo_map.api.server:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    main() 