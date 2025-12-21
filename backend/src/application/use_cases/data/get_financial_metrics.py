"""財務指標取得ユースケース"""

from src.application.interfaces.financial_data_gateway import (
    FinancialDataGateway,
    FinancialMetrics,
)
from src.domain.services.eps_growth_calculator import EPSData, EPSGrowthCalculator


class GetFinancialMetricsUseCase:
    """
    財務指標取得ユースケース

    Gatewayから財務生データを取得し、
    Domain層のCalculatorでEPS成長率を計算して返す。

    責務分離:
        - Gateway: 外部API(yfinance)から生データを取得
        - EPSGrowthCalculator: EPS成長率の計算ロジック（Domain層）
        - UseCase: 上記を組み合わせてFinancialMetricsを構築
    """

    def __init__(
        self,
        financial_gateway: FinancialDataGateway,
        eps_calculator: EPSGrowthCalculator | None = None,
    ) -> None:
        """
        Args:
            financial_gateway: 財務データゲートウェイ
            eps_calculator: EPS成長率計算サービス（Noneの場合はstaticメソッドを使用）
        """
        self._gateway = financial_gateway
        self._eps_calculator = eps_calculator or EPSGrowthCalculator()

    async def execute(self, symbol: str) -> FinancialMetrics | None:
        """
        財務指標を取得

        Args:
            symbol: ティッカーシンボル

        Returns:
            FinancialMetrics: 財務指標（EPS成長率含む）、取得失敗時はNone
        """
        # 1. Gatewayから生データを取得（Infrastructure層）
        raw = await self._gateway.get_raw_financials(symbol)
        if raw is None:
            return None

        # 2. EPS成長率を計算（Domain層）
        eps_data = EPSData(
            quarterly_eps=raw.quarterly_eps,
            annual_eps=raw.annual_eps,
        )
        eps_result = EPSGrowthCalculator.calculate(eps_data)

        # 3. FinancialMetrics DTOを構築して返却
        return FinancialMetrics(
            symbol=raw.symbol,
            eps_ttm=raw.eps_ttm,
            eps_growth_quarterly=eps_result.quarterly_growth,
            eps_growth_annual=eps_result.annual_growth,
            revenue_growth=raw.revenue_growth,
            profit_margin=raw.profit_margin,
            roe=raw.roe,
            debt_to_equity=raw.debt_to_equity,
            institutional_ownership=raw.institutional_ownership,
        )
