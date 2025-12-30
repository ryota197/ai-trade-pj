"""Domain Repositories"""

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
