"""市場ベンチマーク エンティティ"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MarketBenchmark:
    """
    市場ベンチマーク

    S&P500やNASDAQ100のパフォーマンス。Job 0 で1日1回更新。
    対応テーブル: market_benchmarks
    """

    symbol: str  # "^GSPC" (S&P500), "^NDX" (NASDAQ100)
    performance_1y: float | None
    performance_6m: float | None
    performance_3m: float | None
    performance_1m: float | None
    recorded_at: datetime
