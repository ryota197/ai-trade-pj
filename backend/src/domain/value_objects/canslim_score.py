"""CAN-SLIM スコア Value Object"""

from dataclasses import dataclass
from enum import Enum


class ScoreGrade(Enum):
    """スコアグレード"""

    EXCELLENT = "excellent"  # 基準を大きく上回る
    GOOD = "good"  # 基準を満たす
    FAIR = "fair"  # 基準未満だが許容範囲
    POOR = "poor"  # 基準を満たさない
    NA = "na"  # データなし


@dataclass(frozen=True)
class CANSLIMCriteria:
    """
    CAN-SLIM 各項目の評価基準

    各項目のスコア（0-100）とグレードを保持する。
    """

    score: int  # 0-100
    grade: ScoreGrade
    value: float | None  # 実際の値
    threshold: float  # 基準値
    description: str

    @classmethod
    def evaluate(
        cls,
        value: float | None,
        threshold: float,
        description: str,
        higher_is_better: bool = True,
    ) -> "CANSLIMCriteria":
        """値を評価してスコアを計算"""
        if value is None:
            return cls(
                score=0,
                grade=ScoreGrade.NA,
                value=None,
                threshold=threshold,
                description=description,
            )

        # スコア計算（基準値との比率）
        if higher_is_better:
            ratio = value / threshold if threshold != 0 else 0
        else:
            # lower is better（例：52週高値からの乖離）
            ratio = threshold / value if value != 0 else 0

        score = min(100, int(ratio * 100))

        # グレード判定
        if ratio >= 1.5:
            grade = ScoreGrade.EXCELLENT
        elif ratio >= 1.0:
            grade = ScoreGrade.GOOD
        elif ratio >= 0.7:
            grade = ScoreGrade.FAIR
        else:
            grade = ScoreGrade.POOR

        return cls(
            score=score,
            grade=grade,
            value=value,
            threshold=threshold,
            description=description,
        )

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "score": self.score,
            "grade": self.grade.value,
            "value": self.value,
            "threshold": self.threshold,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CANSLIMCriteria":
        """辞書から復元"""
        grade_value = data.get("grade", "na")
        try:
            grade = ScoreGrade(grade_value)
        except ValueError:
            grade = ScoreGrade.NA

        return cls(
            score=data.get("score", 0),
            grade=grade,
            value=data.get("value"),
            threshold=data.get("threshold", 0.0),
            description=data.get("description", ""),
        )


