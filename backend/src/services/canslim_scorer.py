"""CAN-SLIMスコア計算サービス"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.services._lib.types import MarketCondition
from src.services.constants import CANSLIMDefaults

if TYPE_CHECKING:
    from src.models import CANSLIMStock


@dataclass(frozen=True)
class CANSLIMScoreResult:
    """CAN-SLIMスコア計算結果"""

    total: int
    c: int  # Current Earnings
    a: int  # Annual Earnings
    n: int  # New Product/High
    s: int  # Supply/Demand
    l: int  # Leader
    i: int  # Institutional
    m: int  # Market


class CANSLIMScorer:
    """CAN-SLIMスコア計算サービス

    CAN-SLIM基準に基づいて銘柄を評価し、スコアを算出する。

    スコアリング閾値:
    - すべての閾値は CANSLIMDefaults で一元管理
    - 詳細は src/services/constants/canslim_defaults.py を参照
    """

    def score(
        self,
        stock: "CANSLIMStock",
        market_condition: MarketCondition,
    ) -> CANSLIMScoreResult:
        """CAN-SLIMスコアを計算

        Args:
            stock: スクリーニング対象銘柄（ORM model）
            market_condition: 市場状態

        Returns:
            CAN-SLIMスコア（各項目と総合スコア）
        """
        c_score = self._score_current_earnings(stock)
        a_score = self._score_annual_earnings(stock)
        n_score = self._score_new_high(stock)
        s_score = self._score_supply_demand(stock)
        l_score = self._score_leader(stock)
        i_score = self._score_institutional(stock)
        m_score = self._score_market(market_condition)

        total = self._calculate_total(
            c_score, a_score, n_score, s_score, l_score, i_score, m_score
        )

        return CANSLIMScoreResult(
            total=total,
            c=c_score,
            a=a_score,
            n=n_score,
            s=s_score,
            l=l_score,
            i=i_score,
            m=m_score,
        )

    def _score_current_earnings(self, stock: "CANSLIMStock") -> int:
        """C: 当期利益成長率の評価"""
        if stock.eps_growth_quarterly is None:
            return CANSLIMDefaults.SCORE_NEUTRAL

        growth = float(stock.eps_growth_quarterly)
        if growth >= CANSLIMDefaults.EPS_QUARTERLY_EXCELLENT:
            return CANSLIMDefaults.SCORE_EXCELLENT
        if growth >= CANSLIMDefaults.MIN_EPS_GROWTH_QUARTERLY:
            return CANSLIMDefaults.SCORE_GOOD
        if growth >= 0:
            return CANSLIMDefaults.SCORE_NEUTRAL
        return CANSLIMDefaults.SCORE_BAD

    def _score_annual_earnings(self, stock: "CANSLIMStock") -> int:
        """A: 年間利益成長率の評価"""
        if stock.eps_growth_annual is None:
            return CANSLIMDefaults.SCORE_NEUTRAL

        growth = float(stock.eps_growth_annual)
        if growth >= CANSLIMDefaults.EPS_ANNUAL_EXCELLENT:
            return CANSLIMDefaults.SCORE_EXCELLENT
        if growth >= CANSLIMDefaults.MIN_EPS_GROWTH_ANNUAL:
            return CANSLIMDefaults.SCORE_GOOD
        if growth >= 0:
            return CANSLIMDefaults.SCORE_NEUTRAL
        return CANSLIMDefaults.SCORE_BAD

    def _score_new_high(self, stock: "CANSLIMStock") -> int:
        """N: 52週高値近接度の評価"""
        if stock.price is None or stock.week_52_high is None:
            return CANSLIMDefaults.SCORE_NEUTRAL

        if stock.week_52_high == 0:
            return CANSLIMDefaults.SCORE_NEUTRAL

        distance = float(
            (stock.week_52_high - stock.price) / stock.week_52_high * 100
        )

        if distance <= CANSLIMDefaults.NEW_HIGH_EXCELLENT:
            return CANSLIMDefaults.SCORE_EXCELLENT
        if distance <= CANSLIMDefaults.NEW_HIGH_GOOD:
            return 90  # SCORE_EXCELLENT と SCORE_GOOD の間
        if distance <= CANSLIMDefaults.MAX_DISTANCE_FROM_52W_HIGH:
            return CANSLIMDefaults.SCORE_FAIR + 10  # 70点
        if distance <= CANSLIMDefaults.NEW_HIGH_POOR:
            return CANSLIMDefaults.SCORE_POOR
        return CANSLIMDefaults.SCORE_BAD

    def _score_supply_demand(self, stock: "CANSLIMStock") -> int:
        """S: 出来高（需給）の評価"""
        if stock.volume is None or stock.avg_volume_50d is None:
            return CANSLIMDefaults.SCORE_NEUTRAL

        if stock.avg_volume_50d == 0:
            return CANSLIMDefaults.SCORE_NEUTRAL

        ratio = stock.volume / stock.avg_volume_50d

        if ratio >= CANSLIMDefaults.VOLUME_EXCELLENT:
            return CANSLIMDefaults.SCORE_EXCELLENT
        if ratio >= CANSLIMDefaults.MIN_VOLUME_RATIO:
            return CANSLIMDefaults.SCORE_GOOD
        if ratio >= CANSLIMDefaults.VOLUME_FAIR:
            return CANSLIMDefaults.SCORE_FAIR
        return CANSLIMDefaults.SCORE_POOR

    def _score_leader(self, stock: "CANSLIMStock") -> int:
        """L: RS Ratingに基づく評価"""
        if stock.rs_rating is None:
            return CANSLIMDefaults.SCORE_NEUTRAL

        rs = stock.rs_rating
        if rs >= CANSLIMDefaults.RS_EXCELLENT:
            return CANSLIMDefaults.SCORE_EXCELLENT
        if rs >= CANSLIMDefaults.LEADER_RS_THRESHOLD:
            return CANSLIMDefaults.SCORE_GOOD
        if rs >= CANSLIMDefaults.RS_FAIR:
            return CANSLIMDefaults.SCORE_FAIR
        if rs >= CANSLIMDefaults.LAGGARD_RS_THRESHOLD:
            return CANSLIMDefaults.SCORE_POOR
        return CANSLIMDefaults.SCORE_BAD

    def _score_institutional(self, stock: "CANSLIMStock") -> int:
        """I: 機関投資家保有率の評価"""
        if stock.institutional_ownership is None:
            return CANSLIMDefaults.SCORE_NEUTRAL

        ownership = float(stock.institutional_ownership)
        if ownership >= CANSLIMDefaults.INSTITUTIONAL_EXCELLENT:
            return CANSLIMDefaults.SCORE_EXCELLENT
        if ownership >= CANSLIMDefaults.INSTITUTIONAL_GOOD:
            return CANSLIMDefaults.SCORE_GOOD
        if ownership >= CANSLIMDefaults.INSTITUTIONAL_FAIR:
            return CANSLIMDefaults.SCORE_FAIR
        return CANSLIMDefaults.SCORE_POOR

    def _score_market(self, market_condition: MarketCondition) -> int:
        """M: 市場状態の評価"""
        if market_condition == MarketCondition.RISK_ON:
            return CANSLIMDefaults.SCORE_EXCELLENT
        if market_condition == MarketCondition.NEUTRAL:
            return CANSLIMDefaults.SCORE_NEUTRAL
        return CANSLIMDefaults.SCORE_BAD  # RISK_OFF

    def _calculate_total(
        self,
        c: int,
        a: int,
        n: int,
        s: int,
        l: int,
        i: int,
        m: int,
    ) -> int:
        """総合スコアを計算（均等加重平均）"""
        return (c + a + n + s + l + i + m) // 7
