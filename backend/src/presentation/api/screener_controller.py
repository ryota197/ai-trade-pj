"""スクリーナーAPI"""

from fastapi import APIRouter, Depends, HTTPException, Query

from src.application.dto.screener_dto import (
    ScreenerFilterInput,
    StockDetailInput,
)
from src.application.use_cases.screener.get_stock_detail import GetStockDetailUseCase
from src.application.use_cases.screener.screen_canslim_stocks import (
    ScreenCANSLIMStocksUseCase,
)
from src.domain.constants import CANSLIMDefaults
from src.presentation.dependencies import (
    get_screen_canslim_use_case,
    get_stock_detail_use_case,
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

# 定数エイリアス（可読性向上）
_D = CANSLIMDefaults

router = APIRouter(prefix="/screener", tags=["screener"])


@router.get(
    "/canslim",
    response_model=ApiResponse[ScreenerResponse],
    summary="CAN-SLIMスクリーニング",
    description="CAN-SLIM条件を満たす銘柄をスクリーニングする",
)
async def screen_canslim_stocks(
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
    use_case: ScreenCANSLIMStocksUseCase = Depends(get_screen_canslim_use_case),
) -> ApiResponse[ScreenerResponse]:
    """CAN-SLIM条件でスクリーニングを実行"""
    try:
        # 入力DTOを構築
        filter_input = ScreenerFilterInput(
            min_rs_rating=min_rs_rating,
            min_eps_growth_quarterly=min_eps_growth_quarterly,
            min_eps_growth_annual=min_eps_growth_annual,
            max_distance_from_52w_high=max_distance_from_52w_high,
            min_volume_ratio=min_volume_ratio,
            min_canslim_score=min_canslim_score,
            limit=limit,
            offset=offset,
        )

        # ユースケース実行
        result = await use_case.execute(filter_input)

        # レスポンススキーマに変換
        stocks_schema = [
            StockSummarySchema(
                symbol=stock.symbol,
                name=stock.name,
                price=stock.price,
                change_percent=stock.change_percent,
                rs_rating=stock.rs_rating,
                canslim_score=stock.canslim_score,
                volume_ratio=stock.volume_ratio,
                distance_from_52w_high=stock.distance_from_52w_high,
            )
            for stock in result.stocks
        ]

        filter_schema = ScreenerFilterSchema(
            min_rs_rating=filter_input.min_rs_rating,
            min_eps_growth_quarterly=filter_input.min_eps_growth_quarterly,
            min_eps_growth_annual=filter_input.min_eps_growth_annual,
            max_distance_from_52w_high=filter_input.max_distance_from_52w_high,
            min_volume_ratio=filter_input.min_volume_ratio,
            min_canslim_score=filter_input.min_canslim_score,
        )

        response = ScreenerResponse(
            total_count=result.total_count,
            stocks=stocks_schema,
            filter_applied=filter_schema,
            screened_at=result.screened_at,
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
async def get_stock_detail(
    symbol: str,
    use_case: GetStockDetailUseCase = Depends(get_stock_detail_use_case),
) -> ApiResponse[StockDetailSchema]:
    """銘柄詳細を取得"""
    try:
        # 入力DTOを構築
        input_dto = StockDetailInput(symbol=symbol.upper())

        # ユースケース実行
        result = await use_case.execute(input_dto)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Stock not found: {symbol}",
            )

        # CAN-SLIMスコアをスキーマに変換
        canslim_schema = None
        if result.canslim_score is not None:
            cs = result.canslim_score
            canslim_schema = CANSLIMScoreSchema(
                total_score=cs.total_score,
                overall_grade=cs.overall_grade,
                passing_count=cs.passing_count,
                c_score=CANSLIMCriteriaSchema(
                    name=cs.c_score.name,
                    score=cs.c_score.score,
                    grade=cs.c_score.grade,
                    value=cs.c_score.value,
                    threshold=cs.c_score.threshold,
                    description=cs.c_score.description,
                ),
                a_score=CANSLIMCriteriaSchema(
                    name=cs.a_score.name,
                    score=cs.a_score.score,
                    grade=cs.a_score.grade,
                    value=cs.a_score.value,
                    threshold=cs.a_score.threshold,
                    description=cs.a_score.description,
                ),
                n_score=CANSLIMCriteriaSchema(
                    name=cs.n_score.name,
                    score=cs.n_score.score,
                    grade=cs.n_score.grade,
                    value=cs.n_score.value,
                    threshold=cs.n_score.threshold,
                    description=cs.n_score.description,
                ),
                s_score=CANSLIMCriteriaSchema(
                    name=cs.s_score.name,
                    score=cs.s_score.score,
                    grade=cs.s_score.grade,
                    value=cs.s_score.value,
                    threshold=cs.s_score.threshold,
                    description=cs.s_score.description,
                ),
                l_score=CANSLIMCriteriaSchema(
                    name=cs.l_score.name,
                    score=cs.l_score.score,
                    grade=cs.l_score.grade,
                    value=cs.l_score.value,
                    threshold=cs.l_score.threshold,
                    description=cs.l_score.description,
                ),
                i_score=CANSLIMCriteriaSchema(
                    name=cs.i_score.name,
                    score=cs.i_score.score,
                    grade=cs.i_score.grade,
                    value=cs.i_score.value,
                    threshold=cs.i_score.threshold,
                    description=cs.i_score.description,
                ),
            )

        # レスポンススキーマに変換
        response = StockDetailSchema(
            symbol=result.symbol,
            name=result.name,
            price=result.price,
            change=result.change,
            change_percent=result.change_percent,
            volume=result.volume,
            avg_volume=result.avg_volume,
            market_cap=result.market_cap,
            pe_ratio=result.pe_ratio,
            week_52_high=result.week_52_high,
            week_52_low=result.week_52_low,
            eps_growth_quarterly=result.eps_growth_quarterly,
            eps_growth_annual=result.eps_growth_annual,
            rs_rating=result.rs_rating,
            institutional_ownership=result.institutional_ownership,
            canslim_score=canslim_schema,
            updated_at=result.updated_at,
        )

        return ApiResponse(success=True, data=response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stock detail: {e}",
        )
