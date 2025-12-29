"""Infrastructure Repositories"""

from src.infrastructure.repositories.postgres_benchmark_repository import (
    PostgresBenchmarkRepository,
)
from src.infrastructure.repositories.postgres_market_repository import (
    PostgresMarketRepository,
)
from src.infrastructure.repositories.postgres_price_snapshot_repository import (
    PostgresPriceSnapshotRepository,
)
from src.infrastructure.repositories.postgres_stock_identity_repository import (
    PostgresStockIdentityRepository,
)
from src.infrastructure.repositories.postgres_stock_metrics_repository import (
    PostgresStockMetricsRepository,
)
from src.infrastructure.repositories.postgres_stock_query_repository import (
    PostgresStockQueryRepository,
)

# 旧リポジトリ（互換性のため残存、移行後に削除）
from src.infrastructure.repositories.postgres_screener_repository import (
    PostgresScreenerRepository,
)
from src.infrastructure.repositories.postgres_stock_repository import (
    PostgresStockRepository,
)

__all__ = [
    # 正規化構造（5リポジトリ）
    "PostgresStockIdentityRepository",
    "PostgresPriceSnapshotRepository",
    "PostgresStockMetricsRepository",
    "PostgresBenchmarkRepository",
    "PostgresStockQueryRepository",
    # その他
    "PostgresMarketRepository",
    # 旧リポジトリ（互換性のため）
    "PostgresStockRepository",
    "PostgresScreenerRepository",
]
