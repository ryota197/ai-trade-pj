"""Pydanticスキーマ"""

from src.presentation.schemas.common import ApiResponse, ErrorDetail
from src.presentation.schemas.health import HealthResponse
from src.presentation.schemas.market import (
    MarketIndicatorsResponse,
    MarketStatusResponse,
)
from src.presentation.schemas.quote import (
    FinancialsResponse,
    HistoryItem,
    HistoryResponse,
    QuoteResponse,
)
from src.presentation.schemas.screener import (
    CANSLIMCriteriaSchema,
    CANSLIMScoreSchema,
    ScreenerFilterSchema,
    ScreenerResponse,
    StockDetailSchema,
    StockSummarySchema,
)

__all__ = [
    # Common
    "ApiResponse",
    "ErrorDetail",
    # Health
    "HealthResponse",
    # Market
    "MarketStatusResponse",
    "MarketIndicatorsResponse",
    # Quote/Data
    "QuoteResponse",
    "HistoryItem",
    "HistoryResponse",
    "FinancialsResponse",
    # Screener
    "CANSLIMCriteriaSchema",
    "CANSLIMScoreSchema",
    "ScreenerFilterSchema",
    "ScreenerResponse",
    "StockDetailSchema",
    "StockSummarySchema",
]
