"""データ収集ジョブ (Job 1)"""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

from src.adapters.yfinance import YFinanceGateway
from src.models import CANSLIMStock
from src.queries import CANSLIMStockQuery
from src.services import RSCalculator
from src.services.rs_calculator import PriceBar
from src.jobs.executions.base import Job


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
        - canslim_stocks テーブルへのUPSERT
        - relative_strength の計算

    注意:
        - rs_rating, canslim_score は計算しない（後続ジョブに委譲）
        - 各銘柄は独立して処理（1銘柄の失敗が他に影響しない）
    """

    name = "collect_stock_data"

    def __init__(
        self,
        stock_query: CANSLIMStockQuery,
        financial_gateway: YFinanceGateway,
        rs_calculator: RSCalculator | None = None,
    ) -> None:
        self._stock_query = stock_query
        self._gateway = financial_gateway
        self._rs_calculator = rs_calculator or RSCalculator()

    async def execute(self, input_: CollectInput) -> CollectOutput:
        """ジョブ実行"""
        succeeded = 0
        failed = 0
        errors: list[dict] = []
        target_date = date.today()

        # S&P500の履歴を取得（RS計算用ベンチマーク）
        benchmark_bars: list[PriceBar] = []
        try:
            sp500_history = await self._gateway.get_sp500_history(period="1y")
            benchmark_bars = [PriceBar(close=bar.close) for bar in sp500_history]
        except Exception as e:
            # ベンチマーク取得失敗は警告のみ（RS計算がスキップされる）
            errors.append({"symbol": "^GSPC", "error": f"Benchmark fetch failed: {e}"})

        for symbol in input_.symbols:
            try:
                await self._process_single_symbol(symbol, target_date, benchmark_bars)
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
        target_date: date,
        benchmark_bars: list[PriceBar],
    ) -> None:
        """単一銘柄のデータを処理"""
        # 株価データ取得
        quote = await self._gateway.get_quote(symbol)
        if quote is None:
            raise ValueError(f"Quote not found for {symbol}")

        # 財務データ取得
        financials = await self._gateway.get_financial_metrics(symbol)

        # 株価履歴取得（RS計算用）
        stock_bars: list[PriceBar] = []
        try:
            history = await self._gateway.get_price_history(symbol, period="1y")
            stock_bars = [PriceBar(close=bar.close) for bar in history]
        except Exception:
            pass

        # 相対強度を計算
        relative_strength: Decimal | None = None
        if stock_bars and benchmark_bars:
            relative_strength = self._rs_calculator.calculate(stock_bars, benchmark_bars)

        # CANSLIMStockを構築して保存
        stock = CANSLIMStock(
            symbol=symbol.upper(),
            date=target_date,
            name=symbol,  # TODO: 名前取得
            industry=None,
            price=Decimal(str(quote.price)),
            change_percent=Decimal(str(quote.change_percent)),
            volume=quote.volume,
            avg_volume_50d=quote.avg_volume,
            market_cap=quote.market_cap,
            week_52_high=(
                Decimal(str(quote.week_52_high)) if quote.week_52_high else None
            ),
            week_52_low=(
                Decimal(str(quote.week_52_low)) if quote.week_52_low else None
            ),
            eps_growth_quarterly=(
                Decimal(str(financials.eps_growth_quarterly))
                if financials and financials.eps_growth_quarterly
                else None
            ),
            eps_growth_annual=(
                Decimal(str(financials.eps_growth_annual))
                if financials and financials.eps_growth_annual
                else None
            ),
            institutional_ownership=(
                Decimal(str(financials.institutional_ownership))
                if financials and financials.institutional_ownership
                else None
            ),
            relative_strength=relative_strength,
            # RS Rating と CAN-SLIM スコアは Job 2, Job 3 で計算
            rs_rating=None,
            canslim_score=None,
            updated_at=datetime.now(timezone.utc),
        )

        self._stock_query.save(stock)
