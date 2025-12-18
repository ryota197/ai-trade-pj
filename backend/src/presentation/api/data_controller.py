"""データ取得API"""

from fastapi import APIRouter, HTTPException, Query

from src.domain.entities.quote import HistoricalPrice, Quote
from src.infrastructure.gateways.yfinance_gateway import YFinanceGateway
from src.presentation.schemas.common import ApiResponse
from src.presentation.schemas.quote import (
    HistoryItem,
    HistoryResponse,
    QuoteResponse,
)

router = APIRouter(prefix="/data", tags=["data"])

# Gateway インスタンス
gateway = YFinanceGateway()


def _quote_to_response(quote: Quote) -> QuoteResponse:
    """ドメインエンティティをレスポンススキーマに変換"""
    return QuoteResponse(
        symbol=quote.symbol,
        price=quote.price,
        change=quote.change,
        change_percent=quote.change_percent,
        volume=quote.volume,
        market_cap=quote.market_cap,
        pe_ratio=quote.pe_ratio,
        week_52_high=quote.week_52_high,
        week_52_low=quote.week_52_low,
        timestamp=quote.timestamp,
    )


def _history_to_response(
    symbol: str,
    period: str,
    interval: str,
    history: list[HistoricalPrice],
) -> HistoryResponse:
    """ドメインエンティティをレスポンススキーマに変換"""
    return HistoryResponse(
        symbol=symbol.upper(),
        period=period,
        interval=interval,
        data=[
            HistoryItem(
                date=h.date,
                open=h.open,
                high=h.high,
                low=h.low,
                close=h.close,
                volume=h.volume,
            )
            for h in history
        ],
    )


@router.get(
    "/quote/{symbol}",
    response_model=ApiResponse[QuoteResponse],
    summary="株価取得",
    description="指定したシンボルの現在の株価データを取得する",
)
def get_quote(symbol: str) -> ApiResponse[QuoteResponse]:
    """株価データを取得"""
    try:
        quote = gateway.get_quote(symbol)
        return ApiResponse(
            success=True,
            data=_quote_to_response(quote),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch quote: {e}")


@router.get(
    "/history/{symbol}",
    response_model=ApiResponse[HistoryResponse],
    summary="過去データ取得",
    description="指定したシンボルの過去の株価データを取得する",
)
def get_history(
    symbol: str,
    period: str = Query(default="1mo", description="期間（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）"),
    interval: str = Query(default="1d", description="間隔（1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo）"),
) -> ApiResponse[HistoryResponse]:
    """過去の株価データを取得"""
    try:
        history = gateway.get_history(symbol, period=period, interval=interval)
        return ApiResponse(
            success=True,
            data=_history_to_response(symbol, period, interval, history),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {e}")
