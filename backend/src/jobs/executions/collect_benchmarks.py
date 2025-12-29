"""ベンチマーク収集ジョブ (Job 0)"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.application.interfaces.financial_data_gateway import (
    FinancialDataGateway,
)
from src.domain.constants import TradingDays
from src.domain.entities import MarketBenchmark
from src.domain.repositories import BenchmarkRepository
from src.domain.services import PriceBar, RelativeStrengthCalculator
from src.jobs.lib.base import Job


@dataclass
class CollectBenchmarksInput:
    """ベンチマーク収集入力"""

    indices: list[str] = field(default_factory=lambda: ["^GSPC", "^NDX"])


@dataclass
class CollectBenchmarksOutput:
    """ベンチマーク収集出力"""

    indices_updated: int
    benchmarks: dict[str, float]  # {"^GSPC": 25.3, "^NDX": 30.1} weighted_performance
    errors: list[dict] = field(default_factory=list)


class CollectBenchmarksJob(Job[CollectBenchmarksInput, CollectBenchmarksOutput]):
    """
    ベンチマーク収集ジョブ (Job 0)

    市場指数（S&P500, NASDAQ100）のパフォーマンスを取得しDBに保存。
    Job 1 の前に実行し、1日1回で十分。

    責務:
        - 市場指数の価格履歴取得
        - パフォーマンス計算は RelativeStrengthCalculator に委譲
        - market_benchmarks テーブルへの保存
    """

    name = "collect_benchmarks"

    def __init__(
        self,
        benchmark_repository: BenchmarkRepository,
        financial_gateway: FinancialDataGateway,
        rs_calculator: RelativeStrengthCalculator | None = None,
    ) -> None:
        self._benchmark_repo = benchmark_repository
        self._gateway = financial_gateway
        self._rs_calculator = rs_calculator or RelativeStrengthCalculator()

    async def execute(
        self, input_: CollectBenchmarksInput
    ) -> CollectBenchmarksOutput:
        """ジョブ実行"""
        updated = 0
        benchmarks: dict[str, float] = {}
        errors: list[dict] = []

        for index_symbol in input_.indices:
            try:
                benchmark = await self._process_single_index(index_symbol)
                await self._benchmark_repo.save(benchmark)
                updated += 1
                if benchmark.weighted_performance is not None:
                    benchmarks[index_symbol] = benchmark.weighted_performance
            except Exception as e:
                errors.append({"symbol": index_symbol, "error": str(e)})

        return CollectBenchmarksOutput(
            indices_updated=updated,
            benchmarks=benchmarks,
            errors=errors,
        )

    async def _process_single_index(self, symbol: str) -> MarketBenchmark:
        """単一指数のデータを処理"""
        # 1年分の履歴を取得
        history = await self._gateway.get_price_history(symbol, period="1y")
        if not history or len(history) < TradingDays.YEAR:
            raise ValueError(f"Insufficient history for {symbol}")

        # PriceBar に変換
        price_bars = [PriceBar(close=bar.close) for bar in history]

        # 各期間のパフォーマンスを計算（ドメインサービスに委譲）
        performance_1y = self._rs_calculator.calculate_period_return(
            price_bars, days=TradingDays.YEAR
        )
        performance_9m = self._rs_calculator.calculate_period_return(
            price_bars, days=TradingDays.MONTH_9
        )
        performance_6m = self._rs_calculator.calculate_period_return(
            price_bars, days=TradingDays.MONTH_6
        )
        performance_3m = self._rs_calculator.calculate_period_return(
            price_bars, days=TradingDays.MONTH_3
        )
        performance_1m = self._rs_calculator.calculate_period_return(
            price_bars, days=TradingDays.MONTH_1
        )

        # IBD式加重パフォーマンスを計算
        weighted_performance = self._rs_calculator.calculate_weighted_performance(
            price_bars
        )

        return MarketBenchmark(
            symbol=symbol,
            performance_1y=performance_1y,
            performance_9m=performance_9m,
            performance_6m=performance_6m,
            performance_3m=performance_3m,
            performance_1m=performance_1m,
            weighted_performance=weighted_performance,
            recorded_at=datetime.now(timezone.utc),
        )
