"""MarketSnapshot 集約ルート"""

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


@dataclass
class MarketSnapshot:
    """市場状態スナップショット（集約ルート）"""

    id: int
    recorded_at: datetime
    vix: Decimal
    sp500_price: Decimal
    sp500_rsi: Decimal
    sp500_ma200: Decimal
    put_call_ratio: Decimal
    condition: MarketCondition
    score: int  # -5 〜 +5

    def is_above_ma200(self) -> bool:
        """S&P500が200日移動平均線より上か"""
        return self.sp500_price > self.sp500_ma200

    def vix_signal(self) -> Signal:
        """VIXシグナル判定"""
        if self.vix < 15:
            return Signal.BULLISH
        elif self.vix > 25:
            return Signal.BEARISH
        return Signal.NEUTRAL

    def rsi_signal(self) -> Signal:
        """RSIシグナル判定"""
        if self.sp500_rsi > 70:
            return Signal.BEARISH  # 買われすぎ
        elif self.sp500_rsi < 30:
            return Signal.BULLISH  # 売られすぎ
        return Signal.NEUTRAL

    def put_call_signal(self) -> Signal:
        """Put/Call Ratioシグナル判定"""
        if self.put_call_ratio > 1:
            return Signal.BULLISH  # 逆張り指標
        elif self.put_call_ratio < Decimal("0.7"):
            return Signal.BEARISH
        return Signal.NEUTRAL
