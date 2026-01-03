"""マーケット指標取得ユースケース"""

from src.application.dto.market_dto import MarketIndicatorsOutput
from src.domain.models.market_snapshot import MarketSnapshot
from src.domain.repositories.market_snapshot_repository import MarketSnapshotRepository


class GetMarketIndicatorsUseCase:
    """
    マーケット指標取得ユースケース

    保存済みのマーケットスナップショットから指標を取得する。
    """

    def __init__(self, market_snapshot_repo: MarketSnapshotRepository) -> None:
        self._market_snapshot_repo = market_snapshot_repo

    def execute(self) -> MarketIndicatorsOutput | None:
        """
        マーケット指標を取得

        Returns:
            MarketIndicatorsOutput | None: マーケット指標の出力DTO、データがない場合はNone
        """
        snapshot = self._market_snapshot_repo.find_latest()

        if snapshot is None:
            return None

        return self._to_output(snapshot)

    def _to_output(self, snapshot: MarketSnapshot) -> MarketIndicatorsOutput:
        """スナップショットを出力DTOに変換"""
        return MarketIndicatorsOutput(
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
