"""スクリーナー関連スキーマ"""

from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.constants import CANSLIMThresholds

# 定数エイリアス
_T = CANSLIMThresholds


class CANSLIMCriteriaSchema(BaseModel):
    """CAN-SLIM基準項目スキーマ"""

    name: str = Field(..., description="基準名（C, A, N, S, L, I）")
    score: int = Field(..., ge=0, le=100, description="スコア（0-100）")
    grade: str = Field(..., description="グレード（A, B, C, D, F）")
    value: float | None = Field(None, description="実績値")
    threshold: float = Field(..., description="閾値")
    description: str = Field(..., description="説明")


class CANSLIMScoreSchema(BaseModel):
    """CAN-SLIMスコアスキーマ"""

    total_score: int = Field(..., ge=0, le=100, description="総合スコア")
    overall_grade: str = Field(..., description="総合グレード")
    passing_count: int = Field(..., ge=0, le=6, description="合格基準数")
    c_score: CANSLIMCriteriaSchema = Field(..., description="C - Current Quarterly Earnings")
    a_score: CANSLIMCriteriaSchema = Field(..., description="A - Annual Earnings")
    n_score: CANSLIMCriteriaSchema = Field(..., description="N - New High")
    s_score: CANSLIMCriteriaSchema = Field(..., description="S - Supply and Demand")
    l_score: CANSLIMCriteriaSchema = Field(..., description="L - Leader")
    i_score: CANSLIMCriteriaSchema = Field(..., description="I - Institutional Sponsorship")


class StockSummarySchema(BaseModel):
    """銘柄サマリースキーマ（一覧表示用）"""

    symbol: str = Field(..., description="ティッカーシンボル")
    name: str = Field(..., description="銘柄名")
    price: float = Field(..., description="現在株価")
    change_percent: float = Field(..., description="変動率（%）")
    rs_rating: int = Field(..., ge=1, le=99, description="RS Rating")
    canslim_score: int = Field(..., ge=0, le=100, description="CAN-SLIMスコア")
    volume_ratio: float = Field(..., description="出来高倍率")
    distance_from_52w_high: float = Field(..., description="52週高値からの乖離率（%）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "NVDA",
                "name": "NVIDIA Corporation",
                "price": 450.25,
                "change_percent": 2.35,
                "rs_rating": 98,
                "canslim_score": 95,
                "volume_ratio": 1.8,
                "distance_from_52w_high": 5.2,
            }
        }
    }


class ScreenerFilterSchema(BaseModel):
    """スクリーニングフィルタースキーマ"""

    min_rs_rating: int = Field(
        _T.MIN_RS_RATING, ge=1, le=99, description="最小RS Rating"
    )
    min_eps_growth_quarterly: float = Field(
        _T.MIN_EPS_GROWTH_QUARTERLY, description="最小四半期EPS成長率（%）"
    )
    min_eps_growth_annual: float = Field(
        _T.MIN_EPS_GROWTH_ANNUAL, description="最小年間EPS成長率（%）"
    )
    max_distance_from_52w_high: float = Field(
        _T.MAX_DISTANCE_FROM_52W_HIGH, description="最大52週高値乖離率（%）"
    )
    min_volume_ratio: float = Field(
        _T.MIN_VOLUME_RATIO, description="最小出来高倍率"
    )
    min_canslim_score: int = Field(
        _T.MIN_CANSLIM_SCORE, ge=0, le=100, description="最小CAN-SLIMスコア"
    )


class ScreenerResponse(BaseModel):
    """スクリーニング結果レスポンス"""

    total_count: int = Field(..., description="該当銘柄総数")
    stocks: list[StockSummarySchema] = Field(..., description="銘柄リスト")
    filter_applied: ScreenerFilterSchema = Field(..., description="適用されたフィルター")
    screened_at: datetime = Field(..., description="スクリーニング実行日時")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_count": 15,
                "stocks": [
                    {
                        "symbol": "NVDA",
                        "name": "NVIDIA Corporation",
                        "price": 450.25,
                        "change_percent": 2.35,
                        "rs_rating": 98,
                        "canslim_score": 95,
                        "volume_ratio": 1.8,
                        "distance_from_52w_high": 5.2,
                    }
                ],
                "filter_applied": {
                    "min_rs_rating": 80,
                    "min_eps_growth_quarterly": 25.0,
                    "min_eps_growth_annual": 25.0,
                    "max_distance_from_52w_high": 15.0,
                    "min_volume_ratio": 1.5,
                    "min_canslim_score": 70,
                },
                "screened_at": "2024-01-15T10:30:00Z",
            }
        }
    }


class StockDetailSchema(BaseModel):
    """銘柄詳細スキーマ"""

    symbol: str = Field(..., description="ティッカーシンボル")
    name: str = Field(..., description="銘柄名")
    price: float = Field(..., description="現在株価")
    change: float = Field(..., description="変動額")
    change_percent: float = Field(..., description="変動率（%）")
    volume: int = Field(..., description="出来高")
    avg_volume: int = Field(..., description="平均出来高")
    market_cap: float | None = Field(None, description="時価総額")
    pe_ratio: float | None = Field(None, description="PER")
    week_52_high: float = Field(..., description="52週高値")
    week_52_low: float = Field(..., description="52週安値")
    eps_growth_quarterly: float | None = Field(None, description="四半期EPS成長率（%）")
    eps_growth_annual: float | None = Field(None, description="年間EPS成長率（%）")
    rs_rating: int = Field(..., ge=1, le=99, description="RS Rating")
    institutional_ownership: float | None = Field(None, description="機関投資家保有率（%）")
    canslim_score: CANSLIMScoreSchema | None = Field(None, description="CAN-SLIMスコア")
    updated_at: datetime = Field(..., description="最終更新日時")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "NVDA",
                "name": "NVIDIA Corporation",
                "price": 450.25,
                "change": 10.50,
                "change_percent": 2.35,
                "volume": 45000000,
                "avg_volume": 35000000,
                "market_cap": 1100000000000,
                "pe_ratio": 65.2,
                "week_52_high": 480.00,
                "week_52_low": 280.00,
                "eps_growth_quarterly": 122.5,
                "eps_growth_annual": 85.3,
                "rs_rating": 98,
                "institutional_ownership": 72.5,
                "canslim_score": None,
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }
    }
