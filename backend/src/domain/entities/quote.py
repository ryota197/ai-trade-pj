"""株価エンティティ"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Quote:
    """
    株価エンティティ

    現在の株価情報を表すドメインエンティティ。
    frozen=True で不変オブジェクトとして扱う。
    """

    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: float | None
    pe_ratio: float | None
    week_52_high: float | None
    week_52_low: float | None
    timestamp: datetime


@dataclass(frozen=True)
class HistoricalPrice:
    """
    過去の株価データ

    1日分の株価情報を表す値オブジェクト。
    """

    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
