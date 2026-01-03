"""CAN-SLIMスコア計算サービス"""

from dataclasses import dataclass

from src.domain.constants import CANSLIMDefaults
from src.domain.models.canslim_stock import CANSLIMStock
from src.domain.models.market_status import MarketCondition


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

    なぜドメインサービスか:
    - 市場状態（M）の判定に外部コンテキスト（Market Context）の情報が必要
    - 評価ルールが複雑で、集約のメソッドとしては肥大化する
    """

    def score(
        self,
        stock: CANSLIMStock,
        market_condition: MarketCondition,
    ) -> CANSLIMScoreResult:
        """CAN-SLIMスコアを計算

        Args:
            stock: スクリーニング対象銘柄
            market_condition: 市場状態（Market Contextから取得）

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

    def _score_current_earnings(self, stock: CANSLIMStock) -> int:
        """C: 当期利益成長率の評価"""
        if stock.eps_growth_quarterly is None:
            return 50  # データなしは中立

        growth = float(stock.eps_growth_quarterly)
        if growth >= 50:
            return 100
        if growth >= CANSLIMDefaults.MIN_EPS_GROWTH_QUARTERLY:
            return 80
        if growth >= 0:
            return 50
        return 20

    def _score_annual_earnings(self, stock: CANSLIMStock) -> int:
        """A: 年間利益成長率の評価"""
        if stock.eps_growth_annual is None:
            return 50  # データなしは中立

        growth = float(stock.eps_growth_annual)
        if growth >= 50:
            return 100
        if growth >= CANSLIMDefaults.MIN_EPS_GROWTH_ANNUAL:
            return 80
        if growth >= 0:
            return 50
        return 20

    def _score_new_high(self, stock: CANSLIMStock) -> int:
        """N: 52週高値近接度の評価"""
        if stock.price is None or stock.week_52_high is None:
            return 50  # データなしは中立

        if stock.week_52_high == 0:
            return 50

        distance = float(
            (stock.week_52_high - stock.price) / stock.week_52_high * 100
        )

        if distance <= 0:  # 新高値
            return 100
        if distance <= 5:
            return 90
        if distance <= CANSLIMDefaults.MAX_DISTANCE_FROM_52W_HIGH:
            return 70
        if distance <= 25:
            return 40
        return 20

    def _score_supply_demand(self, stock: CANSLIMStock) -> int:
        """S: 出来高（需給）の評価"""
        if stock.volume is None or stock.avg_volume_50d is None:
            return 50  # データなしは中立

        if stock.avg_volume_50d == 0:
            return 50

        ratio = stock.volume / stock.avg_volume_50d

        if ratio >= 2.0:
            return 100
        if ratio >= CANSLIMDefaults.MIN_VOLUME_RATIO:
            return 80
        if ratio >= 1.0:
            return 60
        return 40

    def _score_leader(self, stock: CANSLIMStock) -> int:
        """L: RS Ratingに基づく評価"""
        if stock.rs_rating is None:
            return 50  # データなしは中立

        rs = stock.rs_rating
        if rs >= 90:
            return 100
        if rs >= CANSLIMDefaults.LEADER_RS_THRESHOLD:
            return 80
        if rs >= 70:
            return 60
        if rs >= CANSLIMDefaults.LAGGARD_RS_THRESHOLD:
            return 40
        return 20

    def _score_institutional(self, stock: CANSLIMStock) -> int:
        """I: 機関投資家保有率の評価"""
        if stock.institutional_ownership is None:
            return 50  # データなしは中立

        ownership = float(stock.institutional_ownership)
        if ownership >= 50:
            return 100
        if ownership >= 25:
            return 80
        if ownership >= 10:
            return 60
        return 40

    def _score_market(self, market_condition: MarketCondition) -> int:
        """M: 市場状態の評価"""
        if market_condition == MarketCondition.RISK_ON:
            return 100
        if market_condition == MarketCondition.NEUTRAL:
            return 50
        return 20  # RISK_OFF

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
