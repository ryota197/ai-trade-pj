"""マーケット分析サービス"""

from datetime import datetime
from decimal import Decimal

from src.services._lib.types import MarketAnalysisResult, MarketCondition


class MarketAnalyzer:
    """
    マーケット分析サービス

    市場指標からマーケット状態（Risk On/Off/Neutral）を判定する。

    判定ロジック:
    - スコア ≥ 2 → Risk On
    - スコア ≤ -2 → Risk Off
    - その他 → Neutral
    """

    def analyze(
        self,
        vix: Decimal,
        sp500_price: Decimal,
        sp500_rsi: Decimal,
        sp500_ma200: Decimal,
        put_call_ratio: Decimal,
    ) -> MarketAnalysisResult:
        """
        市場指標から総合判定を行い、MarketAnalysisResult を生成

        Args:
            vix: VIX指数
            sp500_price: S&P500現在価格
            sp500_rsi: S&P500のRSI
            sp500_ma200: S&P500の200日移動平均
            put_call_ratio: Put/Call Ratio

        Returns:
            MarketAnalysisResult（condition, score を含む）
        """
        score = 0

        # VIX評価
        if vix < 15:
            score += 1
        elif vix > 25:
            score -= 2

        # RSI評価
        if 30 <= sp500_rsi <= 70:
            score += 1
        elif sp500_rsi > 70:
            score -= 1

        # 200MA評価
        if sp500_price > sp500_ma200:
            score += 2
        else:
            score -= 2

        # Put/Call評価
        if put_call_ratio > 1:
            score += 1
        elif put_call_ratio < Decimal("0.7"):
            score -= 1

        # 総合判定
        if score >= 2:
            condition = MarketCondition.RISK_ON
        elif score <= -2:
            condition = MarketCondition.RISK_OFF
        else:
            condition = MarketCondition.NEUTRAL

        return MarketAnalysisResult(
            recorded_at=datetime.now(),
            vix=vix,
            sp500_price=sp500_price,
            sp500_rsi=sp500_rsi,
            sp500_ma200=sp500_ma200,
            put_call_ratio=put_call_ratio,
            condition=condition,
            score=score,
        )
