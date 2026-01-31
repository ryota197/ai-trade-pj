"""依存性注入設定"""

from fastapi import Depends
from sqlalchemy.orm import Session

from src.adapters.database import get_db
from src.adapters.symbol_provider import StaticSymbolProvider
from src.adapters.yfinance import YFinanceGateway
from src.queries import (
    CANSLIMStockQuery,
    FlowExecutionQuery,
    JobExecutionQuery,
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
    stock_query = CANSLIMStockQuery(db)
    flow_query = FlowExecutionQuery(db)
    job_query = JobExecutionQuery(db)
    financial_gateway = YFinanceGateway()
    symbol_provider = StaticSymbolProvider()

    # Job 1: データ収集
    collect_job = CollectStockDataJob(
        stock_query=stock_query,
        financial_gateway=financial_gateway,
    )

    # Job 2: RS Rating計算
    rs_rating_job = CalculateRSRatingJob(
        stock_query=stock_query,
    )

    # Job 3: CAN-SLIMスコア計算
    canslim_job = CalculateCANSLIMJob(
        stock_query=stock_query,
    )

    return RefreshScreenerFlow(
        collect_job=collect_job,
        rs_rating_job=rs_rating_job,
        canslim_job=canslim_job,
        symbol_provider=symbol_provider,
        flow_query=flow_query,
        job_query=job_query,
    )
