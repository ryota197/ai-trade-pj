"""マーケット関連 DTO"""

from dataclasses import dataclass
from datetime import datetime

from src.domain.models import MarketCondition


@dataclass(frozen=True)
class MarketIndicatorsOutput:
    """マーケット指標 出力DTO"""

    vix: float
    vix_signal: str
    sp500_price: float
    sp500_rsi: float
    sp500_rsi_signal: str
    sp500_ma200: float
    sp500_above_ma200: bool
    put_call_ratio: float
    put_call_signal: str
    retrieved_at: datetime


@dataclass(frozen=True)
class MarketStatusOutput:
    """マーケット状態 出力DTO"""

    condition: MarketCondition
    condition_label: str
    confidence: float
    score: int
    recommendation: str
    indicators: MarketIndicatorsOutput
    analyzed_at: datetime

    @property
    def is_favorable(self) -> bool:
        """エントリーに適した環境か"""
        return self.condition == MarketCondition.RISK_ON and self.confidence >= 0.6
