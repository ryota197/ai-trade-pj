"""Job Executions - 個別ジョブ実装"""

from src.jobs.executions.base import Job
from src.jobs.executions.collect_stock_data import (
    CollectInput,
    CollectOutput,
    CollectStockDataJob,
)
from src.jobs.executions.calculate_rs_rating import (
    CalculateRSRatingInput,
    CalculateRSRatingJob,
    CalculateRSRatingOutput,
)
from src.jobs.executions.calculate_canslim import (
    CalculateCANSLIMInput,
    CalculateCANSLIMJob,
    CalculateCANSLIMOutput,
)

__all__ = [
    # Base
    "Job",
    # Job 1: データ収集
    "CollectInput",
    "CollectOutput",
    "CollectStockDataJob",
    # Job 2: RS Rating 計算
    "CalculateRSRatingInput",
    "CalculateRSRatingOutput",
    "CalculateRSRatingJob",
    # Job 3: CAN-SLIM スコア計算
    "CalculateCANSLIMInput",
    "CalculateCANSLIMOutput",
    "CalculateCANSLIMJob",
]
