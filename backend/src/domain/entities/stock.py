"""Stock エンティティ"""

from dataclasses import dataclass
from datetime import datetime

from src.domain.value_objects.canslim_score import CANSLIMScore


@dataclass(frozen=True)
class Stock:
    """
    Stock エンティティ

    CAN-SLIMスクリーニング対象の銘柄を表すドメインエンティティ。
    frozen=True で不変オブジェクトとして扱う。
    """

    symbol: str
    name: str
    price: float
    change_percent: float
    volume: int
    avg_volume: int
    market_cap: float | None
    pe_ratio: float | None
    week_52_high: float
    week_52_low: float
    eps_growth_quarterly: float | None  # C - Current Quarterly Earnings
    eps_growth_annual: float | None  # A - Annual Earnings
    rs_rating: int  # L - Leader (Relative Strength Rating: 1-99)
    institutional_ownership: float | None  # I - Institutional Sponsorship
    canslim_score: CANSLIMScore | None
    updated_at: datetime

    @property
    def volume_ratio(self) -> float:
        """S - Supply and Demand: 出来高倍率を計算"""
        if self.avg_volume == 0:
            return 0.0
        return self.volume / self.avg_volume

    @property
    def distance_from_52w_high(self) -> float:
        """N - New High: 52週高値からの乖離率（%）"""
        if self.week_52_high == 0:
            return 0.0
        return ((self.week_52_high - self.price) / self.week_52_high) * 100

    def is_near_52w_high(self, threshold: float = 15.0) -> bool:
        """52週高値付近にいるか（デフォルト15%以内）"""
        return self.distance_from_52w_high <= threshold

    def has_strong_eps_growth(
        self, quarterly_threshold: float = 25.0, annual_threshold: float = 25.0
    ) -> bool:
        """EPS成長率が基準を満たすか"""
        quarterly_ok = (
            self.eps_growth_quarterly is not None
            and self.eps_growth_quarterly >= quarterly_threshold
        )
        annual_ok = (
            self.eps_growth_annual is not None
            and self.eps_growth_annual >= annual_threshold
        )
        return quarterly_ok and annual_ok

    def has_strong_volume(self, threshold: float = 1.5) -> bool:
        """出来高が基準を超えているか"""
        return self.volume_ratio >= threshold

    def is_leader(self, threshold: int = 80) -> bool:
        """RS Ratingがリーダー水準か"""
        return self.rs_rating >= threshold


@dataclass(frozen=True)
class StockSummary:
    """
    銘柄サマリー

    一覧表示用の簡易情報。
    """

    symbol: str
    name: str
    price: float
    change_percent: float
    rs_rating: int
    canslim_total_score: int
