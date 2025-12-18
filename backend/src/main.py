"""FastAPI エントリーポイント"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.presentation.api import data_controller, health_controller, market_controller

settings = get_settings()

# FastAPI アプリケーション
app = FastAPI(
    title="AI Trade App API",
    description="CAN-SLIM投資支援アプリケーションのAPI",
    version="0.1.0",
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json",
)

# CORS設定（開発用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(health_controller.router, prefix=settings.api_prefix)
app.include_router(data_controller.router, prefix=settings.api_prefix)
app.include_router(market_controller.router, prefix=settings.api_prefix)


@app.get("/")
def root():
    """ルートエンドポイント"""
    return {"message": "AI Trade App API", "docs": f"{settings.api_prefix}/docs"}
