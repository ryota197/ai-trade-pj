"""CAN-SLIM スクリーニング閾値定数

CAN-SLIM投資手法における各基準のデフォルト閾値を定義する。
IBD（Investor's Business Daily）の推奨値に基づく。
"""


class CANSLIMThresholds:
    """CAN-SLIMスクリーニングのデフォルト閾値"""

    # C - Current Quarterly Earnings
    # 四半期EPS成長率の最小値（%）
    MIN_EPS_GROWTH_QUARTERLY: float = 25.0

    # A - Annual Earnings
    # 年間EPS成長率の最小値（%）
    MIN_EPS_GROWTH_ANNUAL: float = 25.0

    # N - New High
    # 52週高値からの最大乖離率（%）
    MAX_DISTANCE_FROM_52W_HIGH: float = 15.0

    # S - Supply and Demand
    # 平均出来高に対する最小出来高倍率
    MIN_VOLUME_RATIO: float = 1.5

    # L - Leader
    # 最小RS Rating（1-99）
    MIN_RS_RATING: int = 80

    # I - Institutional Sponsorship
    # 機関投資家保有率（参考値として表示のみ、フィルターには使用しない）

    # M - Market Direction
    # マーケット状態はPhase 2のMarket Statusで判定

    # 総合スコア
    # CAN-SLIMスコアの最小値（0-100）
    MIN_CANSLIM_SCORE: int = 70

    # ページネーション
    DEFAULT_LIMIT: int = 20
    MAX_LIMIT: int = 100
    DEFAULT_OFFSET: int = 0
