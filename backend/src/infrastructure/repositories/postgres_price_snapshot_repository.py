"""PostgreSQL PriceSnapshot リポジトリ"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from src.domain.entities import PriceSnapshot
from src.domain.repositories import PriceSnapshotRepository
from src.infrastructure.database.models import StockPriceModel


class PostgresPriceSnapshotRepository(PriceSnapshotRepository):
    """価格スナップショットリポジトリ実装"""

    def __init__(self, session: Session) -> None:
        self._session = session

    async def save(self, snapshot: PriceSnapshot) -> None:
        """保存"""
        model = StockPriceModel(
            symbol=snapshot.symbol.upper(),
            price=snapshot.price,
            change_percent=snapshot.change_percent,
            volume=snapshot.volume,
            avg_volume_50d=snapshot.avg_volume_50d,
            market_cap=snapshot.market_cap,
            week_52_high=snapshot.week_52_high,
            week_52_low=snapshot.week_52_low,
            recorded_at=snapshot.recorded_at,
        )
        self._session.add(model)
        self._session.commit()

    async def get_latest(self, symbol: str) -> PriceSnapshot | None:
        """最新取得"""
        stmt = (
            select(StockPriceModel)
            .where(StockPriceModel.symbol == symbol.upper())
            .order_by(StockPriceModel.recorded_at.desc())
            .limit(1)
        )
        model = self._session.scalars(stmt).first()

        if model is None:
            return None

        return self._to_entity(model)

    async def get_by_date(self, symbol: str, target_date: date) -> PriceSnapshot | None:
        """日付指定取得"""
        stmt = (
            select(StockPriceModel)
            .where(StockPriceModel.symbol == symbol.upper())
            .where(func.date(StockPriceModel.recorded_at) == target_date)
            .limit(1)
        )
        model = self._session.scalars(stmt).first()

        if model is None:
            return None

        return self._to_entity(model)

    def _to_entity(self, model: StockPriceModel) -> PriceSnapshot:
        """モデルをエンティティに変換"""
        return PriceSnapshot(
            symbol=model.symbol,
            price=float(model.price) if model.price else None,
            change_percent=float(model.change_percent) if model.change_percent else None,
            volume=model.volume,
            avg_volume_50d=model.avg_volume_50d,
            market_cap=model.market_cap,
            week_52_high=float(model.week_52_high) if model.week_52_high else None,
            week_52_low=float(model.week_52_low) if model.week_52_low else None,
            recorded_at=model.recorded_at,
        )
