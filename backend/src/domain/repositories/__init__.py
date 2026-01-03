"""Domain Repositories"""

from src.domain.repositories.canslim_stock_repository import CANSLIMStockRepository
from src.domain.repositories.market_snapshot_repository import MarketSnapshotRepository
from src.domain.repositories.trade_repository import TradeRepository
from src.domain.repositories.watchlist_repository import WatchlistRepository

from src.domain.repositories.benchmark_repository import BenchmarkRepository
from src.domain.repositories.price_snapshot_repository import PriceSnapshotRepository
from src.domain.repositories.stock_identity_repository import StockIdentityRepository
from src.domain.repositories.stock_metrics_repository import StockMetricsRepository
from src.domain.repositories.stock_query_repository import (
    ScreenerFilter,
    ScreenerResult,
    StockAggregate,
    StockQueryRepository,
)

__all__ = [
    # === 新設計（Phase 1） ===
    "CANSLIMStockRepository",
    # === 新設計（Phase 3） ===
    "TradeRepository",
    "MarketSnapshotRepository",
    "WatchlistRepository",
    # === 旧設計（Phase 4 で削除予定） ===
    # 単一テーブル リポジトリ
    "StockIdentityRepository",
    "PriceSnapshotRepository",
    "StockMetricsRepository",
    "BenchmarkRepository",
    # クエリ リポジトリ（読み取り専用）
    "StockQueryRepository",
    "StockAggregate",
    "ScreenerFilter",
    "ScreenerResult",
]
