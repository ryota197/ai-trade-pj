"""CANSLIMStock - CAN-SLIM分析銘柄（集約ルート）"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from src.domain.constants import CANSLIMDefaults

if TYPE_CHECKING:
    from src.domain.models.screening_criteria import ScreeningCriteria


@dataclass
class CANSLIMStock:
    """CAN-SLIM分析銘柄（集約ルート・フラット構造）

    設計方針:
    - フラット構造: PriceSnapshot, StockRating などの値オブジェクトを使わず、
      フラットにフィールドを持つ
    - NULL許容不変条件: 段階的計算に対応するため、計算途中のフィールドは NULL を許容
    - 計算フェーズ: Job 1 → Job 2 → Job 3 の順に段階的に計算・更新

    計算フェーズと更新順序:
        Job 1: 価格データ取得
            → price, change_percent, volume, avg_volume_50d, market_cap,
              week_52_high, week_52_low, eps_growth_quarterly, eps_growth_annual,
              institutional_ownership, relative_strength

        Job 2: RS Rating 計算（全銘柄の relative_strength が必要）
            → rs_rating

        Job 3: CAN-SLIM スコア計算（rs_rating が必要）
            → canslim_score, score_c, score_a, score_n, score_s, score_l, score_i, score_m
    """

    # === 識別子（必須） ===
    symbol: str
    date: date

    # === 銘柄情報 ===
    name: str | None = None
    industry: str | None = None

    # === 価格データ（Job 1 で更新） ===
    price: Decimal | None = None
    change_percent: Decimal | None = None
    volume: int | None = None
    avg_volume_50d: int | None = None
    market_cap: int | None = None
    week_52_high: Decimal | None = None
    week_52_low: Decimal | None = None

    # === 財務データ（Job 1 で更新） ===
    eps_growth_quarterly: Decimal | None = None
    eps_growth_annual: Decimal | None = None
    institutional_ownership: Decimal | None = None

    # === 相対強度（Job 1 で更新） ===
    relative_strength: Decimal | None = None

    # === RS Rating（Job 2 で更新、全銘柄のrelative_strengthが必要） ===
    rs_rating: int | None = None

    # === CAN-SLIM スコア（Job 3 で更新） ===
    canslim_score: int | None = None
    score_c: int | None = None
    score_a: int | None = None
    score_n: int | None = None
    score_s: int | None = None
    score_l: int | None = None
    score_i: int | None = None
    score_m: int | None = None

    # === メタデータ ===
    updated_at: datetime | None = field(default=None)

    # === 不変条件（Invariants） ===
    def __post_init__(self) -> None:
        """不変条件の検証"""
        if not self.symbol:
            raise ValueError("symbol is required")
        if self.rs_rating is not None and not (1 <= self.rs_rating <= 99):
            raise ValueError("rs_rating must be between 1 and 99")
        if self.canslim_score is not None and not (0 <= self.canslim_score <= 100):
            raise ValueError("canslim_score must be between 0 and 100")

    # === ドメインロジック ===
    def meets_filter(self, criteria: ScreeningCriteria) -> bool:
        """スクリーニング条件を満たすか判定

        Args:
            criteria: スクリーニング条件

        Returns:
            条件を満たす場合 True
        """
        if self.rs_rating is None:
            return False
        if self.rs_rating < criteria.min_rs_rating:
            return False
        if self.canslim_score is None:
            return False
        if self.canslim_score < criteria.min_canslim_score:
            return False
        return True

    def distance_from_52week_high(self) -> Decimal | None:
        """52週高値からの乖離率（%）

        Returns:
            乖離率（%）。データ不足の場合は None
        """
        if self.week_52_high is None or self.price is None:
            return None
        if self.week_52_high == 0:
            return Decimal("0")
        return (self.week_52_high - self.price) / self.week_52_high * 100

    def volume_ratio(self) -> Decimal | None:
        """出来高倍率（当日 / 50日平均）

        Returns:
            出来高倍率。データ不足の場合は None
        """
        if self.volume is None or self.avg_volume_50d is None:
            return None
        if self.avg_volume_50d == 0:
            return Decimal("0")
        return Decimal(self.volume) / Decimal(self.avg_volume_50d)

    def is_leader(self) -> bool:
        """主導株か（RS Rating が閾値以上）

        Returns:
            RS Rating が LEADER_RS_THRESHOLD 以上の場合 True
        """
        return (
            self.rs_rating is not None
            and self.rs_rating >= CANSLIMDefaults.LEADER_RS_THRESHOLD
        )

    def is_calculation_complete(self) -> bool:
        """全計算フェーズが完了しているか

        Returns:
            relative_strength, rs_rating, canslim_score がすべて設定済みの場合 True
        """
        return (
            self.relative_strength is not None
            and self.rs_rating is not None
            and self.canslim_score is not None
        )
