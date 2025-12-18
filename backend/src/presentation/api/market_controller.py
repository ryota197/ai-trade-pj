"""マーケットAPI"""

from fastapi import APIRouter, Depends, HTTPException

from src.application.dto.market_dto import MarketIndicatorsOutput, MarketStatusOutput
from src.application.use_cases.market import (
    GetMarketIndicatorsUseCase,
    GetMarketStatusUseCase,
)
from src.presentation.dependencies import (
    get_market_indicators_use_case,
    get_market_status_use_case,
)
from src.presentation.schemas.common import ApiResponse
from src.presentation.schemas.market import (
    MarketIndicatorsResponse,
    MarketStatusResponse,
)

router = APIRouter(prefix="/market", tags=["market"])


def _indicators_to_response(dto: MarketIndicatorsOutput) -> MarketIndicatorsResponse:
    """MarketIndicatorsOutput DTO をレスポンススキーマに変換"""
    return MarketIndicatorsResponse(
        vix=dto.vix,
        vix_signal=dto.vix_signal,
        sp500_price=dto.sp500_price,
        sp500_rsi=dto.sp500_rsi,
        sp500_rsi_signal=dto.sp500_rsi_signal,
        sp500_ma200=dto.sp500_ma200,
        sp500_above_ma200=dto.sp500_above_ma200,
        put_call_ratio=dto.put_call_ratio,
        put_call_signal=dto.put_call_signal,
        retrieved_at=dto.retrieved_at,
    )


def _status_to_response(dto: MarketStatusOutput) -> MarketStatusResponse:
    """MarketStatusOutput DTO をレスポンススキーマに変換"""
    return MarketStatusResponse(
        condition=dto.condition.value,
        condition_label=dto.condition_label,
        confidence=dto.confidence,
        score=dto.score,
        recommendation=dto.recommendation,
        indicators=_indicators_to_response(dto.indicators),
        analyzed_at=dto.analyzed_at,
    )


@router.get("/status", response_model=ApiResponse[MarketStatusResponse])
def get_market_status(
    use_case: GetMarketStatusUseCase = Depends(get_market_status_use_case),
) -> ApiResponse[MarketStatusResponse]:
    """
    マーケット状態を取得

    市場データを取得し、Risk On/Off/Neutral を判定して返す。

    - **condition**: risk_on / risk_off / neutral
    - **confidence**: 判定の確信度 (0-1)
    - **score**: 総合スコア (-5 〜 +5)
    - **recommendation**: 推奨アクション
    - **indicators**: 各種市場指標
    """
    try:
        output = use_case.execute()
        return ApiResponse(
            success=True,
            data=_status_to_response(output),
        )
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"Market data fetch error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/indicators", response_model=ApiResponse[MarketIndicatorsResponse])
def get_market_indicators(
    use_case: GetMarketIndicatorsUseCase = Depends(get_market_indicators_use_case),
) -> ApiResponse[MarketIndicatorsResponse]:
    """
    マーケット指標を取得

    各種市場指標を取得して返す（状態判定は行わない）。

    - **vix**: VIX指数（恐怖指数）
    - **sp500_price**: S&P500 現在価格
    - **sp500_rsi**: S&P500 RSI（14日）
    - **sp500_ma200**: S&P500 200日移動平均
    - **put_call_ratio**: Put/Call Ratio
    """
    try:
        output = use_case.execute()
        return ApiResponse(
            success=True,
            data=_indicators_to_response(output),
        )
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"Market data fetch error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
