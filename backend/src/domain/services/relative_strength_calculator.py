"""相対強度計算サービス（IBD式）"""

from dataclasses import dataclass

from src.domain.constants import TradingDays


@dataclass
class PriceBar:
    """価格バー（計算用）"""

    close: float


class RelativeStrengthCalculator:
    """
    相対強度（Relative Strength）計算サービス（IBD式）

    IBD（Investor's Business Daily）のRS Rating計算方式を採用。
    4期間（3/6/9/12ヶ月）のリターンを加重平均し、
    ベンチマーク（S&P500等）と比較して相対的な強さを数値化する。

    加重: 3ヶ月=40%, 6ヶ月=20%, 9ヶ月=20%, 12ヶ月=20%
    直近3ヶ月を2倍に重み付けすることでモメンタムを重視。

    参考: docs/poc/business-logic/relative-strength.md
    """

    # IBD式の加重定数
    WEIGHT_3M = 0.40
    WEIGHT_6M = 0.20
    WEIGHT_9M = 0.20
    WEIGHT_12M = 0.20

    def calculate_relative_strength(
        self,
        stock_bars: list[PriceBar],
        benchmark_weighted_performance: float,
    ) -> float | None:
        """
        IBD式相対強度を計算

        Args:
            stock_bars: 銘柄の価格バーリスト（古い順、最低252営業日必要）
            benchmark_weighted_performance: ベンチマークの加重パフォーマンス（%）

        Returns:
            float: 相対強度（100 = ベンチマークと同等）
                   100超: ベンチマークを上回る
                   100未満: ベンチマークを下回る
                   計算不可の場合は None
        """
        stock_weighted = self.calculate_weighted_performance(stock_bars)
        if stock_weighted is None:
            return None

        return self.calculate_relative_strength_from_performances(
            stock_weighted, benchmark_weighted_performance
        )

    def calculate_relative_strength_from_performances(
        self,
        stock_weighted_performance: float,
        benchmark_weighted_performance: float,
    ) -> float | None:
        """
        加重パフォーマンス値から相対強度を計算

        計算式: (1 + 銘柄%) / (1 + ベンチマーク%) × 100

        Args:
            stock_weighted_performance: 銘柄の加重パフォーマンス（%）
            benchmark_weighted_performance: ベンチマークの加重パフォーマンス（%）

        Returns:
            float: 相対強度（100基準）
        """
        # ベンチマークが-100%（全損）の場合は計算不可
        if benchmark_weighted_performance <= -100:
            return None

        stock_factor = 1 + (stock_weighted_performance / 100)
        benchmark_factor = 1 + (benchmark_weighted_performance / 100)

        return (stock_factor / benchmark_factor) * 100

    def calculate_weighted_performance(
        self,
        bars: list[PriceBar],
    ) -> float | None:
        """
        IBD式加重パフォーマンスを計算

        計算式: 3ヶ月×40% + 6ヶ月×20% + 9ヶ月×20% + 12ヶ月×20%

        Args:
            bars: 価格バーリスト（古い順、最低252営業日必要）

        Returns:
            float: 加重パフォーマンス（%）
        """
        if not bars or len(bars) < TradingDays.YEAR:
            return None

        # 各期間のリターンを計算
        return_3m = self.calculate_period_return(bars, TradingDays.MONTH_3)
        return_6m = self.calculate_period_return(bars, TradingDays.MONTH_6)
        return_9m = self.calculate_period_return(bars, TradingDays.MONTH_9)
        return_12m = self.calculate_period_return(bars, TradingDays.YEAR)

        # いずれかが計算不可なら全体も計算不可
        if any(r is None for r in [return_3m, return_6m, return_9m, return_12m]):
            return None

        # 加重平均を計算
        weighted = (
            return_3m * self.WEIGHT_3M
            + return_6m * self.WEIGHT_6M
            + return_9m * self.WEIGHT_9M
            + return_12m * self.WEIGHT_12M
        )

        return weighted

    def calculate_period_return(
        self,
        bars: list[PriceBar],
        days: int,
    ) -> float | None:
        """
        期間リターンを計算

        計算式: (現在価格 - N日前価格) / N日前価格 × 100

        Args:
            bars: 価格バーリスト（古い順）
            days: 期間（営業日数）

        Returns:
            float: 期間リターン（%）
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

    @staticmethod
    def calculate_percentile_rank(
        value: float,
        all_values: list[float],
    ) -> int:
        """
        パーセンタイルランク（RS Rating）を計算

        全銘柄の相対強度リストから、対象銘柄のパーセンタイル順位を算出する。
        IBDのRS Ratingは1-99のスケールで表される。

        Args:
            value: 対象銘柄の相対強度
            all_values: 全銘柄の相対強度リスト

        Returns:
            int: RS Rating (1-99)
        """
        if not all_values:
            return 50

        sorted_values = sorted(all_values)
        n = len(sorted_values)

        # パーセンタイル計算: value以下の銘柄数 / 全銘柄数 × 100
        rank = sum(1 for v in sorted_values if v <= value)
        percentile = (rank / n) * 100

        # 1-99の範囲に収める
        return max(1, min(99, int(percentile)))

    def calculate_from_prices(
        self,
        stock_prices: list[float],
        benchmark_prices: list[float],
    ) -> tuple[float | None, int]:
        """
        価格リストから相対強度とRS Ratingを計算（レガシー互換）

        注意: RS Ratingは推定値。正確なパーセンタイルには
        calculate_percentile_rank() を使用すること。

        Args:
            stock_prices: 銘柄の価格リスト（古い順、最低252日分）
            benchmark_prices: ベンチマークの価格リスト（古い順、最低252日分）

        Returns:
            tuple[float | None, int]: (相対強度, 推定RS Rating)
        """
        # 価格リストをPriceBarリストに変換
        stock_bars = [PriceBar(close=p) for p in stock_prices]
        benchmark_bars = [PriceBar(close=p) for p in benchmark_prices]

        # 加重パフォーマンスを計算
        stock_weighted = self.calculate_weighted_performance(stock_bars)
        benchmark_weighted = self.calculate_weighted_performance(benchmark_bars)

        if stock_weighted is None or benchmark_weighted is None:
            return None, 50

        # 相対強度を計算
        relative_strength = self.calculate_relative_strength_from_performances(
            stock_weighted, benchmark_weighted
        )

        if relative_strength is None:
            return None, 50

        # RS Ratingを推定（全銘柄リストなしの簡易計算）
        rs_rating = self._estimate_rs_rating(relative_strength)

        return relative_strength, rs_rating

    @staticmethod
    def _estimate_rs_rating(relative_strength: float) -> int:
        """
        相対強度からRS Ratingを推定（全銘柄リストなしの場合）

        注意: これは簡易推定であり、正確なパーセンタイル計算ではない。
        """
        # 相対強度100を基準に線形マッピング
        # RS 80-120 を Rating 30-70 にマッピング
        rs_rating = int(50 + (relative_strength - 100) * 0.5)
        return max(1, min(99, rs_rating))
