"""マーケット状態取得ユースケース"""

from datetime import datetime

from src.application.dto.market_dto import MarketIndicatorsOutput, MarketStatusOutput
from src.domain.models.market_snapshot import MarketSnapshot
from src.domain.repositories.market_snapshot_repository import MarketSnapshotRepository


class GetMarketStatusUseCase:
    """
    マーケット状態取得ユースケース

    保存済みのマーケットスナップショットから状態を取得する。
    """

    def __init__(self, market_snapshot_repo: MarketSnapshotRepository) -> None:
        self._market_snapshot_repo = market_snapshot_repo

    def execute(self) -> MarketStatusOutput | None:
        """
        最新のマーケット状態を取得

        Returns:
            MarketStatusOutput | None: マーケット状態の出力DTO、データがない場合はNone
        """
        snapshot = self._market_snapshot_repo.find_latest()

        if snapshot is None:
            return None

        return self._to_output(snapshot)

    def _to_output(self, snapshot: MarketSnapshot) -> MarketStatusOutput:
        """スナップショットを出力DTOに変換"""
        indicators_output = MarketIndicatorsOutput(
            vix=snapshot.vix,
            vix_signal=snapshot.vix_signal().value,
            sp500_price=snapshot.sp500_price,
            sp500_rsi=snapshot.sp500_rsi,
            sp500_rsi_signal=snapshot.rsi_signal().value,
            sp500_ma200=snapshot.sp500_ma200,
            sp500_above_ma200=snapshot.is_above_ma200(),
            put_call_ratio=snapshot.put_call_ratio,
            put_call_signal=snapshot.put_call_signal().value,
            retrieved_at=snapshot.recorded_at,
        )

        return MarketStatusOutput(
            condition=snapshot.condition,
            condition_label=snapshot.condition.value,
            score=snapshot.score,
            indicators=indicators_output,
            recorded_at=snapshot.recorded_at,
        )
