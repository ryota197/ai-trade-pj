"""ScreeningCriteria - スクリーニング条件（値オブジェクト）"""

from dataclasses import dataclass, field
from decimal import Decimal

from src.domain.constants import CANSLIMDefaults


@dataclass(frozen=True)
class ScreeningCriteria:
    """スクリーニング条件（値オブジェクト）

    CAN-SLIM銘柄をフィルタリングするための条件を定義する。
    frozen=True により不変性を保証。
    デフォルト値は CANSLIMDefaults から取得。

    Attributes:
        min_rs_rating: 最低RS Rating
        min_canslim_score: 最低CAN-SLIMスコア
        min_eps_growth_quarterly: 最低四半期EPS成長率（%）
        min_eps_growth_annual: 最低年間EPS成長率（%）
        max_distance_from_high: 52週高値乖離率上限（%）
        min_volume_ratio: 最低出来高倍率
    """

    min_rs_rating: int = CANSLIMDefaults.MIN_RS_RATING
    min_canslim_score: int = CANSLIMDefaults.MIN_CANSLIM_SCORE
    min_eps_growth_quarterly: Decimal = field(
        default_factory=lambda: Decimal(str(CANSLIMDefaults.MIN_EPS_GROWTH_QUARTERLY))
    )
    min_eps_growth_annual: Decimal = field(
        default_factory=lambda: Decimal(str(CANSLIMDefaults.MIN_EPS_GROWTH_ANNUAL))
    )
    max_distance_from_high: Decimal = field(
        default_factory=lambda: Decimal(str(CANSLIMDefaults.MAX_DISTANCE_FROM_52W_HIGH))
    )
    min_volume_ratio: Decimal = field(
        default_factory=lambda: Decimal(str(CANSLIMDefaults.MIN_VOLUME_RATIO))
    )

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if not (1 <= self.min_rs_rating <= 99):
            raise ValueError("min_rs_rating must be between 1 and 99")
        if not (0 <= self.min_canslim_score <= 100):
            raise ValueError("min_canslim_score must be between 0 and 100")
        if self.max_distance_from_high < 0:
            raise ValueError("max_distance_from_high must be non-negative")
        if self.min_volume_ratio < 0:
            raise ValueError("min_volume_ratio must be non-negative")
