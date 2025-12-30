"""マーケット指標取得ユースケース"""

from datetime import datetime

from src.application.dto.market_dto import MarketIndicatorsOutput
from src.domain.repositories.market_data_repository import MarketDataRepository
from src.domain.models import (
    MovingAverageIndicator,
    PutCallRatioIndicator,
    RsiIndicator,
    VixIndicator,
)


class GetMarketIndicatorsUseCase:
    """
    マーケット指標取得ユースケース

    各種市場指標を取得して返す（状態判定は行わない）。
    """

    def __init__(self, market_data_repo: MarketDataRepository) -> None:
        self._market_data_repo = market_data_repo

    def execute(self) -> MarketIndicatorsOutput:
        """
        マーケット指標を取得

        Returns:
            MarketIndicatorsOutput: マーケット指標の出力DTO
        """
        # 市場データを取得
        vix = self._market_data_repo.get_vix()
        sp500_price = self._market_data_repo.get_sp500_price()
        sp500_rsi = self._market_data_repo.get_sp500_rsi()
        sp500_ma200 = self._market_data_repo.get_sp500_ma200()
        put_call_ratio = self._market_data_repo.get_put_call_ratio()

        # シグナル判定用に Value Object を構築
        vix_indicator = VixIndicator(value=vix)
        rsi_indicator = RsiIndicator(value=sp500_rsi)
        ma_indicator = MovingAverageIndicator(
            current_price=sp500_price,
            ma_200=sp500_ma200,
        )
        pc_indicator = PutCallRatioIndicator(value=put_call_ratio)

        return MarketIndicatorsOutput(
            vix=vix,
            vix_signal=vix_indicator.signal.value,
            sp500_price=sp500_price,
            sp500_rsi=sp500_rsi,
            sp500_rsi_signal=rsi_indicator.signal.value,
            sp500_ma200=sp500_ma200,
            sp500_above_ma200=ma_indicator.is_above_ma,
            put_call_ratio=put_call_ratio,
            put_call_signal=pc_indicator.signal.value,
            retrieved_at=datetime.now(),
        )
