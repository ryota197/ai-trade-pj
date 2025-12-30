"""マーケット状態エンティティ"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.domain.value_objects.market_indicators import MarketIndicators


class MarketCondition(Enum):
    """マーケット状態"""

    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class MarketStatus:
    """
    マーケット状態エンティティ

    市場全体の環境を表すドメインエンティティ。
    CAN-SLIMの「M（Market Direction）」の判断材料を提供する。
    """

    condition: MarketCondition
    confidence: float
    score: int
    indicators: MarketIndicators
    recommendation: str
    analyzed_at: datetime

    def is_favorable_for_entry(self) -> bool:
        """エントリーに適した環境か"""
        return self.condition == MarketCondition.RISK_ON and self.confidence >= 0.6

    def is_unfavorable_for_entry(self) -> bool:
        """エントリーを避けるべき環境か"""
        return self.condition == MarketCondition.RISK_OFF
