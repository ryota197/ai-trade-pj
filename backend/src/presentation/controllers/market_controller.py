"""マーケットAPI"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.adapters.database import get_db
from src.models import MarketSnapshot
from src.queries import MarketSnapshotQuery
from src.services._lib.types import Signal
from src.presentation.schemas.common import ApiResponse
from src.presentation.schemas.market import (
    MarketIndicatorsResponse,
    MarketStatusResponse,
)

router = APIRouter(prefix="/market", tags=["market"])


# ========================================
# ヘルパー関数（ドメインロジックのインライン化）
# ========================================


def _vix_signal(vix: float) -> Signal:
    """VIXシグナル判定"""
    if vix < 15:
        return Signal.BULLISH
    elif vix > 25:
        return Signal.BEARISH
    return Signal.NEUTRAL


def _rsi_signal(rsi: float) -> Signal:
    """RSIシグナル判定"""
    if rsi > 70:
        return Signal.BEARISH
    elif rsi < 30:
        return Signal.BULLISH
    return Signal.NEUTRAL


def _put_call_signal(put_call_ratio: float) -> Signal:
    """Put/Call Ratioシグナル判定"""
    if put_call_ratio > 1:
        return Signal.BULLISH
    elif put_call_ratio < 0.7:
        return Signal.BEARISH
    return Signal.NEUTRAL


def _snapshot_to_indicators(snapshot: MarketSnapshot) -> MarketIndicatorsResponse:
    """MarketSnapshotを指標レスポンスに変換"""
    vix = float(snapshot.vix)
    rsi = float(snapshot.sp500_rsi)
    put_call = float(snapshot.put_call_ratio)
    sp500_price = float(snapshot.sp500_price)
    sp500_ma200 = float(snapshot.sp500_ma200)

    return MarketIndicatorsResponse(
        vix=vix,
        vix_signal=_vix_signal(vix).value,
        sp500_price=sp500_price,
        sp500_rsi=rsi,
        sp500_rsi_signal=_rsi_signal(rsi).value,
        sp500_ma200=sp500_ma200,
        sp500_above_ma200=sp500_price > sp500_ma200,
        put_call_ratio=put_call,
        put_call_signal=_put_call_signal(put_call).value,
        retrieved_at=snapshot.recorded_at,
    )


def _get_recommendation(score: int) -> str:
    """スナップショットから推奨アクションを生成"""
    if score >= 2:
        return "市場環境は良好。個別株のエントリー検討可。"
    elif score <= -2:
        return "市場環境は悪化。新規エントリーは控えめに。"
    return "市場環境は中立。慎重な判断を。"


def _snapshot_to_status(snapshot: MarketSnapshot) -> MarketStatusResponse:
    """MarketSnapshotを状態レスポンスに変換"""
    return MarketStatusResponse(
        condition=snapshot.condition,
        condition_label=snapshot.condition.replace("_", " ").title(),
        confidence=min(abs(snapshot.score) / 5.0, 1.0),
        score=snapshot.score,
        recommendation=_get_recommendation(snapshot.score),
        indicators=_snapshot_to_indicators(snapshot),
        analyzed_at=snapshot.recorded_at,
    )


# ========================================
# エンドポイント
# ========================================


@router.get("/status", response_model=ApiResponse[MarketStatusResponse])
def get_market_status(
    db: Session = Depends(get_db),
) -> ApiResponse[MarketStatusResponse]:
    """マーケット状態を取得"""
    try:
        query = MarketSnapshotQuery(db)
        snapshot = query.find_latest()

        if snapshot is None:
            raise HTTPException(status_code=404, detail="Market data not available")

        return ApiResponse(success=True, data=_snapshot_to_status(snapshot))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/indicators", response_model=ApiResponse[MarketIndicatorsResponse])
def get_market_indicators(
    db: Session = Depends(get_db),
) -> ApiResponse[MarketIndicatorsResponse]:
    """マーケット指標を取得"""
    try:
        query = MarketSnapshotQuery(db)
        snapshot = query.find_latest()

        if snapshot is None:
            raise HTTPException(status_code=404, detail="Market indicators not available")

        return ApiResponse(success=True, data=_snapshot_to_indicators(snapshot))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
