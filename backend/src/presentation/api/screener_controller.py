"""スクリーナーAPI"""

from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.domain.constants import CANSLIMDefaults
from src.domain.models.canslim_stock import CANSLIMStock
from src.domain.models.screening_criteria import ScreeningCriteria
from src.infrastructure.database.connection import get_db
from src.infrastructure.repositories.postgres_canslim_stock_repository import (
    PostgresCANSLIMStockRepository,
)
from src.presentation.schemas.common import ApiResponse
from src.presentation.schemas.screener import (
    CANSLIMCriteriaSchema,
    CANSLIMScoreSchema,
    ScreenerFilterSchema,
    ScreenerResponse,
    StockDetailSchema,
    StockSummarySchema,
)

# 定数エイリアス
_D = CANSLIMDefaults

router = APIRouter(prefix="/screener", tags=["screener"])


# ========================================
# ヘルパー関数
# ========================================


def _score_to_grade(score: int) -> str:
    """スコアをグレードに変換"""
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    elif score >= 20:
        return "D"
    return "F"


def _count_passing(stock: CANSLIMStock) -> int:
    """合格項目数をカウント"""
    passing = 0
    for score in [
        stock.score_c,
        stock.score_a,
        stock.score_n,
        stock.score_s,
        stock.score_l,
        stock.score_i,
    ]:
        if score is not None and score >= 10:
            passing += 1
    return passing


def _create_criteria_schema(name: str, score: int | None) -> CANSLIMCriteriaSchema:
    """スコアからCriteriaSchemaを作成"""
    score_val = score or 0
    return CANSLIMCriteriaSchema(
        name=name,
        score=score_val,
        grade=_score_to_grade(score_val),
        value=None,
        threshold=0.0,
        description="",
    )


def _stock_to_summary(stock: CANSLIMStock) -> StockSummarySchema:
    """CANSLIMStockをサマリースキーマに変換"""
    return StockSummarySchema(
        symbol=stock.symbol,
        name=stock.name or stock.symbol,
        price=float(stock.price) if stock.price else 0.0,
        change_percent=float(stock.change_percent) if stock.change_percent else 0.0,
        rs_rating=stock.rs_rating or 0,
        canslim_score=stock.canslim_score or 0,
        volume_ratio=float(stock.volume_ratio()) if stock.volume_ratio() else 0.0,
        distance_from_52w_high=(
            float(stock.distance_from_52week_high())
            if stock.distance_from_52week_high()
            else 0.0
        ),
    )


def _stock_to_detail(stock: CANSLIMStock) -> StockDetailSchema:
    """CANSLIMStockを詳細スキーマに変換"""
    canslim_schema = None
    if stock.canslim_score is not None:
        canslim_schema = CANSLIMScoreSchema(
            total_score=stock.canslim_score,
            overall_grade=_score_to_grade(stock.canslim_score),
            passing_count=_count_passing(stock),
            c_score=_create_criteria_schema(
                "C - Current Quarterly Earnings", stock.score_c
            ),
            a_score=_create_criteria_schema("A - Annual Earnings", stock.score_a),
            n_score=_create_criteria_schema("N - New High", stock.score_n),
            s_score=_create_criteria_schema("S - Supply and Demand", stock.score_s),
            l_score=_create_criteria_schema("L - Leader", stock.score_l),
            i_score=_create_criteria_schema(
                "I - Institutional Sponsorship", stock.score_i
            ),
        )

    price = float(stock.price) if stock.price else 0.0
    change_percent = float(stock.change_percent) if stock.change_percent else 0.0

    return StockDetailSchema(
        symbol=stock.symbol,
        name=stock.name or stock.symbol,
        price=price,
        change=price * change_percent / 100,
        change_percent=change_percent,
        volume=stock.volume or 0,
        avg_volume=stock.avg_volume_50d or 0,
        market_cap=float(stock.market_cap) if stock.market_cap else None,
        pe_ratio=None,
        week_52_high=float(stock.week_52_high) if stock.week_52_high else 0.0,
        week_52_low=float(stock.week_52_low) if stock.week_52_low else 0.0,
        eps_growth_quarterly=(
            float(stock.eps_growth_quarterly) if stock.eps_growth_quarterly else None
        ),
        eps_growth_annual=(
            float(stock.eps_growth_annual) if stock.eps_growth_annual else None
        ),
        rs_rating=stock.rs_rating or 0,
        institutional_ownership=(
            float(stock.institutional_ownership)
            if stock.institutional_ownership
            else None
        ),
        canslim_score=canslim_schema,
        updated_at=stock.updated_at or datetime.now(),
    )


