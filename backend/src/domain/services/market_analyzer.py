"""マーケット分析 ドメインサービス"""

from datetime import datetime

from src.domain.models import MarketCondition, MarketStatus
from src.domain.value_objects.market_indicators import MarketIndicators


class MarketAnalyzer:
    """
    マーケット分析ドメインサービス

    市場指標からマーケット状態（Risk On/Off/Neutral）を判定する。

    判定ロジック:
    - スコア ≥ 3 → Risk On
    - スコア ≤ -2 → Risk Off
    - その他 → Neutral
    """

    # 判定閾値
    RISK_ON_THRESHOLD = 3
    RISK_OFF_THRESHOLD = -2

    # 最大スコア（VIX: ±2, RSI: ±1, MA: ±1, P/C: ±1 = ±5）
    MAX_SCORE = 5

    def analyze(self, indicators: MarketIndicators) -> MarketStatus:
        """
        市場指標を分析してマーケット状態を判定

        Args:
            indicators: 市場指標

        Returns:
            MarketStatus: マーケット状態エンティティ
        """
        score = indicators.total_score
        condition = self._determine_condition(score)
        confidence = self._calculate_confidence(score, condition)
        recommendation = self._generate_recommendation(condition, confidence)

        return MarketStatus(
            condition=condition,
            confidence=confidence,
            score=score,
            indicators=indicators,
            recommendation=recommendation,
            analyzed_at=datetime.now(),
        )

    def _determine_condition(self, score: int) -> MarketCondition:
        """スコアからマーケット状態を判定"""
        if score >= self.RISK_ON_THRESHOLD:
            return MarketCondition.RISK_ON
        elif score <= self.RISK_OFF_THRESHOLD:
            return MarketCondition.RISK_OFF
        return MarketCondition.NEUTRAL

    def _calculate_confidence(
        self, score: int, condition: MarketCondition
    ) -> float:
        """
        判定の確信度を計算（0.0 - 1.0）

        スコアの絶対値が大きいほど確信度が高い
        """
        if condition == MarketCondition.NEUTRAL:
            # Neutralの場合は中程度の確信度
            return 0.5

        # Risk On/Off の場合、閾値からの距離で確信度を計算
        if condition == MarketCondition.RISK_ON:
            # スコア3で0.6、スコア5で1.0
            excess = score - self.RISK_ON_THRESHOLD
            confidence = 0.6 + (excess / (self.MAX_SCORE - self.RISK_ON_THRESHOLD)) * 0.4
        else:
            # スコア-2で0.6、スコア-5で1.0
            excess = abs(score - self.RISK_OFF_THRESHOLD)
            confidence = 0.6 + (excess / (self.MAX_SCORE + self.RISK_OFF_THRESHOLD)) * 0.4

        return min(1.0, max(0.0, round(confidence, 2)))

    def _generate_recommendation(
        self, condition: MarketCondition, confidence: float
    ) -> str:
        """推奨アクションを生成"""
        recommendations = {
            MarketCondition.RISK_ON: {
                "high": "市場環境は良好。個別株のエントリーを積極的に検討可。",
                "medium": "市場環境は良好。個別株のエントリー検討可。",
                "low": "市場環境はやや良好。慎重にエントリーを検討。",
            },
            MarketCondition.RISK_OFF: {
                "high": "市場環境は悪化。新規エントリーは避け、ポジション縮小を検討。",
                "medium": "市場環境は不安定。新規エントリーは控えめに。",
                "low": "市場環境はやや不安定。リスク管理を徹底。",
            },
            MarketCondition.NEUTRAL: {
                "high": "市場環境は中立。個別銘柄の選別が重要。",
                "medium": "市場環境は中立。個別銘柄の選別が重要。",
                "low": "市場環境は中立。個別銘柄の選別が重要。",
            },
        }

        if confidence >= 0.8:
            level = "high"
        elif confidence >= 0.6:
            level = "medium"
        else:
            level = "low"

        return recommendations[condition][level]
