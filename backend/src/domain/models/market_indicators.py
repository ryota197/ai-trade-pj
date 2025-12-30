"""マーケット指標 Value Object"""

from dataclasses import dataclass
from enum import Enum


class SignalType(Enum):
    """シグナル種別"""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class VixIndicator:
    """VIX指標"""

    value: float

    @property
    def signal(self) -> SignalType:
        """VIXシグナル判定"""
        if self.value < 20:
            return SignalType.BULLISH
        elif self.value > 30:
            return SignalType.BEARISH
        return SignalType.NEUTRAL

    @property
    def score(self) -> int:
        """スコア（±2）"""
        if self.value < 20:
            return 2
        elif self.value > 30:
            return -2
        return 0


@dataclass(frozen=True)
class RsiIndicator:
    """RSI指標"""

    value: float

    @property
    def signal(self) -> SignalType:
        """RSIシグナル判定"""
        if 30 <= self.value <= 70:
            return SignalType.BULLISH
        elif self.value < 30:
            return SignalType.BEARISH  # 売られすぎ
        else:
            return SignalType.BEARISH  # 買われすぎ

    @property
    def score(self) -> int:
        """スコア（±1）"""
        if 30 <= self.value <= 70:
            return 1
        return -1


@dataclass(frozen=True)
class MovingAverageIndicator:
    """移動平均指標"""

    current_price: float
    ma_200: float

    @property
    def is_above_ma(self) -> bool:
        """200MAを上回っているか"""
        return self.current_price > self.ma_200

    @property
    def signal(self) -> SignalType:
        """シグナル判定"""
        return SignalType.BULLISH if self.is_above_ma else SignalType.BEARISH

    @property
    def score(self) -> int:
        """スコア（±1）"""
        return 1 if self.is_above_ma else -1


@dataclass(frozen=True)
class PutCallRatioIndicator:
    """Put/Call Ratio指標"""

    value: float

    @property
    def signal(self) -> SignalType:
        """シグナル判定"""
        if self.value > 1.0:
            return SignalType.BULLISH  # 悲観的 → 逆張りで強気
        elif self.value < 0.7:
            return SignalType.BEARISH  # 楽観的 → 警戒
        return SignalType.NEUTRAL

    @property
    def score(self) -> int:
        """スコア（±1）"""
        if self.value > 1.0:
            return 1
        elif self.value < 0.7:
            return -1
        return 0


@dataclass(frozen=True)
class MarketIndicators:
    """
    マーケット指標 Value Object

    市場環境を判断するための各種指標を集約する。
    """

    vix: VixIndicator
    sp500_rsi: RsiIndicator
    sp500_ma: MovingAverageIndicator
    put_call_ratio: PutCallRatioIndicator

    @property
    def total_score(self) -> int:
        """合計スコア"""
        return (
            self.vix.score
            + self.sp500_rsi.score
            + self.sp500_ma.score
            + self.put_call_ratio.score
        )
