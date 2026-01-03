"""Job Executions - 個別ジョブ実装"""

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

# TODO: Job 3 を新しいドメインモデルに合わせて修正後にインポートを有効化
# from src.jobs.executions.calculate_canslim import (
#     CalculateCANSLIMJob,
#     CalculateCANSLIMOutput,
# )

# TODO: Job 0 は現在の設計では不要（Job 1 内でベンチマーク取得）
# from src.jobs.executions.collect_benchmarks import (
#     CollectBenchmarksInput,
#     CollectBenchmarksJob,
#     CollectBenchmarksOutput,
# )

__all__ = [
    # Job 1: データ収集
    "CollectInput",
    "CollectOutput",
    "CollectStockDataJob",
    # Job 2: RS Rating 計算
    "CalculateRSRatingInput",
    "CalculateRSRatingOutput",
    "CalculateRSRatingJob",
    # TODO: Job 3 修正後に追加
    # "CalculateCANSLIMOutput",
    # "CalculateCANSLIMJob",
]
