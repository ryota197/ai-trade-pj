"""Adapters layer - External system connections"""

from src.adapters.database import Base, SessionLocal, engine, get_db
from src.adapters.symbol_provider import (
    StaticSymbolProvider,
    SymbolProvider,
    WikipediaSymbolProvider,
)
from src.adapters.yfinance import (
    FinancialMetrics,
    FundamentalIndicators,
    FundamentalsGateway,
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
    "FundamentalsGateway",
    "QuoteData",
    "HistoricalBar",
    "RawFinancialData",
    "FinancialMetrics",
    "FundamentalIndicators",
    # Symbol Provider
    "SymbolProvider",
    "WikipediaSymbolProvider",
    "StaticSymbolProvider",
]
