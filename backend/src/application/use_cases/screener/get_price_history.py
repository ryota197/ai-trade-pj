"""株価履歴取得 ユースケース"""

from datetime import datetime

from src.application.dto.screener_dto import (
    PriceBarOutput,
    PriceHistoryInput,
    PriceHistoryOutput,
)
from src.application.interfaces.financial_data_gateway import FinancialDataGateway


class GetPriceHistoryUseCase:
    """
    株価履歴取得 ユースケース

    指定期間の株価履歴（OHLCV）を取得する。
    チャート表示やテクニカル分析に使用。
    """

    # 有効な期間とインターバルの組み合わせ
    VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"}
    VALID_INTERVALS = {"1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"}

    def __init__(
        self,
        financial_gateway: FinancialDataGateway,
    ) -> None:
        self._financial_gateway = financial_gateway

    async def execute(
        self,
        input_dto: PriceHistoryInput,
    ) -> PriceHistoryOutput:
        """
        株価履歴を取得

        Args:
            input_dto: 入力DTO（シンボル、期間、インターバル）

        Returns:
            PriceHistoryOutput: 株価履歴

        Raises:
            ValueError: 無効な期間またはインターバル
        """
        # バリデーション
        if input_dto.period not in self.VALID_PERIODS:
            raise ValueError(
                f"Invalid period: {input_dto.period}. "
                f"Valid periods: {self.VALID_PERIODS}"
            )

        if input_dto.interval not in self.VALID_INTERVALS:
            raise ValueError(
                f"Invalid interval: {input_dto.interval}. "
                f"Valid intervals: {self.VALID_INTERVALS}"
            )

        # 株価履歴を取得
        bars = await self._financial_gateway.get_price_history(
            symbol=input_dto.symbol,
            period=input_dto.period,
            interval=input_dto.interval,
        )

        # 出力DTOに変換
        bar_outputs = [
            PriceBarOutput(
                date=bar.date,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
            )
            for bar in bars
        ]

        return PriceHistoryOutput(
            symbol=input_dto.symbol,
            period=input_dto.period,
            interval=input_dto.interval,
            bars=bar_outputs,
            retrieved_at=datetime.now(),
        )
