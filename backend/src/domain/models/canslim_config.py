"""CAN-SLIM設定 Value Objects"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CANSLIMWeights:
    """CAN-SLIM各要素の重み"""

    c: float = 0.20  # Current quarterly earnings
    a: float = 0.20  # Annual earnings
    n: float = 0.15  # New high
    s: float = 0.15  # Supply/demand
    l: float = 0.20  # Leader
    i: float = 0.10  # Institutional

    def __post_init__(self) -> None:
        total = self.c + self.a + self.n + self.s + self.l + self.i
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


@dataclass(frozen=True)
class CANSLIMScoreThresholds:
    """CAN-SLIMスコア計算の閾値（スコア化時の評価基準）"""

    # EPS成長率
    min_eps_growth: float = 25.0  # CAN-SLIM基準: 25%以上
    max_eps_growth: float = 100.0  # 100%以上は満点

    # 52週高値からの距離
    max_distance_from_high: float = 25.0  # 25%以内で評価対象

    # 出来高比率
    min_volume_ratio: float = 1.0  # 平均と同等以上
    max_volume_ratio: float = 3.0  # 3倍で満点

    # RS Rating
    min_rs_rating: int = 50  # 50以上で評価
    max_rs_rating: int = 99  # 99で満点

    # 機関投資家保有率
    min_inst_ownership: float = 10.0  # 10%以上で評価
    max_inst_ownership: float = 60.0  # 60%で満点
