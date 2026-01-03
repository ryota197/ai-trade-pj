"""マーケット関連 DTO"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from src.domain.models.market_snapshot import MarketCondition


@dataclass(frozen=True)
class MarketIndicatorsOutput:
    """マーケット指標 出力DTO"""

    vix: Decimal
    vix_signal: str
    sp500_price: Decimal
    sp500_rsi: Decimal
    sp500_rsi_signal: str
    sp500_ma200: Decimal
    sp500_above_ma200: bool
    put_call_ratio: Decimal
    put_call_signal: str
    retrieved_at: datetime


@dataclass(frozen=True)
class MarketStatusOutput:
    """マーケット状態 出力DTO"""

    condition: MarketCondition
    condition_label: str
    score: int
    indicators: MarketIndicatorsOutput
    recorded_at: datetime

    @property
    def is_favorable(self) -> bool:
        """エントリーに適した環境か"""
        return self.condition == MarketCondition.RISK_ON and self.score >= 2