@dataclass(frozen=True)
class CANSLIMScore:
    """
    CAN-SLIM スコア Value Object

    William O'Neilが提唱するCAN-SLIM投資法の各項目スコアを集約する。
    - C: Current Quarterly Earnings（四半期EPS成長率）
    - A: Annual Earnings（年間EPS成長率）
    - N: New High（新高値 / 52週高値からの乖離）
    - S: Supply and Demand（出来高倍率）
    - L: Leader（RS Rating）
    - I: Institutional Sponsorship（機関投資家保有率）
    - M: Market Direction（マーケット環境）- 外部から参照
    """

    c_score: CANSLIMCriteria  # Current Quarterly Earnings
    a_score: CANSLIMCriteria  # Annual Earnings
    n_score: CANSLIMCriteria  # New High
    s_score: CANSLIMCriteria  # Supply and Demand
    l_score: CANSLIMCriteria  # Leader (RS Rating)
    i_score: CANSLIMCriteria  # Institutional Sponsorship

    @property
    def total_score(self) -> int:
        """
        総合スコア（0-100）

        各項目の加重平均を計算。
        L (RS Rating)とC (四半期EPS)を重視。
        """
        weights = {
            "c": 20,  # Current Quarterly Earnings
            "a": 15,  # Annual Earnings
            "n": 15,  # New High
            "s": 10,  # Supply and Demand
            "l": 25,  # Leader (most important)
            "i": 15,  # Institutional
        }

        weighted_sum = (
            self.c_score.score * weights["c"]
            + self.a_score.score * weights["a"]
            + self.n_score.score * weights["n"]
            + self.s_score.score * weights["s"]
            + self.l_score.score * weights["l"]
            + self.i_score.score * weights["i"]
        )

        total_weight = sum(weights.values())
        return int(weighted_sum / total_weight)

    @property
    def passing_criteria_count(self) -> int:
        """基準を満たす項目数"""
        criteria = [
            self.c_score,
            self.a_score,
            self.n_score,
            self.s_score,
            self.l_score,
            self.i_score,
        ]
        return sum(
            1
            for c in criteria
            if c.grade in (ScoreGrade.EXCELLENT, ScoreGrade.GOOD)
        )

    @property
    def overall_grade(self) -> ScoreGrade:
        """総合グレード"""
        score = self.total_score
        if score >= 85:
            return ScoreGrade.EXCELLENT
        elif score >= 70:
            return ScoreGrade.GOOD
        elif score >= 50:
            return ScoreGrade.FAIR
        return ScoreGrade.POOR

    def is_screener_candidate(
        self,
        min_total_score: int = 70,
        min_passing_count: int = 4,
    ) -> bool:
        """スクリーニング候補として適格か"""
        return (
            self.total_score >= min_total_score
            and self.passing_criteria_count >= min_passing_count
        )

    @classmethod
    def calculate(
        cls,
        eps_growth_quarterly: float | None,
        eps_growth_annual: float | None,
        distance_from_52w_high: float,
        volume_ratio: float,
        rs_rating: int,
        institutional_ownership: float | None,
    ) -> "CANSLIMScore":
        """各値からCANSLIMScoreを計算"""
        c_score = CANSLIMCriteria.evaluate(
            value=eps_growth_quarterly,
            threshold=25.0,
            description="四半期EPS成長率 (>=25%)",
            higher_is_better=True,
        )

        a_score = CANSLIMCriteria.evaluate(
            value=eps_growth_annual,
            threshold=25.0,
            description="年間EPS成長率 (>=25%)",
            higher_is_better=True,
        )

        # N: 52週高値からの乖離は低いほど良い
        # 15%以内が理想的なので、逆数で評価
        n_value = 100 - distance_from_52w_high if distance_from_52w_high <= 100 else 0
        n_score = CANSLIMCriteria.evaluate(
            value=n_value,
            threshold=85.0,  # 15%乖離 = 85点
            description="52週高値からの近さ (<=15%乖離)",
            higher_is_better=True,
        )

        s_score = CANSLIMCriteria.evaluate(
            value=volume_ratio,
            threshold=1.5,
            description="出来高倍率 (>=1.5x)",
            higher_is_better=True,
        )

        l_score = CANSLIMCriteria.evaluate(
            value=float(rs_rating),
            threshold=80.0,
            description="RS Rating (>=80)",
            higher_is_better=True,
        )

        i_score = CANSLIMCriteria.evaluate(
            value=institutional_ownership,
            threshold=50.0,
            description="機関投資家保有率 (参考値)",
            higher_is_better=True,
        )

        return cls(
            c_score=c_score,
            a_score=a_score,
            n_score=n_score,
            s_score=s_score,
            l_score=l_score,
            i_score=i_score,
        )

    def to_dict(self) -> dict:
        """辞書形式に変換（永続化用）"""
        return {
            "c_score": self.c_score.to_dict(),
            "a_score": self.a_score.to_dict(),
            "n_score": self.n_score.to_dict(),
            "s_score": self.s_score.to_dict(),
            "l_score": self.l_score.to_dict(),
            "i_score": self.i_score.to_dict(),
            "total_score": self.total_score,
            "passing_count": self.passing_criteria_count,
            "overall_grade": self.overall_grade.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CANSLIMScore":
        """
        辞書から復元（再計算なし）

        保存されたデータから直接CANSLIMScoreを復元する。
        calculate()と異なり、スコアを再計算しない。
        """
        return cls(
            c_score=CANSLIMCriteria.from_dict(data.get("c_score", {})),
            a_score=CANSLIMCriteria.from_dict(data.get("a_score", {})),
            n_score=CANSLIMCriteria.from_dict(data.get("n_score", {})),
            s_score=CANSLIMCriteria.from_dict(data.get("s_score", {})),
            l_score=CANSLIMCriteria.from_dict(data.get("l_score", {})),
            i_score=CANSLIMCriteria.from_dict(data.get("i_score", {})),
        )
