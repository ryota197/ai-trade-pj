"""計算指標 エンティティ"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StockMetrics:
    """
    計算指標

    CAN-SLIM関連の指標。Job 1, 2, 3 で段階的に更新。
    対応テーブル: stock_metrics
    """

    symbol: str

    # ファンダメンタル（Job 1 で取得）
    eps_growth_quarterly: float | None  # C - Current Quarterly Earnings
    eps_growth_annual: float | None  # A - Annual Earnings
    institutional_ownership: float | None  # I - Institutional Sponsorship

    # RS関連（Job 1, 2 で段階的に設定）
    relative_strength: float | None  # S&P500比の相対強度（生値）- Job 1
    rs_rating: int | None  # L - Leader (RS Rating: 1-99) - Job 2

    # CAN-SLIMスコア（Job 3 で設定）
    canslim_score: int | None  # 0-100

    calculated_at: datetime
