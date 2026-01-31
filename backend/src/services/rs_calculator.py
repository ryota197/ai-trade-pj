"""相対強度計算サービス（IBD式）"""

from dataclasses import dataclass
from decimal import Decimal

from src.services.constants import CANSLIMDefaults, TradingDays


@dataclass
class PriceBar:
    """価格バー（計算用）"""

    close: float


class RSCalculator:
    """
    相対強度（Relative Strength）計算サービス（IBD式）

    IBD（Investor's Business Daily）のRS Rating計算方式を採用。
    4期間（3/6/9/12ヶ月）のリターンを加重平均し、
    ベンチマーク（S&P500等）と比較して相対的な強さを数値化する。

    加重: 3ヶ月=40%, 6ヶ月=20%, 9ヶ月=20%, 12ヶ月=20%
    直近3ヶ月を2倍に重み付けすることでモメンタムを重視。

    参考: docs/poc/business-logic/relative-strength.md
    """

    def calculate(
        self,
        stock_bars: list[PriceBar],
        benchmark_bars: list[PriceBar],
    ) -> Decimal | None:
        """個別銘柄の相対強度を計算

        Args:
            stock_bars: 銘柄の価格バーリスト（古い順、最低252営業日必要）
            benchmark_bars: ベンチマークの価格バーリスト（古い順、最低252営業日必要）

        Returns:
            相対強度（Decimal）。100 = ベンチマークと同等。計算不可の場合は None
        """
        stock_weighted = self._calculate_weighted_performance(stock_bars)
        benchmark_weighted = self._calculate_weighted_performance(benchmark_bars)

        if stock_weighted is None or benchmark_weighted is None:
            return None

        rs = self._calculate_relative_strength_from_performances(
            stock_weighted, benchmark_weighted
        )

        if rs is None:
            return None

        return Decimal(str(round(rs, 4)))

    def calculate_all(
        self,
        stocks: dict[str, list[PriceBar]],
        benchmark_bars: list[PriceBar],
    ) -> dict[str, Decimal]:
        """全銘柄の相対強度を一括計算

        Args:
            stocks: 銘柄ごとの価格バーリスト {symbol: [PriceBar, ...]}
            benchmark_bars: ベンチマークの価格バーリスト

        Returns:
            銘柄ごとの相対強度 {symbol: Decimal}
        """
        results: dict[str, Decimal] = {}

        for symbol, stock_bars in stocks.items():
            rs = self.calculate(stock_bars, benchmark_bars)
            if rs is not None:
                results[symbol] = rs

        return results

    # === 内部ヘルパーメソッド ===

    def _calculate_relative_strength_from_performances(
        self,
        stock_weighted_performance: float,
        benchmark_weighted_performance: float,
    ) -> float | None:
        """
        加重パフォーマンス値から相対強度を計算

        計算式: (1 + 銘柄%) / (1 + ベンチマーク%) × 100
        """
        # ベンチマークが-100%（全損）の場合は計算不可
        if benchmark_weighted_performance <= -100:
            return None

        stock_factor = 1 + (stock_weighted_performance / 100)
        benchmark_factor = 1 + (benchmark_weighted_performance / 100)

        return (stock_factor / benchmark_factor) * 100

    def _calculate_weighted_performance(
        self,
        bars: list[PriceBar],
    ) -> float | None:
        """
        IBD式加重パフォーマンスを計算

        計算式: 3ヶ月×40% + 6ヶ月×20% + 9ヶ月×20% + 12ヶ月×20%
        """
        if not bars or len(bars) < TradingDays.YEAR:
            return None

        # 各期間のリターンを計算
        return_3m = self._calculate_period_return(bars, TradingDays.MONTH_3)
        return_6m = self._calculate_period_return(bars, TradingDays.MONTH_6)
        return_9m = self._calculate_period_return(bars, TradingDays.MONTH_9)
        return_12m = self._calculate_period_return(bars, TradingDays.YEAR)

        # いずれかが計算不可なら全体も計算不可
        if any(r is None for r in [return_3m, return_6m, return_9m, return_12m]):
            return None

        # 加重平均を計算
        weighted = (
            return_3m * CANSLIMDefaults.RS_WEIGHT_3M
            + return_6m * CANSLIMDefaults.RS_WEIGHT_6M
            + return_9m * CANSLIMDefaults.RS_WEIGHT_9M
            + return_12m * CANSLIMDefaults.RS_WEIGHT_12M
        )

        return weighted

    def _calculate_period_return(
        self,
        bars: list[PriceBar],
        days: int,
    ) -> float | None:
        """
        期間リターンを計算

        計算式: (現在価格 - N日前価格) / N日前価格 × 100
        """
        if not bars or len(bars) < days:
            return None

        # 期間の開始位置を決定
        start_idx = len(bars) - days
        first_close = bars[start_idx].close
        last_close = bars[-1].close

        if first_close == 0:
            return None

        return ((last_close - first_close) / first_close) * 100
