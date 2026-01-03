"""CAN-SLIMスコア計算ジョブ (Job 3)"""

from dataclasses import dataclass, field

from src.domain.repositories import StockMetricsRepository, StockQueryRepository
from src.domain.services import CANSLIMInput, CANSLIMScoreCalculator
from src.jobs.lib.base import Job


@dataclass
class CalculateCANSLIMOutput:
    """CAN-SLIMスコア計算出力"""

    total_stocks: int
    updated_count: int
    errors: list[dict] = field(default_factory=list)


class CalculateCANSLIMJob(Job[None, CalculateCANSLIMOutput]):
    """
    CAN-SLIMスコア計算ジョブ (Job 3)

    DB内の全銘柄データからCAN-SLIMスコアを計算し、
    stock_metrics.canslim_score を一括更新する。

    責務:
        - DB内の当日分の全銘柄データを取得（price + metrics）
        - CAN-SLIMスコア計算（CANSLIMScoreCalculator に委譲）
        - stock_metrics.canslim_score を一括更新

    注意:
        - 外部API呼び出しなし
        - Job 2 完了後に実行（rs_rating が必要）
        - 500銘柄でも数秒で完了
    """

    name = "calculate_canslim"

    def __init__(
        self,
        stock_query_repository: StockQueryRepository,
        stock_metrics_repository: StockMetricsRepository,
        canslim_calculator: CANSLIMScoreCalculator | None = None,
    ) -> None:
        self._query_repo = stock_query_repository
        self._metrics_repo = stock_metrics_repository
        self._calculator = canslim_calculator or CANSLIMScoreCalculator()

    async def execute(self, _: None = None) -> CalculateCANSLIMOutput:
        """ジョブ実行"""
        errors: list[dict] = []

        # 1. 当日分の全銘柄データを取得（rs_rating が設定済みのもの）
        stocks = await self._query_repo.get_all_for_canslim()

        if not stocks:
            return CalculateCANSLIMOutput(
                total_stocks=0,
                updated_count=0,
                errors=[{"error": "No stocks with rs_rating found"}],
            )

        # 2. 各銘柄のCAN-SLIMスコアを計算
        updates: list[tuple[str, int]] = []
        for stock_data in stocks:
            symbol = stock_data.identity.symbol
            try:
                # 計算に必要なデータを抽出
                input_data = self._build_input(stock_data)
                canslim_score = self._calculator.calculate(input_data)
                updates.append((symbol, canslim_score))
            except Exception as e:
                errors.append({"symbol": symbol, "error": str(e)})

        # 3. 一括更新
        updated_count = 0
        if updates:
            updated_count = await self._metrics_repo.bulk_update_canslim_score(updates)

        return CalculateCANSLIMOutput(
            total_stocks=len(stocks),
            updated_count=updated_count,
            errors=errors,
        )

    def _build_input(self, stock_data) -> CANSLIMInput:
        """StockDataからCANSLIMInputを構築"""
        price = stock_data.price
        metrics = stock_data.metrics

        return CANSLIMInput(
            eps_growth_quarterly=(
                metrics.eps_growth_quarterly if metrics else None
            ),
            eps_growth_annual=metrics.eps_growth_annual if metrics else None,
            price=price.price if price else None,
            week_52_high=price.week_52_high if price else None,
            volume=price.volume if price else None,
            avg_volume_50d=price.avg_volume_50d if price else None,
            rs_rating=metrics.rs_rating if metrics else None,
            institutional_ownership=(
                metrics.institutional_ownership if metrics else None
            ),
        )
