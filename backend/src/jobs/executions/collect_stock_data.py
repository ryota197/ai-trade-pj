"""データ収集ジョブ (Job 1)"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.application.interfaces.financial_data_gateway import (
    FinancialDataGateway,
)
from src.domain.entities import PriceSnapshot, StockIdentity, StockMetrics
from src.domain.repositories import (
    BenchmarkRepository,
    PriceSnapshotRepository,
    StockIdentityRepository,
    StockMetricsRepository,
)
from src.domain.services import PriceBar, RelativeStrengthCalculator
from src.jobs.lib.base import Job


@dataclass
class CollectInput:
    """データ収集ジョブ入力"""

    symbols: list[str]
    source: str  # "sp500" | "nasdaq100"


@dataclass
class CollectOutput:
    """データ収集ジョブ出力"""

    processed: int
    succeeded: int
    failed: int
    errors: list[dict] = field(default_factory=list)


class CollectStockDataJob(Job[CollectInput, CollectOutput]):
    """
    データ収集ジョブ (Job 1)

    外部APIから株価・財務データを取得し、DBに保存する。

    責務:
        - 株価データ取得（quote, history）
        - 財務データ取得（EPS, institutional ownership等）
        - 3テーブルへのINSERT（stocks, stock_prices, stock_metrics）

    注意:
        - relative_strength 計算は RelativeStrengthCalculator に委譲
        - rs_rating, canslim_score は計算しない（後続ジョブに委譲）
        - 各銘柄は独立して処理（1銘柄の失敗が他に影響しない）
        - ベンチマークは Job 0 で事前に保存されている前提
    """

    name = "collect_stock_data"

    def __init__(
        self,
        stock_identity_repository: StockIdentityRepository,
        price_snapshot_repository: PriceSnapshotRepository,
        stock_metrics_repository: StockMetricsRepository,
        benchmark_repository: BenchmarkRepository,
        financial_gateway: FinancialDataGateway,
        rs_calculator: RelativeStrengthCalculator | None = None,
    ) -> None:
        self._identity_repo = stock_identity_repository
        self._price_repo = price_snapshot_repository
        self._metrics_repo = stock_metrics_repository
        self._benchmark_repo = benchmark_repository
        self._gateway = financial_gateway
        self._rs_calculator = rs_calculator or RelativeStrengthCalculator()

    async def execute(self, input_: CollectInput) -> CollectOutput:
        """ジョブ実行"""
        succeeded = 0
        failed = 0
        errors: list[dict] = []

        # DBからS&P500のIBD式加重パフォーマンスを取得（API呼び出しなし）
        benchmark_weighted_perf = await self._benchmark_repo.get_latest_weighted_performance("^GSPC")
        if benchmark_weighted_perf is None:
            return CollectOutput(
                processed=0,
                succeeded=0,
                failed=len(input_.symbols),
                errors=[
                    {
                        "symbol": "*",
                        "error": "Benchmark not found. Run Job 0 first.",
                    }
                ],
            )

        for symbol in input_.symbols:
            try:
                await self._process_single_symbol(symbol, benchmark_weighted_perf)
                succeeded += 1
            except Exception as e:
                failed += 1
                errors.append({"symbol": symbol, "error": str(e)})

        return CollectOutput(
            processed=len(input_.symbols),
            succeeded=succeeded,
            failed=failed,
            errors=errors,
        )

    async def _process_single_symbol(
        self,
        symbol: str,
        benchmark_weighted_perf: float,
    ) -> None:
        """単一銘柄のデータを処理"""
        now = datetime.now(timezone.utc)

        # 株価データ取得
        quote = await self._gateway.get_quote(symbol)
        if quote is None:
            raise ValueError(f"Quote not found for {symbol}")

        # 財務データ取得
        financials = await self._gateway.get_financial_metrics(symbol)

        # 株価履歴取得（relative_strength計算用）
        history = await self._gateway.get_price_history(symbol, period="1y")

        # IBD式 relative_strength 計算（ドメインサービスに委譲）
        relative_strength = None
        if history:
            price_bars = [PriceBar(close=bar.close) for bar in history]
            relative_strength = self._rs_calculator.calculate_relative_strength(
                stock_bars=price_bars,
                benchmark_weighted_performance=benchmark_weighted_perf,
            )

        # 1. 銘柄マスター保存
        identity = StockIdentity(
            symbol=symbol,
            name=quote.symbol,  # TODO: 名前を別途取得
            industry=None,  # TODO: 業種を取得
        )
        await self._identity_repo.save(identity)

        # 2. 価格スナップショット保存
        price = PriceSnapshot(
            symbol=symbol,
            price=quote.price,
            change_percent=quote.change_percent,
            volume=quote.volume,
            avg_volume_50d=quote.avg_volume,
            market_cap=int(quote.market_cap) if quote.market_cap else None,
            week_52_high=quote.week_52_high,
            week_52_low=quote.week_52_low,
            recorded_at=now,
        )
        await self._price_repo.save(price)

        # 3. 計算指標保存（rs_rating, canslim_score は NULL）
        metrics = StockMetrics(
            symbol=symbol,
            eps_growth_quarterly=(
                financials.eps_growth_quarterly if financials else None
            ),
            eps_growth_annual=financials.eps_growth_annual if financials else None,
            institutional_ownership=(
                financials.institutional_ownership if financials else None
            ),
            relative_strength=relative_strength,
            rs_rating=None,  # Job 2 で計算
            canslim_score=None,  # Job 3 で計算
            calculated_at=now,
        )
        await self._metrics_repo.save(metrics)
