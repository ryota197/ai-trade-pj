"""PostgreSQL トレードリポジトリ"""

from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from src.domain.entities.paper_trade import PaperTrade, TradeStatus, TradeType
from src.domain.repositories.trade_repository import TradeRepository
from src.infrastructure.database.models.paper_trade_model import PaperTradeModel


class PostgresTradeRepository(TradeRepository):
    """
    PostgreSQLによるトレードリポジトリ実装

    TradeRepositoryインターフェースを実装し、
    ペーパートレードをPostgreSQLに保存・取得する。
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    async def get_by_id(self, trade_id: int) -> PaperTrade | None:
        """IDでトレードを取得"""
        stmt = select(PaperTradeModel).where(PaperTradeModel.id == trade_id)
        model = self._session.scalars(stmt).first()

        if model is None:
            return None

        return self._to_entity(model)

    async def get_by_symbol(
        self,
        symbol: str,
        status: TradeStatus | None = None,
    ) -> list[PaperTrade]:
        """シンボルでトレード一覧を取得"""
        stmt = select(PaperTradeModel).where(
            PaperTradeModel.symbol == symbol.upper()
        )

        if status is not None:
            stmt = stmt.where(PaperTradeModel.status == status.value)

        stmt = stmt.order_by(PaperTradeModel.entry_date.desc())

        models = self._session.scalars(stmt).all()
        return [self._to_entity(model) for model in models]

    async def get_all(
        self,
        status: TradeStatus | None = None,
        trade_type: TradeType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PaperTrade]:
        """トレード一覧を取得"""
        stmt = select(PaperTradeModel)

        if status is not None:
            stmt = stmt.where(PaperTradeModel.status == status.value)

        if trade_type is not None:
            stmt = stmt.where(PaperTradeModel.trade_type == trade_type.value)

        stmt = (
            stmt.order_by(PaperTradeModel.entry_date.desc())
            .offset(offset)
            .limit(limit)
        )

        models = self._session.scalars(stmt).all()
        return [self._to_entity(model) for model in models]

    async def get_open_positions(self) -> list[PaperTrade]:
        """オープンポジション一覧を取得"""
        stmt = (
            select(PaperTradeModel)
            .where(PaperTradeModel.status == TradeStatus.OPEN.value)
            .order_by(PaperTradeModel.entry_date.desc())
        )

        models = self._session.scalars(stmt).all()
        return [self._to_entity(model) for model in models]

    async def get_closed_trades(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PaperTrade]:
        """クローズ済みトレード一覧を取得"""
        stmt = select(PaperTradeModel).where(
            PaperTradeModel.status == TradeStatus.CLOSED.value
        )

        if start_date is not None:
            stmt = stmt.where(PaperTradeModel.exit_date >= start_date)

        if end_date is not None:
            stmt = stmt.where(PaperTradeModel.exit_date <= end_date)

        stmt = (
            stmt.order_by(PaperTradeModel.exit_date.desc())
            .offset(offset)
            .limit(limit)
        )

        models = self._session.scalars(stmt).all()
        return [self._to_entity(model) for model in models]

    async def save(self, trade: PaperTrade) -> PaperTrade:
        """トレードを保存"""
        model = PaperTradeModel(
            symbol=trade.symbol.upper(),
            trade_type=trade.trade_type.value,
            quantity=trade.quantity,
            entry_price=trade.entry_price,
            entry_date=trade.entry_date,
            exit_price=trade.exit_price,
            exit_date=trade.exit_date,
            stop_loss_price=trade.stop_loss_price,
            target_price=trade.target_price,
            status=trade.status.value,
            notes=trade.notes,
            created_at=trade.created_at,
        )

        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)

        return self._to_entity(model)

    async def update(self, trade: PaperTrade) -> PaperTrade:
        """トレードを更新"""
        stmt = (
            update(PaperTradeModel)
            .where(PaperTradeModel.id == trade.id)
            .values(
                symbol=trade.symbol.upper(),
                trade_type=trade.trade_type.value,
                quantity=trade.quantity,
                entry_price=trade.entry_price,
                entry_date=trade.entry_date,
                exit_price=trade.exit_price,
                exit_date=trade.exit_date,
                stop_loss_price=trade.stop_loss_price,
                target_price=trade.target_price,
                status=trade.status.value,
                notes=trade.notes,
                updated_at=datetime.now(timezone.utc),
            )
        )

        self._session.execute(stmt)
        self._session.commit()

        return await self.get_by_id(trade.id)

    async def close_position(
        self,
        trade_id: int,
        exit_price: float,
        exit_date: datetime | None = None,
    ) -> PaperTrade | None:
        """ポジションをクローズ"""
        if exit_date is None:
            exit_date = datetime.now(timezone.utc)

        stmt = (
            update(PaperTradeModel)
            .where(PaperTradeModel.id == trade_id)
            .where(PaperTradeModel.status == TradeStatus.OPEN.value)
            .values(
                exit_price=exit_price,
                exit_date=exit_date,
                status=TradeStatus.CLOSED.value,
                updated_at=datetime.now(timezone.utc),
            )
        )

        result = self._session.execute(stmt)
        self._session.commit()

        if result.rowcount == 0:
            return None

        return await self.get_by_id(trade_id)

    async def cancel_trade(self, trade_id: int) -> bool:
        """トレードをキャンセル"""
        stmt = (
            update(PaperTradeModel)
            .where(PaperTradeModel.id == trade_id)
            .where(PaperTradeModel.status == TradeStatus.OPEN.value)
            .values(
                status=TradeStatus.CANCELLED.value,
                updated_at=datetime.now(timezone.utc),
            )
        )

        result = self._session.execute(stmt)
        self._session.commit()

        return result.rowcount > 0

    async def delete(self, trade_id: int) -> bool:
        """トレードを削除"""
        stmt = delete(PaperTradeModel).where(PaperTradeModel.id == trade_id)
        result = self._session.execute(stmt)
        self._session.commit()

        return result.rowcount > 0

    async def count(
        self,
        status: TradeStatus | None = None,
        trade_type: TradeType | None = None,
    ) -> int:
        """トレード数をカウント"""
        stmt = select(func.count(PaperTradeModel.id))

        if status is not None:
            stmt = stmt.where(PaperTradeModel.status == status.value)

        if trade_type is not None:
            stmt = stmt.where(PaperTradeModel.trade_type == trade_type.value)

        return self._session.scalar(stmt) or 0

    async def get_total_profit_loss(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> float:
        """期間内の総損益を取得"""
        # クローズ済みトレードを取得して計算
        trades = await self.get_closed_trades(
            start_date=start_date,
            end_date=end_date,
            limit=10000,
        )

        total_pnl = 0.0
        for trade in trades:
            if trade.profit_loss is not None:
                total_pnl += trade.profit_loss

        return round(total_pnl, 2)

    def _to_entity(self, model: PaperTradeModel) -> PaperTrade:
        """モデルをエンティティに変換"""
        return PaperTrade(
            id=model.id,
            symbol=model.symbol,
            trade_type=TradeType(model.trade_type),
            quantity=model.quantity,
            entry_price=float(model.entry_price),
            entry_date=model.entry_date,
            exit_price=float(model.exit_price) if model.exit_price else None,
            exit_date=model.exit_date,
            stop_loss_price=(
                float(model.stop_loss_price) if model.stop_loss_price else None
            ),
            target_price=float(model.target_price) if model.target_price else None,
            status=TradeStatus(model.status),
            notes=model.notes,
            created_at=model.created_at,
        )
