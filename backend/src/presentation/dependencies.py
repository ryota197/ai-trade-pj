"""依存性注入設定"""

from fastapi import Depends
from sqlalchemy.orm import Session

from src.application.use_cases.admin.refresh_screener_data import (
    RefreshScreenerDataUseCase,
)
from src.application.use_cases.market import (
    GetMarketIndicatorsUseCase,
    GetMarketStatusUseCase,
)
from src.application.use_cases.portfolio import (
    GetPerformanceUseCase,
    GetTradesUseCase,
    ManageWatchlistUseCase,
    RecordTradeUseCase,
)
from src.application.use_cases.screener.get_stock_detail import GetStockDetailUseCase
from src.application.use_cases.screener.screen_canslim_stocks import (
    ScreenCANSLIMStocksUseCase,
)
from src.domain.services.market_analyzer import MarketAnalyzer
from src.domain.services.rs_calculator import RSCalculator
from src.infrastructure.database.connection import get_db
from src.infrastructure.external.symbol_provider import StaticSymbolProvider
from src.infrastructure.gateways.yfinance_gateway import YFinanceGateway
from src.infrastructure.gateways.yfinance_market_data_gateway import (
    YFinanceMarketDataGateway,
)
from src.infrastructure.repositories.postgres_refresh_job_repository import (
    PostgresRefreshJobRepository,
)
from src.infrastructure.repositories.postgres_canslim_stock_repository import (
    PostgresCANSLIMStockRepository,
)
from src.infrastructure.repositories.postgres_flow_execution_repository import (
    PostgresFlowExecutionRepository,
)
from src.infrastructure.repositories.postgres_job_execution_repository import (
    PostgresJobExecutionRepository,
)
from src.infrastructure.repositories.postgres_trade_repository import (
    PostgresTradeRepository,
)
from src.infrastructure.repositories.postgres_watchlist_repository import (
    PostgresWatchlistRepository,
)
from src.jobs.executions.collect_stock_data import CollectStockDataJob
from src.jobs.executions.calculate_rs_rating import CalculateRSRatingJob
from src.jobs.executions.calculate_canslim import CalculateCANSLIMJob
from src.jobs.flows.refresh_screener import RefreshScreenerFlow


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
    stock_repo = PostgresCANSLIMStockRepository(db)

    return ScreenCANSLIMStocksUseCase(
        canslim_stock_repository=stock_repo,
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
    stock_repo = PostgresCANSLIMStockRepository(db)

    return GetStockDetailUseCase(canslim_stock_repository=stock_repo)


# ============================================================
# Portfolio Use Cases
# ============================================================


def get_manage_watchlist_use_case(
    db: Session = Depends(get_db),
) -> ManageWatchlistUseCase:
    """
    ManageWatchlistUseCaseの依存性を解決

    Args:
        db: データベースセッション

    Returns:
        ManageWatchlistUseCase: ウォッチリスト管理ユースケース
    """
    watchlist_repo = PostgresWatchlistRepository(db)

    return ManageWatchlistUseCase(watchlist_repository=watchlist_repo)


def get_record_trade_use_case(
    db: Session = Depends(get_db),
) -> RecordTradeUseCase:
    """
    RecordTradeUseCaseの依存性を解決

    Args:
        db: データベースセッション

    Returns:
        RecordTradeUseCase: トレード記録ユースケース
    """
    trade_repo = PostgresTradeRepository(db)

    return RecordTradeUseCase(trade_repository=trade_repo)


def get_trades_use_case(
    db: Session = Depends(get_db),
) -> GetTradesUseCase:
    """
    GetTradesUseCaseの依存性を解決

    Args:
        db: データベースセッション

    Returns:
        GetTradesUseCase: トレード取得ユースケース
    """
    trade_repo = PostgresTradeRepository(db)
    financial_gateway = YFinanceGateway()

    return GetTradesUseCase(
        trade_repository=trade_repo,
        financial_gateway=financial_gateway,
    )


def get_performance_use_case(
    db: Session = Depends(get_db),
) -> GetPerformanceUseCase:
    """
    GetPerformanceUseCaseの依存性を解決

    Args:
        db: データベースセッション

    Returns:
        GetPerformanceUseCase: パフォーマンス取得ユースケース
    """
    trade_repo = PostgresTradeRepository(db)

    return GetPerformanceUseCase(
        trade_repository=trade_repo,
    )


# ============================================================
# Admin Use Cases
# ============================================================


def get_refresh_screener_use_case(
    db: Session = Depends(get_db),
) -> RefreshScreenerDataUseCase:
    """
    RefreshScreenerDataUseCaseの依存性を解決

    Args:
        db: データベースセッション

    Returns:
        RefreshScreenerDataUseCase: スクリーニングデータ更新ユースケース

    Deprecated:
        Phase 2以降は get_refresh_screener_flow を使用してください。
    """
    job_repo = PostgresRefreshJobRepository(db)
    stock_repo = PostgresCANSLIMStockRepository(db)
    financial_gateway = YFinanceGateway()
    rs_calculator = RSCalculator()

    return RefreshScreenerDataUseCase(
        job_repository=job_repo,
        stock_repository=stock_repo,
        financial_gateway=financial_gateway,
        rs_calculator=rs_calculator,
    )


def get_refresh_screener_flow(
    db: Session = Depends(get_db),
) -> RefreshScreenerFlow:
    """
    RefreshScreenerFlowの依存性を解決

    Args:
        db: データベースセッション

    Returns:
        RefreshScreenerFlow: スクリーナーデータ更新フロー
    """
    stock_repo = PostgresCANSLIMStockRepository(db)
    flow_repo = PostgresFlowExecutionRepository(db)
    job_repo = PostgresJobExecutionRepository(db)
    financial_gateway = YFinanceGateway()
    symbol_provider = StaticSymbolProvider()

    # Job 1: データ収集
    collect_job = CollectStockDataJob(
        stock_repository=stock_repo,
        financial_gateway=financial_gateway,
    )

    # Job 2: RS Rating計算
    rs_rating_job = CalculateRSRatingJob(
        stock_repository=stock_repo,
    )

    # Job 3: CAN-SLIMスコア計算
    canslim_job = CalculateCANSLIMJob(
        stock_repository=stock_repo,
        # market_repository は省略（デフォルトでNEUTRAL）
    )

    return RefreshScreenerFlow(
        collect_job=collect_job,
        rs_rating_job=rs_rating_job,
        canslim_job=canslim_job,
        symbol_provider=symbol_provider,
        flow_repository=flow_repo,
        job_repository=job_repo,
    )
