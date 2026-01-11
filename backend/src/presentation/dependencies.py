"""依存性注入設定"""

from fastapi import Depends
from sqlalchemy.orm import Session

from src.infrastructure.database.connection import get_db
from src.infrastructure.gateways.symbol_provider import StaticSymbolProvider
from src.infrastructure.gateways.yfinance_gateway import YFinanceGateway
from src.infrastructure.repositories.postgres_canslim_stock_repository import (
    PostgresCANSLIMStockRepository,
)
from src.infrastructure.repositories.postgres_flow_execution_repository import (
    PostgresFlowExecutionRepository,
)
from src.infrastructure.repositories.postgres_job_execution_repository import (
    PostgresJobExecutionRepository,
)
from src.jobs.executions.calculate_canslim import CalculateCANSLIMJob
from src.jobs.executions.calculate_rs_rating import CalculateRSRatingJob
from src.jobs.executions.collect_stock_data import CollectStockDataJob
from src.jobs.flows.refresh_screener import RefreshScreenerFlow

# ============================================================
# Admin (Jobs/Flows)
# ============================================================


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
    )

    return RefreshScreenerFlow(
        collect_job=collect_job,
        rs_rating_job=rs_rating_job,
        canslim_job=canslim_job,
        symbol_provider=symbol_provider,
        flow_repository=flow_repo,
        job_repository=job_repo,
    )
