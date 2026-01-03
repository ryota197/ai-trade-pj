"""財務指標取得ユースケース"""

from src.application.interfaces.financial_data_gateway import (
    FinancialDataGateway,
    FinancialMetrics,
)


class GetFinancialMetricsUseCase:
    """
    財務指標取得ユースケース

    Gatewayから財務データを取得して返す。
    EPS成長率はAPI（yfinance）から直接取得する。
    """

    def __init__(self, financial_gateway: FinancialDataGateway) -> None:
        """
        Args:
            financial_gateway: 財務データゲートウェイ
        """
        self._gateway = financial_gateway

    async def execute(self, symbol: str) -> FinancialMetrics | None:
        """
        財務指標を取得

        Args:
            symbol: ティッカーシンボル

        Returns:
            FinancialMetrics: 財務指標、取得失敗時はNone
        """
        return await self._gateway.get_financial_metrics(symbol)
