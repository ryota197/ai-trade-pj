"""市場ベンチマーク エンティティ"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MarketBenchmark:
    """
    市場ベンチマーク

    S&P500やNASDAQ100のパフォーマンス。Job 0 で1日1回更新。
    対応テーブル: market_benchmarks

    weighted_performance: IBD式加重パフォーマンス
        計算式: 3M×40% + 6M×20% + 9M×20% + 12M×20%
        Job 1 で RS Rating 計算時に使用
    """

    symbol: str  # "^GSPC" (S&P500), "^NDX" (NASDAQ100)
    performance_1y: float | None
    performance_9m: float | None
    performance_6m: float | None
    performance_3m: float | None
    performance_1m: float | None
    weighted_performance: float | None  # IBD式加重パフォーマンス
    recorded_at: datetime
