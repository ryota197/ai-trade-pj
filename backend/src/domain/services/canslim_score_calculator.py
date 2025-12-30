"""CAN-SLIMスコア計算サービス"""

from dataclasses import dataclass

from src.domain.models import CANSLIMScoreThresholds, CANSLIMWeights


@dataclass(frozen=True)
class CANSLIMInput:
    """CAN-SLIMスコア計算入力"""

    eps_growth_quarterly: float | None  # C: 四半期EPS成長率 (%)
    eps_growth_annual: float | None  # A: 年間EPS成長率 (%)
    price: float | None  # N: 現在価格
    week_52_high: float | None  # N: 52週高値
    volume: int | None  # S: 当日出来高
    avg_volume_50d: int | None  # S: 50日平均出来高
    rs_rating: int | None  # L: RS Rating (1-99)
    institutional_ownership: float | None  # I: 機関投資家保有率 (%)


class CANSLIMScoreCalculator:
    """
    CAN-SLIMスコア計算サービス

    CAN-SLIMの各要素を評価し、総合スコア (0-100) を計算する。

    Note:
        - 各要素は0-100の範囲で正規化
        - データ欠損時はその要素を評価から除外し、残りで正規化
        - M (Market) は個別銘柄評価のためスキップ
    """

    def __init__(
        self,
        weights: CANSLIMWeights | None = None,
        thresholds: CANSLIMScoreThresholds | None = None,
    ) -> None:
        self._weights = weights or CANSLIMWeights()
        self._thresholds = thresholds or CANSLIMScoreThresholds()

    def calculate(self, input_data: CANSLIMInput) -> int:
        """
        CAN-SLIMスコアを計算

        Args:
            input_data: CAN-SLIM計算入力データ

        Returns:
            int: CAN-SLIMスコア (0-100)
        """
        scores: list[tuple[float, float]] = []  # (score, weight)
        w = self._weights

        # C: Current Quarterly Earnings
        c_score = self._calculate_eps_score(input_data.eps_growth_quarterly)
        if c_score is not None:
            scores.append((c_score, w.c))

        # A: Annual Earnings
        a_score = self._calculate_eps_score(input_data.eps_growth_annual)
        if a_score is not None:
            scores.append((a_score, w.a))

        # N: New High
        n_score = self._calculate_new_high_score(
            input_data.price, input_data.week_52_high
        )
        if n_score is not None:
            scores.append((n_score, w.n))

        # S: Supply/Demand
        s_score = self._calculate_volume_score(
            input_data.volume, input_data.avg_volume_50d
        )
        if s_score is not None:
            scores.append((s_score, w.s))

        # L: Leader
        l_score = self._calculate_rs_score(input_data.rs_rating)
        if l_score is not None:
            scores.append((l_score, w.l))

        # I: Institutional
        i_score = self._calculate_institutional_score(
            input_data.institutional_ownership
        )
        if i_score is not None:
            scores.append((i_score, w.i))

        # 加重平均計算
        if not scores:
            return 0

        total_weight = sum(weight for _, weight in scores)
        if total_weight == 0:
            return 0

        # 重み正規化して加重平均を計算
        weighted_sum = sum(
            score * (weight / total_weight) for score, weight in scores
        )

        return int(round(weighted_sum))

    def _calculate_eps_score(self, growth: float | None) -> float | None:
        """EPS成長率スコア計算 (C, A共通)"""
        if growth is None:
            return None

        t = self._thresholds

        if growth < 0:
            return 0.0

        if growth >= t.max_eps_growth:
            return 100.0

        if growth < t.min_eps_growth:
            return (growth / t.min_eps_growth) * 50.0

        ratio = (growth - t.min_eps_growth) / (t.max_eps_growth - t.min_eps_growth)
        return 50.0 + ratio * 50.0

    def _calculate_new_high_score(
        self, price: float | None, week_52_high: float | None
    ) -> float | None:
        """52週高値近接度スコア計算 (N)"""
        if price is None or week_52_high is None or week_52_high <= 0:
            return None

        t = self._thresholds
        distance_percent = ((week_52_high - price) / week_52_high) * 100

        if distance_percent <= 0:
            return 100.0

        if distance_percent > t.max_distance_from_high:
            return 0.0

        return 100.0 * (1 - distance_percent / t.max_distance_from_high)

    def _calculate_volume_score(
        self, volume: int | None, avg_volume: int | None
    ) -> float | None:
        """出来高比率スコア計算 (S)"""
        if volume is None or avg_volume is None or avg_volume <= 0:
            return None

        t = self._thresholds
        ratio = volume / avg_volume

        if ratio < t.min_volume_ratio:
            return ratio * 50.0

        if ratio >= t.max_volume_ratio:
            return 100.0

        normalized = (ratio - t.min_volume_ratio) / (
            t.max_volume_ratio - t.min_volume_ratio
        )
        return 50.0 + normalized * 50.0

    def _calculate_rs_score(self, rs_rating: int | None) -> float | None:
        """RS Ratingスコア計算 (L)"""
        if rs_rating is None:
            return None

        t = self._thresholds

        if rs_rating < t.min_rs_rating:
            return (rs_rating / t.min_rs_rating) * 50.0

        normalized = (rs_rating - t.min_rs_rating) / (
            t.max_rs_rating - t.min_rs_rating
        )
        return 50.0 + normalized * 50.0

    def _calculate_institutional_score(
        self, ownership: float | None
    ) -> float | None:
        """機関投資家保有率スコア計算 (I)"""
        if ownership is None:
            return None

        t = self._thresholds

        if ownership < t.min_inst_ownership:
            return (ownership / t.min_inst_ownership) * 50.0

        if ownership >= t.max_inst_ownership:
            return 100.0

        normalized = (ownership - t.min_inst_ownership) / (
            t.max_inst_ownership - t.min_inst_ownership
        )
        return 50.0 + normalized * 50.0
