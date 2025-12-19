"""スクリーナー関連 DTO"""

from dataclasses import dataclass
from datetime import datetime


# ============================================================
# 入力DTO
# ============================================================


@dataclass(frozen=True)
class ScreenerFilterInput:
    """スクリーニングフィルター 入力DTO"""

    min_rs_rating: int = 80
    min_eps_growth_quarterly: float = 25.0
    min_eps_growth_annual: float = 25.0
    max_distance_from_52w_high: float = 15.0
    min_volume_ratio: float = 1.5
    min_canslim_score: int = 70
    min_market_cap: float | None = None
    max_market_cap: float | None = None
    symbols: list[str] | None = None
    limit: int = 20
    offset: int = 0


@dataclass(frozen=True)
class StockDetailInput:
    """銘柄詳細取得 入力DTO"""

    symbol: str


@dataclass(frozen=True)
class PriceHistoryInput:
    """株価履歴取得 入力DTO"""

    symbol: str
    period: str = "1y"  # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max
    interval: str = "1d"  # 1m, 5m, 15m, 1h, 1d, 1wk, 1mo


# ============================================================
# 出力DTO
# ============================================================


@dataclass(frozen=True)
class CANSLIMCriteriaOutput:
    """CAN-SLIM基準項目 出力DTO"""

    name: str
    score: int
    grade: str
    value: float | None
    threshold: float
    description: str


@dataclass(frozen=True)
class CANSLIMScoreOutput:
    """CAN-SLIMスコア 出力DTO"""

    total_score: int
    overall_grade: str
    passing_count: int
    c_score: CANSLIMCriteriaOutput
    a_score: CANSLIMCriteriaOutput
    n_score: CANSLIMCriteriaOutput
    s_score: CANSLIMCriteriaOutput
    l_score: CANSLIMCriteriaOutput
    i_score: CANSLIMCriteriaOutput


@dataclass(frozen=True)
class StockSummaryOutput:
    """銘柄サマリー 出力DTO（一覧表示用）"""

    symbol: str
    name: str
    price: float
    change_percent: float
    rs_rating: int
    canslim_score: int
    volume_ratio: float
    distance_from_52w_high: float


@dataclass(frozen=True)
class ScreenerResultOutput:
    """スクリーニング結果 出力DTO"""

    total_count: int
    stocks: list[StockSummaryOutput]
    filter_applied: ScreenerFilterInput
    screened_at: datetime


@dataclass(frozen=True)
class StockDetailOutput:
    """銘柄詳細 出力DTO"""

    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    avg_volume: int
    market_cap: float | None
    pe_ratio: float | None
    week_52_high: float
    week_52_low: float
    eps_growth_quarterly: float | None
    eps_growth_annual: float | None
    rs_rating: int
    institutional_ownership: float | None
    canslim_score: CANSLIMScoreOutput | None
    updated_at: datetime


@dataclass(frozen=True)
class PriceBarOutput:
    """株価バー 出力DTO"""

    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True)
class PriceHistoryOutput:
    """株価履歴 出力DTO"""

    symbol: str
    period: str
    interval: str
    bars: list[PriceBarOutput]
    retrieved_at: datetime


@dataclass(frozen=True)
class FinancialDataOutput:
    """財務データ 出力DTO"""

    symbol: str
    eps_current_quarter: float | None
    eps_previous_quarter: float | None
    eps_growth_quarterly: float | None
    eps_current_year: float | None
    eps_previous_year: float | None
    eps_growth_annual: float | None
    revenue_growth: float | None
    profit_margin: float | None
    roe: float | None
    debt_to_equity: float | None
    institutional_ownership: float | None
    retrieved_at: datetime
