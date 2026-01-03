"""Job Executions - 個別ジョブ実装"""

from src.jobs.executions.calculate_canslim import (
    CalculateCANSLIMJob,
    CalculateCANSLIMOutput,
)
from src.jobs.executions.calculate_rs_rating import (
    CalculateRSRatingJob,
    CalculateRSRatingOutput,
)
from src.jobs.executions.collect_benchmarks import (
    CollectBenchmarksInput,
    CollectBenchmarksJob,
    CollectBenchmarksOutput,
)
from src.jobs.executions.collect_stock_data import (
    CollectInput,
    CollectOutput,
    CollectStockDataJob,
)

__all__ = [
    # Job 0: ベンチマーク収集
    "CollectBenchmarksInput",
    "CollectBenchmarksOutput",
    "CollectBenchmarksJob",
    # Job 1: データ収集
    "CollectInput",
    "CollectOutput",
    "CollectStockDataJob",
    # Job 2: RS Rating 計算
    "CalculateRSRatingOutput",
    "CalculateRSRatingJob",
    # Job 3: CAN-SLIM スコア計算
    "CalculateCANSLIMOutput",
    "CalculateCANSLIMJob",
]
