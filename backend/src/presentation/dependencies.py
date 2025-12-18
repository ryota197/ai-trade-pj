"""依存性注入設定"""

from src.application.use_cases.market import (
    GetMarketIndicatorsUseCase,
    GetMarketStatusUseCase,
)
from src.domain.services.market_analyzer import MarketAnalyzer
from src.infrastructure.gateways.yfinance_market_data_gateway import (
    YFinanceMarketDataGateway,
)


def get_market_status_use_case() -> GetMarketStatusUseCase:
    """
    GetMarketStatusUseCaseの依存性を解決

    Returns:
        GetMarketStatusUseCase: マーケット状態取得ユースケース
    """
    market_data_repo = YFinanceMarketDataGateway()
    market_analyzer = MarketAnalyzer()

    return GetMarketStatusUseCase(
        market_data_repo=market_data_repo,
        market_analyzer=market_analyzer,
    )


def get_market_indicators_use_case() -> GetMarketIndicatorsUseCase:
    """
    GetMarketIndicatorsUseCaseの依存性を解決

    Returns:
        GetMarketIndicatorsUseCase: マーケット指標取得ユースケース
    """
    market_data_repo = YFinanceMarketDataGateway()

    return GetMarketIndicatorsUseCase(market_data_repo=market_data_repo)
