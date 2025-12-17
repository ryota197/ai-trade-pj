"""ヘルスチェックAPI"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.infrastructure.database.connection import get_db
from src.presentation.schemas.common import ApiResponse
from src.presentation.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse[HealthResponse])
def health_check(db: Session = Depends(get_db)) -> ApiResponse[HealthResponse]:
    """
    ヘルスチェックエンドポイント

    - アプリケーションの稼働状態を確認
    - データベース接続を確認
    """
    # DB接続確認
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return ApiResponse(
        success=True,
        data=HealthResponse(
            status="ok",
            database=db_status,
        ),
    )
