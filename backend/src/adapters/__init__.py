"""Adapters layer - External system connections"""

from src.adapters.database import Base, SessionLocal, engine, get_db
from src.adapters.symbol_provider import (
    StaticSymbolProvider,
    SymbolProvider,
    WikipediaSymbolProvider,
)
from src.adapters.yfinance import (
    FinancialMetrics,
    HistoricalBar,
    QuoteData,
    RawFinancialData,
    YFinanceGateway,
    YFinanceMarketDataGateway,
)

__all__ = [
    # Database
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    # YFinance
    "YFinanceGateway",
    "YFinanceMarketDataGateway",
    "QuoteData",
    "HistoricalBar",
    "RawFinancialData",
    "FinancialMetrics",
    # Symbol Provider
    "SymbolProvider",
    "WikipediaSymbolProvider",
    "StaticSymbolProvider",
]
