"""依存性注入設定"""

from fastapi import Depends
from sqlalchemy.orm import Session

from src.application.use_cases.market import (
    GetMarketIndicatorsUseCase,
    GetMarketStatusUseCase,
)
from src.application.use_cases.screener.get_stock_detail import GetStockDetailUseCase
from src.application.use_cases.screener.screen_canslim_stocks import (
    ScreenCANSLIMStocksUseCase,
)
from src.domain.services.market_analyzer import MarketAnalyzer
from src.domain.services.rs_rating_calculator import RSRatingCalculator
from src.infrastructure.database.connection import get_db
from src.infrastructure.gateways.yfinance_gateway import YFinanceGateway
from src.infrastructure.gateways.yfinance_market_data_gateway import (
    YFinanceMarketDataGateway,
)
from src.infrastructure.repositories.postgres_screener_repository import (
    PostgresScreenerRepository,
)


def get_market_status_use_case() -> GetMarketStatusUseCase:
    """
    GetMarketStatusUseCaseの依存性を解決

    Returns:
        GetMarketStatusUseCase: マーケット状態取得ユースケース
    """
    market_data_repo = YFinanceMarketDataGateway()
    market_analyzer = MarketAnalyzer()

    return GetMarketStatusUseCase(
        market_data_repo=market_data_repo,
        market_analyzer=market_analyzer,
    )


def get_market_indicators_use_case() -> GetMarketIndicatorsUseCase:
    """
    GetMarketIndicatorsUseCaseの依存性を解決

    Returns:
        GetMarketIndicatorsUseCase: マーケット指標取得ユースケース
    """
    market_data_repo = YFinanceMarketDataGateway()

    return GetMarketIndicatorsUseCase(market_data_repo=market_data_repo)


def get_screen_canslim_use_case(
    db: Session = Depends(get_db),
) -> ScreenCANSLIMStocksUseCase:
    """
    ScreenCANSLIMStocksUseCaseの依存性を解決

    Args:
        db: データベースセッション

    Returns:
        ScreenCANSLIMStocksUseCase: CAN-SLIMスクリーニングユースケース
    """
    stock_repo = PostgresScreenerRepository(db)
    financial_gateway = YFinanceGateway()
    rs_calculator = RSRatingCalculator()

    return ScreenCANSLIMStocksUseCase(
        stock_repository=stock_repo,
        financial_gateway=financial_gateway,
        rs_calculator=rs_calculator,
    )


def get_stock_detail_use_case(
    db: Session = Depends(get_db),
) -> GetStockDetailUseCase:
    """
    GetStockDetailUseCaseの依存性を解決

    Args:
        db: データベースセッション

    Returns:
        GetStockDetailUseCase: 銘柄詳細取得ユースケース
    """
    stock_repo = PostgresScreenerRepository(db)

    return GetStockDetailUseCase(stock_repository=stock_repo)
