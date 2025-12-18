"""マーケット状態取得ユースケース"""

from datetime import datetime

from src.application.dto.market_dto import MarketIndicatorsOutput, MarketStatusOutput
from src.domain.repositories.market_data_repository import MarketDataRepository
from src.domain.services.market_analyzer import MarketAnalyzer
from src.domain.value_objects.market_indicators import (
    MarketIndicators,
    MovingAverageIndicator,
    PutCallRatioIndicator,
    RsiIndicator,
    VixIndicator,
)


class GetMarketStatusUseCase:
    """
    マーケット状態取得ユースケース

    市場データを取得し、Risk On/Off/Neutral を判定して返す。
    """

    def __init__(
        self,
        market_data_repo: MarketDataRepository,
        market_analyzer: MarketAnalyzer,
    ) -> None:
        self._market_data_repo = market_data_repo
        self._market_analyzer = market_analyzer

    def execute(self) -> MarketStatusOutput:
        """
        マーケット状態を取得・分析

        Returns:
            MarketStatusOutput: マーケット状態の出力DTO
        """
        # 市場データを取得
        vix = self._market_data_repo.get_vix()
        sp500_price = self._market_data_repo.get_sp500_price()
        sp500_rsi = self._market_data_repo.get_sp500_rsi()
        sp500_ma200 = self._market_data_repo.get_sp500_ma200()
        put_call_ratio = self._market_data_repo.get_put_call_ratio()

        # ドメイン Value Object を構築
        indicators = MarketIndicators(
            vix=VixIndicator(value=vix),
            sp500_rsi=RsiIndicator(value=sp500_rsi),
            sp500_ma=MovingAverageIndicator(
                current_price=sp500_price,
                ma_200=sp500_ma200,
            ),
            put_call_ratio=PutCallRatioIndicator(value=put_call_ratio),
        )

        # ドメインサービスで分析
        market_status = self._market_analyzer.analyze(indicators)

        # 出力DTOに変換
        indicators_output = MarketIndicatorsOutput(
            vix=vix,
            vix_signal=indicators.vix.signal.value,
            sp500_price=sp500_price,
            sp500_rsi=sp500_rsi,
            sp500_rsi_signal=indicators.sp500_rsi.signal.value,
            sp500_ma200=sp500_ma200,
            sp500_above_ma200=indicators.sp500_ma.is_above_ma,
            put_call_ratio=put_call_ratio,
            put_call_signal=indicators.put_call_ratio.signal.value,
            retrieved_at=datetime.now(),
        )

        return MarketStatusOutput(
            condition=market_status.condition,
            condition_label=market_status.condition.value,
            confidence=market_status.confidence,
            score=market_status.score,
            recommendation=market_status.recommendation,
            indicators=indicators_output,
            analyzed_at=market_status.analyzed_at,
        )
