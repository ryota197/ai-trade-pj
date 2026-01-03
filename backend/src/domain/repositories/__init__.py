"""Domain Repositories"""

from src.domain.repositories.canslim_stock_repository import CANSLIMStockRepository
from src.domain.repositories.market_snapshot_repository import MarketSnapshotRepository
from src.domain.repositories.trade_repository import TradeRepository
from src.domain.repositories.watchlist_repository import WatchlistRepository

__all__ = [
    # Screener Context
    "CANSLIMStockRepository",
    # Market Context
    "MarketSnapshotRepository",
    # Portfolio Context
    "TradeRepository",
    "WatchlistRepository",
]
