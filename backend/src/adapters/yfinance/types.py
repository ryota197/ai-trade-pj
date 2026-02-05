"""yfinance データ型定義"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class QuoteData:
    """株価データ"""

    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    avg_volume: int
    market_cap: float | None
    pe_ratio: float | None
    week_52_high: float
    week_52_low: float
    timestamp: datetime


@dataclass(frozen=True)
class HistoricalBar:
    """過去の株価バー"""

    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True)
class RawFinancialData:
    """財務生データ"""

    symbol: str
    quarterly_eps: list[float]  # 四半期EPS（新しい順）
    annual_eps: list[float]  # 年間EPS（新しい順）
    eps_ttm: float | None  # 直近12ヶ月EPS
    revenue_growth: float | None  # 売上成長率（%）
    profit_margin: float | None  # 利益率（%）
    roe: float | None  # 自己資本利益率（%）
    debt_to_equity: float | None  # 負債資本比率
    institutional_ownership: float | None  # 機関投資家保有率（%）


@dataclass(frozen=True)
class FinancialMetrics:
    """財務指標（計算済み）"""

    symbol: str
    eps_ttm: float | None
    eps_growth_quarterly: float | None
    eps_growth_annual: float | None
    revenue_growth: float | None
    profit_margin: float | None
    roe: float | None
    debt_to_equity: float | None
    institutional_ownership: float | None


@dataclass(frozen=True)
class FundamentalIndicators:
    """ファンダメンタル指標"""

    symbol: str
    # バリュエーション
    forward_pe: float | None
    peg_ratio: float | None
    # 収益性
    roe: float | None
    operating_margin: float | None
    revenue_growth: float | None
    # リスク
    beta: float | None
