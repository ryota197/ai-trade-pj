"""RS Rating（相対強度）計算サービス"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PricePerformance:
    """価格パフォーマンス"""

    period_3m: float  # 3ヶ月リターン（%）
    period_6m: float  # 6ヶ月リターン（%）
    period_9m: float  # 9ヶ月リターン（%）
    period_12m: float  # 12ヶ月リターン（%）

    @property
    def weighted_performance(self) -> float:
        """
        IBD式加重パフォーマンス

        直近のパフォーマンスを重視:
        - 直近3ヶ月: 40%
        - 3-6ヶ月: 20%
        - 6-9ヶ月: 20%
        - 9-12ヶ月: 20%
        """
        return (
            self.period_3m * 0.40
            + self.period_6m * 0.20
            + self.period_9m * 0.20
            + self.period_12m * 0.20
        )


@dataclass(frozen=True)
class RSRatingResult:
    """RS Rating計算結果"""

    symbol: str
    rs_rating: int  # 1-99
    relative_strength: float  # S&P500比の相対強度
    stock_performance: PricePerformance
    benchmark_performance: PricePerformance
    calculated_at: datetime


class RSRatingCalculator:
    """
    RS Rating 計算サービス

    William O'Neil / IBD の Relative Strength Rating を計算する。
    RS Rating は、株式の価格パフォーマンスを S&P 500 に対して比較し、
    全銘柄中のパーセンタイルランキング（1-99）として表す。
    """

    @staticmethod
    def calculate_performance(
        prices: list[float],
    ) -> PricePerformance | None:
        """
        価格データからパフォーマンスを計算

        Args:
            prices: 価格リスト（古い順、最低252日分必要）

        Returns:
            PricePerformance: 各期間のリターン
        """
        if len(prices) < 252:  # 約1年の取引日数
            return None

        current_price = prices[-1]

        # 各期間の開始インデックス（取引日ベース）
        # 3ヶ月 ≈ 63取引日, 6ヶ月 ≈ 126取引日, 9ヶ月 ≈ 189取引日, 12ヶ月 ≈ 252取引日
        idx_3m = max(0, len(prices) - 63)
        idx_6m = max(0, len(prices) - 126)
        idx_9m = max(0, len(prices) - 189)
        idx_12m = max(0, len(prices) - 252)

        price_3m = prices[idx_3m]
        price_6m = prices[idx_6m]
        price_9m = prices[idx_9m]
        price_12m = prices[idx_12m]

        def calc_return(start: float, end: float) -> float:
            if start == 0:
                return 0.0
            return ((end - start) / start) * 100

        return PricePerformance(
            period_3m=calc_return(price_3m, current_price),
            period_6m=calc_return(price_6m, current_price),
            period_9m=calc_return(price_9m, current_price),
            period_12m=calc_return(price_12m, current_price),
        )

    @staticmethod
    def calculate_relative_strength(
        stock_performance: PricePerformance,
        benchmark_performance: PricePerformance,
    ) -> float:
        """
        S&P500に対する相対強度を計算

        Args:
            stock_performance: 株式のパフォーマンス
            benchmark_performance: ベンチマーク（S&P500）のパフォーマンス

        Returns:
            float: 相対強度（100 = S&P500と同等）
        """
        stock_weighted = stock_performance.weighted_performance
        benchmark_weighted = benchmark_performance.weighted_performance

        # ベンチマークがマイナスの場合の処理
        if benchmark_weighted <= -100:
            benchmark_weighted = -99  # 極端な値を防ぐ

        # 相対強度 = (1 + stock) / (1 + benchmark) * 100
        relative = (
            (1 + stock_weighted / 100) / (1 + benchmark_weighted / 100)
        ) * 100

        return relative

    @staticmethod
    def calculate_rs_rating(
        relative_strength: float,
        all_relative_strengths: list[float],
    ) -> int:
        """
        相対強度から RS Rating（パーセンタイルランク）を計算

        Args:
            relative_strength: 対象銘柄の相対強度
            all_relative_strengths: 全銘柄の相対強度リスト

        Returns:
            int: RS Rating (1-99)
        """
        if not all_relative_strengths:
            return 50

        sorted_strengths = sorted(all_relative_strengths)
        n = len(sorted_strengths)

        # パーセンタイル計算
        rank = sum(1 for rs in sorted_strengths if rs <= relative_strength)
        percentile = (rank / n) * 100

        # 1-99の範囲に収める
        return max(1, min(99, int(percentile)))

    def calculate_single(
        self,
        symbol: str,
        stock_prices: list[float],
        benchmark_prices: list[float],
        all_relative_strengths: list[float] | None = None,
    ) -> RSRatingResult | None:
        """
        単一銘柄のRS Ratingを計算

        Args:
            symbol: ティッカーシンボル
            stock_prices: 株価リスト（古い順、最低252日分）
            benchmark_prices: ベンチマーク価格リスト（古い順、最低252日分）
            all_relative_strengths: 全銘柄の相対強度（ランキング計算用）

        Returns:
            RSRatingResult: RS Rating計算結果
        """
        stock_perf = self.calculate_performance(stock_prices)
        benchmark_perf = self.calculate_performance(benchmark_prices)

        if stock_perf is None or benchmark_perf is None:
            return None

        relative_strength = self.calculate_relative_strength(
            stock_perf, benchmark_perf
        )

        # 全銘柄データがない場合は、相対強度から簡易的にRS Ratingを推定
        if all_relative_strengths is None:
            # 相対強度100を基準に線形マッピング
            # RS 80-120 を Rating 30-70 にマッピング
            rs_rating = int(50 + (relative_strength - 100) * 0.5)
            rs_rating = max(1, min(99, rs_rating))
        else:
            rs_rating = self.calculate_rs_rating(
                relative_strength, all_relative_strengths
            )

        return RSRatingResult(
            symbol=symbol,
            rs_rating=rs_rating,
            relative_strength=relative_strength,
            stock_performance=stock_perf,
            benchmark_performance=benchmark_perf,
            calculated_at=datetime.now(),
        )

    def calculate_batch(
        self,
        symbols: list[str],
        stock_prices_map: dict[str, list[float]],
        benchmark_prices: list[float],
    ) -> list[RSRatingResult]:
        """
        複数銘柄のRS Ratingを一括計算

        Args:
            symbols: ティッカーシンボルのリスト
            stock_prices_map: シンボル -> 株価リストのマップ
            benchmark_prices: ベンチマーク価格リスト（古い順、最低252日分）

        Returns:
            list[RSRatingResult]: RS Rating計算結果のリスト
        """
        benchmark_perf = self.calculate_performance(benchmark_prices)
        if benchmark_perf is None:
            return []

        # まず全銘柄の相対強度を計算
        relative_strengths: dict[str, float] = {}
        stock_performances: dict[str, PricePerformance] = {}

        for symbol in symbols:
            prices = stock_prices_map.get(symbol, [])

            stock_perf = self.calculate_performance(prices)
            if stock_perf is not None:
                rs = self.calculate_relative_strength(stock_perf, benchmark_perf)
                relative_strengths[symbol] = rs
                stock_performances[symbol] = stock_perf

        all_rs_values = list(relative_strengths.values())

        # RS Ratingを計算
        results: list[RSRatingResult] = []
        for symbol, rs in relative_strengths.items():
            rs_rating = self.calculate_rs_rating(rs, all_rs_values)
            results.append(
                RSRatingResult(
                    symbol=symbol,
                    rs_rating=rs_rating,
                    relative_strength=rs,
                    stock_performance=stock_performances[symbol],
                    benchmark_performance=benchmark_perf,
                    calculated_at=datetime.now(),
                )
            )

        return results
