"""マーケットAPI"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.domain.models.market_snapshot import MarketSnapshot
from src.infrastructure.database.connection import get_db
from src.infrastructure.repositories.postgres_market_snapshot_repository import (
    PostgresMarketSnapshotRepository,
)
from src.presentation.schemas.common import ApiResponse
from src.presentation.schemas.market import (
    MarketIndicatorsResponse,
    MarketStatusResponse,
)

router = APIRouter(prefix="/market", tags=["market"])


def _snapshot_to_indicators(snapshot: MarketSnapshot) -> MarketIndicatorsResponse:
    """MarketSnapshotを指標レスポンスに変換"""
    return MarketIndicatorsResponse(
        vix=float(snapshot.vix),
        vix_signal=snapshot.vix_signal().value,
        sp500_price=float(snapshot.sp500_price),
        sp500_rsi=float(snapshot.sp500_rsi),
        sp500_rsi_signal=snapshot.rsi_signal().value,
        sp500_ma200=float(snapshot.sp500_ma200),
        sp500_above_ma200=snapshot.is_above_ma200(),
        put_call_ratio=float(snapshot.put_call_ratio),
        put_call_signal=snapshot.put_call_signal().value,
        retrieved_at=snapshot.recorded_at,
    )


def _snapshot_to_status(snapshot: MarketSnapshot) -> MarketStatusResponse:
    """MarketSnapshotを状態レスポンスに変換"""
    return MarketStatusResponse(
        condition=snapshot.condition.value,
        condition_label=snapshot.condition.value.replace("_", " ").title(),
        confidence=min(abs(snapshot.score) / 5.0, 1.0),
        score=snapshot.score,
        recommendation=_get_recommendation(snapshot),
        indicators=_snapshot_to_indicators(snapshot),
        analyzed_at=snapshot.recorded_at,
    )


def _get_recommendation(snapshot: MarketSnapshot) -> str:
    """スナップショットから推奨アクションを生成"""
    if snapshot.score >= 2:
        return "市場環境は良好。個別株のエントリー検討可。"
    elif snapshot.score <= -2:
        return "市場環境は悪化。新規エントリーは控えめに。"
    return "市場環境は中立。慎重な判断を。"


@router.get("/status", response_model=ApiResponse[MarketStatusResponse])
def get_market_status(
    db: Session = Depends(get_db),
) -> ApiResponse[MarketStatusResponse]:
    """
    マーケット状態を取得

    保存済みのマーケットスナップショットから状態を取得する。
    """
    try:
        repo = PostgresMarketSnapshotRepository(db)
        snapshot = repo.find_latest()

        if snapshot is None:
            raise HTTPException(
                status_code=404,
                detail="Market data not available",
            )

        return ApiResponse(success=True, data=_snapshot_to_status(snapshot))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/indicators", response_model=ApiResponse[MarketIndicatorsResponse])
def get_market_indicators(
    db: Session = Depends(get_db),
) -> ApiResponse[MarketIndicatorsResponse]:
    """
    マーケット指標を取得

    保存済みのマーケットスナップショットから指標を取得する。
    """
    try:
        repo = PostgresMarketSnapshotRepository(db)
        snapshot = repo.find_latest()

        if snapshot is None:
            raise HTTPException(
                status_code=404,
                detail="Market indicators not available",
            )

        return ApiResponse(success=True, data=_snapshot_to_indicators(snapshot))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
