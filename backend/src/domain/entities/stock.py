"""Stock エンティティ"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Stock:
    """
    Stock エンティティ

    CAN-SLIMスクリーニング対象の銘柄を表すドメインエンティティ。
    frozen=True で不変オブジェクトとして扱う。
    """

    symbol: str
    name: str | None
    industry: str | None
    price: float | None
    change_percent: float | None
    volume: int | None
    avg_volume_50d: int | None
    market_cap: int | None
    week_52_high: float | None
    week_52_low: float | None

    # CAN-SLIM指標
    eps_growth_quarterly: float | None  # C - Current Quarterly Earnings
    eps_growth_annual: float | None  # A - Annual Earnings
    institutional_ownership: float | None  # I - Institutional Sponsorship

    # RS関連（Job 1, 2 で段階的に設定）
    relative_strength: float | None  # S&P500比の相対強度（生値）- Job 1で保存
    rs_rating: int | None  # L - Leader (RS Rating: 1-99) - Job 2で更新

    # CAN-SLIMスコア（Job 3 で設定）
    canslim_score: int | None  # 0-100

    # メタデータ
    updated_at: datetime

    @property
    def volume_ratio(self) -> float:
        """S - Supply and Demand: 出来高倍率を計算"""
        if self.avg_volume_50d is None or self.avg_volume_50d == 0:
            return 0.0
        if self.volume is None:
            return 0.0
        return self.volume / self.avg_volume_50d

    @property
    def distance_from_52w_high(self) -> float:
        """N - New High: 52週高値からの乖離率（%）"""
        if self.week_52_high is None or self.week_52_high == 0:
            return 0.0
        if self.price is None:
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
        if self.rs_rating is None:
            return False
        return self.rs_rating >= threshold


@dataclass(frozen=True)
class StockSummary:
    """
    銘柄サマリー

    一覧表示用の簡易情報。
    """

    symbol: str
    name: str | None
    price: float | None
    change_percent: float | None
    rs_rating: int | None
    canslim_score: int | None
