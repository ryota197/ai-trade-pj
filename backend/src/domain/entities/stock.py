"""Stock エンティティ（正規化構造）"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StockIdentity:
    """
    銘柄マスター

    銘柄の基本情報を表す。更新頻度は稀。
    """

    symbol: str
    name: str | None = None
    industry: str | None = None


@dataclass(frozen=True)
class PriceSnapshot:
    """
    価格スナップショット

    日次の株価・出来高データ。履歴として蓄積可能。
    """

    symbol: str
    price: float | None
    change_percent: float | None
    volume: int | None
    avg_volume_50d: int | None
    market_cap: int | None
    week_52_high: float | None
    week_52_low: float | None
    recorded_at: datetime


@dataclass(frozen=True)
class StockMetrics:
    """
    計算指標

    CAN-SLIM関連の指標。Job 1, 2, 3 で段階的に更新。
    """

    symbol: str

    # ファンダメンタル（Job 1 で取得）
    eps_growth_quarterly: float | None  # C - Current Quarterly Earnings
    eps_growth_annual: float | None  # A - Annual Earnings
    institutional_ownership: float | None  # I - Institutional Sponsorship

    # RS関連（Job 1, 2 で段階的に設定）
    relative_strength: float | None  # S&P500比の相対強度（生値）- Job 1
    rs_rating: int | None  # L - Leader (RS Rating: 1-99) - Job 2

    # CAN-SLIMスコア（Job 3 で設定）
    canslim_score: int | None  # 0-100

    calculated_at: datetime


@dataclass(frozen=True)
class MarketBenchmark:
    """
    市場ベンチマーク

    S&P500やNASDAQ100のパフォーマンス。Job 0 で1日1回更新。
    """

    symbol: str  # "^GSPC" (S&P500), "^NDX" (NASDAQ100)
    performance_1y: float | None
    performance_6m: float | None
    performance_3m: float | None
    performance_1m: float | None
    recorded_at: datetime


@dataclass(frozen=True)
class Stock:
    """
    銘柄集約ルート

    画面表示やAPI応答用に各エンティティを組み合わせる。
    frozen=True で不変オブジェクトとして扱う。
    """

    identity: StockIdentity
    price: PriceSnapshot | None = None
    metrics: StockMetrics | None = None

    @property
    def symbol(self) -> str:
        """ティッカーシンボル"""
        return self.identity.symbol

    @property
    def name(self) -> str | None:
        """企業名"""
        return self.identity.name

    @property
    def industry(self) -> str | None:
        """業種"""
        return self.identity.industry

    @property
    def volume_ratio(self) -> float:
        """S - Supply and Demand: 出来高倍率を計算"""
        if not self.price:
            return 0.0
        if self.price.avg_volume_50d is None or self.price.avg_volume_50d == 0:
            return 0.0
        if self.price.volume is None:
            return 0.0
        return self.price.volume / self.price.avg_volume_50d

    @property
    def distance_from_52w_high(self) -> float:
        """N - New High: 52週高値からの乖離率（%）"""
        if not self.price:
            return 0.0
        if self.price.week_52_high is None or self.price.week_52_high == 0:
            return 0.0
        if self.price.price is None:
            return 0.0
        return (
            (self.price.week_52_high - self.price.price) / self.price.week_52_high
        ) * 100

    @property
    def rs_rating(self) -> int | None:
        """RS Rating (1-99)"""
        if not self.metrics:
            return None
        return self.metrics.rs_rating

    @property
    def canslim_score(self) -> int | None:
        """CAN-SLIMスコア (0-100)"""
        if not self.metrics:
            return None
        return self.metrics.canslim_score

    def is_near_52w_high(self, threshold: float = 15.0) -> bool:
        """52週高値付近にいるか（デフォルト15%以内）"""
        return self.distance_from_52w_high <= threshold

    def has_strong_eps_growth(
        self, quarterly_threshold: float = 25.0, annual_threshold: float = 25.0
    ) -> bool:
        """EPS成長率が基準を満たすか"""
        if not self.metrics:
            return False
        quarterly_ok = (
            self.metrics.eps_growth_quarterly is not None
            and self.metrics.eps_growth_quarterly >= quarterly_threshold
        )
        annual_ok = (
            self.metrics.eps_growth_annual is not None
            and self.metrics.eps_growth_annual >= annual_threshold
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
