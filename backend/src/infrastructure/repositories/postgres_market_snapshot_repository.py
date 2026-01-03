"""PostgreSQL マーケットスナップショットリポジトリ"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models.market_snapshot import MarketCondition, MarketSnapshot
from src.domain.repositories.market_snapshot_repository import MarketSnapshotRepository
from src.infrastructure.database.models.market_snapshot_model import (
    MarketSnapshotModel,
)


class PostgresMarketSnapshotRepository(MarketSnapshotRepository):
    """PostgreSQLによるマーケットスナップショットリポジトリ実装"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_latest(self) -> MarketSnapshot | None:
        """最新のマーケット状態を取得"""
        stmt = (
            select(MarketSnapshotModel)
            .order_by(MarketSnapshotModel.recorded_at.desc())
            .limit(1)
        )
        model = self._session.scalars(stmt).first()

        if model is None:
            return None

        return self._to_entity(model)

    def save(self, snapshot: MarketSnapshot) -> None:
        """マーケット状態を保存"""
        model = MarketSnapshotModel(
            recorded_at=snapshot.recorded_at,
            vix=float(snapshot.vix),
            sp500_price=float(snapshot.sp500_price),
            sp500_rsi=float(snapshot.sp500_rsi),
            sp500_ma200=float(snapshot.sp500_ma200),
            put_call_ratio=float(snapshot.put_call_ratio),
            condition=snapshot.condition.value,
            score=snapshot.score,
        )

        self._session.add(model)
        self._session.commit()

    def _to_entity(self, model: MarketSnapshotModel) -> MarketSnapshot:
        """モデルをエンティティに変換"""
        return MarketSnapshot(
            id=model.id,
            recorded_at=model.recorded_at,
            vix=Decimal(str(model.vix)),
            sp500_price=Decimal(str(model.sp500_price)),
            sp500_rsi=Decimal(str(model.sp500_rsi)),
            sp500_ma200=Decimal(str(model.sp500_ma200)),
            put_call_ratio=Decimal(str(model.put_call_ratio)),
            condition=MarketCondition(model.condition),
            score=model.score,
        )
