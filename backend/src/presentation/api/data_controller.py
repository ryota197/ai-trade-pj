"""データ取得API"""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from src.infrastructure.gateways.financial_data_gateway import (
    QuoteData,
    HistoricalBar,
)
from src.infrastructure.gateways.yfinance_gateway import YFinanceGateway
from src.presentation.schemas.common import ApiResponse
from src.presentation.schemas.quote import (
    FinancialsResponse,
    HistoryItem,
    HistoryResponse,
    QuoteResponse,
)

router = APIRouter(prefix="/data", tags=["data"])

# Gateway インスタンス
gateway = YFinanceGateway()


def _quote_to_response(quote: QuoteData) -> QuoteResponse:
    """DTOをレスポンススキーマに変換"""
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
    history: list[HistoricalBar],
) -> HistoryResponse:
    """DTOをレスポンススキーマに変換"""
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
async def get_quote(symbol: str) -> ApiResponse[QuoteResponse]:
    """株価データを取得"""
    try:
        quote = await gateway.get_quote(symbol)
        if quote is None:
            raise HTTPException(status_code=404, detail=f"Invalid symbol: {symbol}")
        return ApiResponse(
            success=True,
            data=_quote_to_response(quote),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch quote: {e}")


@router.get(
    "/history/{symbol}",
    response_model=ApiResponse[HistoryResponse],
    summary="過去データ取得",
    description="指定したシンボルの過去の株価データを取得する",
)
async def get_history(
    symbol: str,
    period: str = Query(default="1mo", description="期間（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）"),
    interval: str = Query(default="1d", description="間隔（1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo）"),
) -> ApiResponse[HistoryResponse]:
    """過去の株価データを取得"""
    try:
        history = await gateway.get_price_history(symbol, period=period, interval=interval)
        if not history:
            raise HTTPException(status_code=404, detail=f"No history data for symbol: {symbol}")
        return ApiResponse(
            success=True,
            data=_history_to_response(symbol, period, interval, history),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {e}")


@router.get(
    "/financials/{symbol}",
    response_model=ApiResponse[FinancialsResponse],
    summary="財務指標取得",
    description="指定したシンボルの財務指標（EPS成長率、ROE等）を取得する",
)
async def get_financials(symbol: str) -> ApiResponse[FinancialsResponse]:
    """財務指標を取得"""
    try:
        metrics = await gateway.get_financial_metrics(symbol)

        if metrics is None:
            raise HTTPException(
                status_code=404,
                detail=f"Financial data not found: {symbol}",
            )

        response = FinancialsResponse(
            symbol=metrics.symbol,
            eps_ttm=metrics.eps_ttm,
            eps_growth_quarterly=metrics.eps_growth_quarterly,
            eps_growth_annual=metrics.eps_growth_annual,
            revenue_growth=metrics.revenue_growth,
            profit_margin=metrics.profit_margin,
            roe=metrics.roe,
            debt_to_equity=metrics.debt_to_equity,
            institutional_ownership=metrics.institutional_ownership,
            retrieved_at=datetime.now(),
        )

        return ApiResponse(success=True, data=response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch financials: {e}",
        )
