"""データ収集ジョブ (Job 1)"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.application.interfaces.financial_data_gateway import (
    FinancialDataGateway,
    HistoricalBar,
)
from src.domain.entities.stock import Stock
from src.domain.repositories.stock_repository import StockRepository
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
        - relative_strength 計算
        - DBへのUPSERT

    注意:
        - rs_rating, canslim_score は計算しない（後続ジョブに委譲）
        - 各銘柄は独立して処理（1銘柄の失敗が他に影響しない）
    """

    name = "collect_stock_data"

    def __init__(
        self,
        stock_repository: StockRepository,
        financial_gateway: FinancialDataGateway,
    ) -> None:
        self._stock_repo = stock_repository
        self._gateway = financial_gateway

    async def execute(self, input_: CollectInput) -> CollectOutput:
        """ジョブ実行"""
        succeeded = 0
        failed = 0
        errors: list[dict] = []

        # S&P500の履歴を取得（ベンチマーク）
        try:
            sp500_bars = await self._gateway.get_sp500_history(period="1y")
            benchmark_perf = self._calculate_performance(sp500_bars)
        except Exception:
            sp500_bars = []
            benchmark_perf = None

        for symbol in input_.symbols:
            try:
                await self._process_single_symbol(symbol, benchmark_perf)
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
        benchmark_perf: float | None,
    ) -> None:
        """単一銘柄のデータを処理"""
        # 株価データ取得
        quote = await self._gateway.get_quote(symbol)
        if quote is None:
            raise ValueError(f"Quote not found for {symbol}")

        # 財務データ取得
        financials = await self._gateway.get_financial_metrics(symbol)

        # 株価履歴取得（relative_strength計算用）
        history = await self._gateway.get_price_history(symbol, period="1y")

        # relative_strength 計算
        relative_strength = None
        if benchmark_perf and history:
            stock_perf = self._calculate_performance(history)
            if stock_perf is not None and benchmark_perf != 0:
                relative_strength = (stock_perf / benchmark_perf) * 100

        # Stockエンティティを構築して保存
        # 注意: rs_rating, canslim_score は NULL（後続ジョブで計算）
        stock = Stock(
            symbol=symbol,
            name=quote.symbol,  # TODO: 名前を別途取得
            industry=None,  # TODO: 業種を取得
            price=quote.price,
            change_percent=quote.change_percent,
            volume=quote.volume,
            avg_volume_50d=quote.avg_volume,
            market_cap=int(quote.market_cap) if quote.market_cap else None,
            week_52_high=quote.week_52_high,
            week_52_low=quote.week_52_low,
            eps_growth_quarterly=financials.eps_growth_quarterly if financials else None,
            eps_growth_annual=financials.eps_growth_annual if financials else None,
            institutional_ownership=financials.institutional_ownership
            if financials
            else None,
            relative_strength=relative_strength,
            rs_rating=None,  # Job 2 で計算
            canslim_score=None,  # Job 3 で計算
            updated_at=datetime.now(timezone.utc),
        )

        await self._stock_repo.save(stock)

    def _calculate_performance(self, bars: list[HistoricalBar]) -> float | None:
        """
        パフォーマンス（期間リターン）を計算

        Args:
            bars: 株価バーのリスト

        Returns:
            float: パフォーマンス（%）、計算不可の場合はNone
        """
        if not bars or len(bars) < 2:
            return None

        # 最初と最後の終値からリターンを計算
        first_close = bars[0].close
        last_close = bars[-1].close

        if first_close == 0:
            return None

        return ((last_close - first_close) / first_close) * 100
