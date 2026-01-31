"""Service types - enums and result dataclasses"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class MarketCondition(Enum):
    """マーケット状態"""

    RISK_ON = "risk_on"
    NEUTRAL = "neutral"
    RISK_OFF = "risk_off"


class Signal(Enum):
    """シグナル種別"""

    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"


@dataclass(frozen=True)
class MarketAnalysisResult:
    """マーケット分析結果

    MarketAnalyzer の出力として使用。
    ORM MarketSnapshot への変換は呼び出し側で行う。
    """

    recorded_at: datetime
    vix: Decimal
    sp500_price: Decimal
    sp500_rsi: Decimal
    sp500_ma200: Decimal
    put_call_ratio: Decimal
    condition: MarketCondition
    score: int  # -5 〜 +5
