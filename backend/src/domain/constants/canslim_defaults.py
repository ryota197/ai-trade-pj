"""CAN-SLIM スクリーニングデフォルト値

CAN-SLIM投資手法における各基準のデフォルト閾値を定義する。
IBD（Investor's Business Daily）の推奨値に基づく。
"""


class CANSLIMDefaults:
    """CAN-SLIMスクリーニングのデフォルト閾値"""

    # ============================================================
    # スコア値（共通）
    # ============================================================
    SCORE_EXCELLENT: int = 100  # 優秀
    SCORE_GOOD: int = 80  # 良好
    SCORE_FAIR: int = 60  # 普通
    SCORE_NEUTRAL: int = 50  # 中立（データなし時のデフォルト）
    SCORE_POOR: int = 40  # やや悪い
    SCORE_BAD: int = 20  # 悪い

    # ============================================================
    # C - Current Quarterly Earnings（四半期EPS成長率）
    # ============================================================
    # スクリーニング用最小値（%）
    MIN_EPS_GROWTH_QUARTERLY: float = 25.0
    # スコアリング用閾値（%）
    EPS_QUARTERLY_EXCELLENT: float = 50.0  # >= 50%: SCORE_EXCELLENT
    # >= MIN_EPS_GROWTH_QUARTERLY: SCORE_GOOD
    # >= 0%: SCORE_NEUTRAL

    # ============================================================
    # A - Annual Earnings（年間EPS成長率）
    # ============================================================
    # スクリーニング用最小値（%）
    MIN_EPS_GROWTH_ANNUAL: float = 25.0
    # スコアリング用閾値（%）
    EPS_ANNUAL_EXCELLENT: float = 50.0  # >= 50%: SCORE_EXCELLENT
    # >= MIN_EPS_GROWTH_ANNUAL: SCORE_GOOD
    # >= 0%: SCORE_NEUTRAL

    # ============================================================
    # N - New High（52週高値からの乖離率）
    # ============================================================
    # スクリーニング用最大乖離率（%）
    MAX_DISTANCE_FROM_52W_HIGH: float = 15.0
    # スコアリング用閾値（%）
    NEW_HIGH_EXCELLENT: float = 0.0  # <= 0%（新高値）: SCORE_EXCELLENT
    NEW_HIGH_GOOD: float = 5.0  # <= 5%: 90点
    # <= MAX_DISTANCE_FROM_52W_HIGH: SCORE_FAIR + 10
    NEW_HIGH_POOR: float = 25.0  # <= 25%: SCORE_POOR

    # ============================================================
    # S - Supply and Demand（出来高倍率）
    # ============================================================
    # スクリーニング用最小倍率
    MIN_VOLUME_RATIO: float = 1.5
    # スコアリング用閾値
    VOLUME_EXCELLENT: float = 2.0  # >= 2.0倍: SCORE_EXCELLENT
    # >= MIN_VOLUME_RATIO: SCORE_GOOD
    VOLUME_FAIR: float = 1.0  # >= 1.0倍: SCORE_FAIR

    # ============================================================
    # L - Leader（RS Rating）
    # ============================================================
    # スクリーニング用最小値（1-99）
    MIN_RS_RATING: int = 80
    # 主導株判定閾値
    LEADER_RS_THRESHOLD: int = 80
    # 出遅れ株判定閾値
    LAGGARD_RS_THRESHOLD: int = 50
    # スコアリング用閾値
    RS_EXCELLENT: int = 90  # >= 90: SCORE_EXCELLENT
    # >= LEADER_RS_THRESHOLD: SCORE_GOOD
    RS_FAIR: int = 70  # >= 70: SCORE_FAIR
    # >= LAGGARD_RS_THRESHOLD: SCORE_POOR

    # ============================================================
    # I - Institutional Sponsorship（機関投資家保有率）
    # ============================================================
    # スコアリング用閾値（%）
    INSTITUTIONAL_EXCELLENT: float = 50.0  # >= 50%: SCORE_EXCELLENT
    INSTITUTIONAL_GOOD: float = 25.0  # >= 25%: SCORE_GOOD
    INSTITUTIONAL_FAIR: float = 10.0  # >= 10%: SCORE_FAIR
    # < 10%: SCORE_POOR

    # ============================================================
    # M - Market Direction
    # ============================================================
    # マーケット状態はMarketCondition enumで判定
    # RISK_ON: SCORE_EXCELLENT, NEUTRAL: SCORE_NEUTRAL, RISK_OFF: SCORE_BAD

    # ============================================================
    # 総合スコア
    # ============================================================
    # CAN-SLIMスコアの最小値（0-100）
    MIN_CANSLIM_SCORE: int = 70

    # ============================================================
    # ページネーション
    # ============================================================
    DEFAULT_LIMIT: int = 20
    MAX_LIMIT: int = 100
    DEFAULT_OFFSET: int = 0

    # ============================================================
    # RS計算 IBD式加重（合計100%）
    # ============================================================
    RS_WEIGHT_3M: float = 0.40  # 3ヶ月: 40%
    RS_WEIGHT_6M: float = 0.20  # 6ヶ月: 20%
    RS_WEIGHT_9M: float = 0.20  # 9ヶ月: 20%
    RS_WEIGHT_12M: float = 0.20  # 12ヶ月: 20%