# ========================================
# エンドポイント
# ========================================


@router.get(
    "/canslim",
    response_model=ApiResponse[ScreenerResponse],
    summary="CAN-SLIMスクリーニング",
    description="CAN-SLIM条件を満たす銘柄をスクリーニングする",
)
def screen_canslim_stocks(
    min_rs_rating: int = Query(
        _D.MIN_RS_RATING, ge=1, le=99, description="最小RS Rating"
    ),
    min_eps_growth_quarterly: float = Query(
        _D.MIN_EPS_GROWTH_QUARTERLY, description="最小四半期EPS成長率（%）"
    ),
    min_eps_growth_annual: float = Query(
        _D.MIN_EPS_GROWTH_ANNUAL, description="最小年間EPS成長率（%）"
    ),
    max_distance_from_52w_high: float = Query(
        _D.MAX_DISTANCE_FROM_52W_HIGH, description="最大52週高値乖離率（%）"
    ),
    min_volume_ratio: float = Query(
        _D.MIN_VOLUME_RATIO, description="最小出来高倍率"
    ),
    min_canslim_score: int = Query(
        _D.MIN_CANSLIM_SCORE, ge=0, le=100, description="最小CAN-SLIMスコア"
    ),
    limit: int = Query(
        _D.DEFAULT_LIMIT, ge=1, le=_D.MAX_LIMIT, description="取得件数"
    ),
    offset: int = Query(_D.DEFAULT_OFFSET, ge=0, description="オフセット"),
    db: Session = Depends(get_db),
) -> ApiResponse[ScreenerResponse]:
    """CAN-SLIM条件でスクリーニングを実行"""
    try:
        repo = PostgresCANSLIMStockRepository(db)

        criteria = ScreeningCriteria(
            min_rs_rating=min_rs_rating,
            min_canslim_score=min_canslim_score,
            min_eps_growth_quarterly=Decimal(str(min_eps_growth_quarterly)),
            min_eps_growth_annual=Decimal(str(min_eps_growth_annual)),
            max_distance_from_high=Decimal(str(max_distance_from_52w_high)),
            min_volume_ratio=Decimal(str(min_volume_ratio)),
        )

        stocks = repo.find_by_criteria(
            target_date=date.today(),
            criteria=criteria,
            limit=limit,
            offset=offset,
        )

        stocks_schema = [_stock_to_summary(stock) for stock in stocks]

        filter_schema = ScreenerFilterSchema(
            min_rs_rating=min_rs_rating,
            min_eps_growth_quarterly=min_eps_growth_quarterly,
            min_eps_growth_annual=min_eps_growth_annual,
            max_distance_from_52w_high=max_distance_from_52w_high,
            min_volume_ratio=min_volume_ratio,
            min_canslim_score=min_canslim_score,
        )

        response = ScreenerResponse(
            total_count=len(stocks_schema),
            stocks=stocks_schema,
            filter_applied=filter_schema,
            screened_at=datetime.now(),
        )

        return ApiResponse(success=True, data=response)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Screener failed: {e}",
        )


@router.get(
    "/stock/{symbol}",
    response_model=ApiResponse[StockDetailSchema],
    summary="銘柄詳細取得",
    description="個別銘柄の詳細情報（CAN-SLIMスコア含む）を取得する",
)
def get_stock_detail(
    symbol: str,
    db: Session = Depends(get_db),
) -> ApiResponse[StockDetailSchema]:
    """銘柄詳細を取得"""
    try:
        repo = PostgresCANSLIMStockRepository(db)

        stock = repo.find_by_symbol_and_date(
            symbol=symbol.upper(),
            target_date=date.today(),
        )

        if stock is None:
            raise HTTPException(
                status_code=404,
                detail=f"Stock not found: {symbol}",
            )

        response = _stock_to_detail(stock)

        return ApiResponse(success=True, data=response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stock detail: {e}",
        )
