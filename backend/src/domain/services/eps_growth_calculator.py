"""EPS成長率計算サービス"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EPSData:
    """EPS生データ

    Gatewayから取得した四半期・年間EPSの生データを保持する。
    計算はEPSGrowthCalculatorで行う。
    """

    quarterly_eps: list[float]  # 四半期EPS（新しい順）
    annual_eps: list[float]  # 年間EPS（新しい順）


@dataclass(frozen=True)
class EPSGrowthResult:
    """EPS成長率計算結果"""

    quarterly_growth: float | None  # 四半期成長率（%）
    annual_growth: float | None  # 年間成長率（%）


class EPSGrowthCalculator:
    """
    EPS成長率計算サービス

    四半期EPS成長率（前年同期比）と年間EPS成長率を計算する。
    CAN-SLIM の C (Current quarterly earnings) と
    A (Annual earnings) の評価に使用される。
    """

    @staticmethod
    def calculate_quarterly_growth(eps_data: EPSData) -> float | None:
        """
        四半期EPS成長率を計算（前年同期比）

        Args:
            eps_data: EPS生データ

        Returns:
            float | None: 成長率（%）、計算不可の場合はNone

        Note:
            CAN-SLIMでは最低25%以上の成長を基準とする
        """
        quarterly = eps_data.quarterly_eps

        if len(quarterly) < 2:
            return None

        # 最新四半期と前年同期を比較
        # quarterly_eps は新しい順なので、[0]が最新、[3]or[1]が比較対象
        current = quarterly[0]
        previous = quarterly[3] if len(quarterly) >= 4 else quarterly[1]

        if previous == 0:
            return None

        growth = ((current - previous) / abs(previous)) * 100
        return round(growth, 2)

    @staticmethod
    def calculate_annual_growth(eps_data: EPSData) -> float | None:
        """
        年間EPS成長率を計算

        Args:
            eps_data: EPS生データ

        Returns:
            float | None: 成長率（%）、計算不可の場合はNone

        Note:
            CAN-SLIMでは過去3年間で年25%以上の成長を基準とする
        """
        annual = eps_data.annual_eps

        if len(annual) < 2:
            return None

        # 最新年度と前年度を比較
        # annual_eps は新しい順なので、[0]が最新、[1]が前年度
        current = annual[0]
        previous = annual[1]

        if previous == 0:
            return None

        growth = ((current - previous) / abs(previous)) * 100
        return round(growth, 2)

    @classmethod
    def calculate(cls, eps_data: EPSData) -> EPSGrowthResult:
        """
        四半期・年間EPS成長率を一括計算

        Args:
            eps_data: EPS生データ

        Returns:
            EPSGrowthResult: 計算結果
        """
        return EPSGrowthResult(
            quarterly_growth=cls.calculate_quarterly_growth(eps_data),
            annual_growth=cls.calculate_annual_growth(eps_data),
        )
