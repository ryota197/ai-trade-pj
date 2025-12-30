"""Domain Entities - 後方互換性のためのre-export

注意: このモジュールは非推奨です。
- Entity/Value Object は `src.domain.models` からインポートしてください
- 定数は `src.domain.constants` からインポートしてください
"""

# Models（Entity / Value Object）
from src.domain.models import (
    CANSLIMScoreThresholds,
    CANSLIMWeights,
    HistoricalPrice,
    MarketBenchmark,
    MarketCondition,
    MarketStatus,
    PaperTrade,
    PriceSnapshot,
    Quote,
    StockIdentity,
    StockMetrics,
    WatchlistItem,
)

# Constants
from src.domain.constants import (
    CANSLIMDefaults,
    TradingDays,
)

__all__ = [
    # Models
    "StockIdentity",
    "PriceSnapshot",
    "StockMetrics",
    "Quote",
    "HistoricalPrice",
    "MarketBenchmark",
    "MarketCondition",
    "MarketStatus",
    "CANSLIMWeights",
    "CANSLIMScoreThresholds",
    "WatchlistItem",
    "PaperTrade",
    # Constants
    "CANSLIMDefaults",
    "TradingDays",
]
