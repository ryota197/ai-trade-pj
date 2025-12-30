"""RS Rating 計算ジョブ (Job 2)"""

from dataclasses import dataclass, field

from src.domain.repositories import StockMetricsRepository
from src.domain.services import RelativeStrengthCalculator
from src.jobs.lib.base import Job


@dataclass
class CalculateRSRatingOutput:
    """RS Rating 計算出力"""

    total_stocks: int
    updated_count: int
    errors: list[dict] = field(default_factory=list)


class CalculateRSRatingJob(Job[None, CalculateRSRatingOutput]):
    """
    RS Rating 計算ジョブ (Job 2)

    DB内の全銘柄の relative_strength からパーセンタイルランキングを計算し、
    rs_rating (1-99) を一括更新する。

    責務:
        - DB内の全銘柄の最新 relative_strength を取得
        - パーセンタイル計算（RelativeStrengthCalculator に委譲）
        - stock_metrics.rs_rating を一括更新

    注意:
        - 外部API呼び出しなし
        - Job 1 完了後に実行
        - 500銘柄でも数秒で完了
    """

    name = "calculate_rs_rating"

    def __init__(
        self,
        stock_metrics_repository: StockMetricsRepository,
        rs_calculator: RelativeStrengthCalculator | None = None,
    ) -> None:
        self._metrics_repo = stock_metrics_repository
        self._rs_calculator = rs_calculator or RelativeStrengthCalculator()

    async def execute(self, _: None = None) -> CalculateRSRatingOutput:
        """ジョブ実行"""
        errors: list[dict] = []

        # 1. 全銘柄の最新 relative_strength を取得
        stocks_with_rs = await self._metrics_repo.get_all_latest_relative_strength()

        if not stocks_with_rs:
            return CalculateRSRatingOutput(
                total_stocks=0,
                updated_count=0,
                errors=[{"error": "No stocks with relative_strength found"}],
            )

        # 2. 全銘柄の relative_strength リストを作成
        all_relative_strengths = [rs for _, rs in stocks_with_rs]

        # 3. 各銘柄の rs_rating を計算
        updates: list[tuple[str, int]] = []
        for symbol, relative_strength in stocks_with_rs:
            try:
                rs_rating = self._rs_calculator.calculate_percentile_rank(
                    relative_strength, all_relative_strengths
                )
                updates.append((symbol, rs_rating))
            except Exception as e:
                errors.append({"symbol": symbol, "error": str(e)})

        # 4. 一括更新
        updated_count = 0
        if updates:
            updated_count = await self._metrics_repo.bulk_update_rs_rating(updates)

        return CalculateRSRatingOutput(
            total_stocks=len(stocks_with_rs),
            updated_count=updated_count,
            errors=errors,
        )
