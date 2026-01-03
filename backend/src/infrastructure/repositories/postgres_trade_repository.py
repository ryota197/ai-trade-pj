"""PostgreSQL トレードリポジトリ"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models.trade import Trade, TradeStatus, TradeType
from src.domain.repositories.trade_repository import TradeRepository
from src.infrastructure.database.models.trade_model import TradeModel


class PostgresTradeRepository(TradeRepository):
    """PostgreSQLによるトレードリポジトリ実装"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, trade_id: int) -> Trade | None:
        """IDでトレードを取得"""
        stmt = select(TradeModel).where(TradeModel.id == trade_id)
        model = self._session.scalars(stmt).first()

        if model is None:
            return None

        return self._to_entity(model)

    def find_open_positions(self) -> list[Trade]:
        """オープンポジション一覧を取得"""
        stmt = (
            select(TradeModel)
            .where(TradeModel.status == TradeStatus.OPEN.value)
            .order_by(TradeModel.traded_at.desc())
        )
        models = self._session.scalars(stmt).all()
        return [self._to_entity(model) for model in models]

    def find_by_symbol(self, symbol: str) -> list[Trade]:
        """シンボルでトレード一覧を取得"""
        stmt = (
            select(TradeModel)
            .where(TradeModel.symbol == symbol.upper())
            .order_by(TradeModel.traded_at.desc())
        )
        models = self._session.scalars(stmt).all()
        return [self._to_entity(model) for model in models]

    def find_closed(self, limit: int = 50) -> list[Trade]:
        """クローズ済みトレード一覧を取得"""
        stmt = (
            select(TradeModel)
            .where(TradeModel.status == TradeStatus.CLOSED.value)
            .order_by(TradeModel.closed_at.desc())
            .limit(limit)
        )
        models = self._session.scalars(stmt).all()
        return [self._to_entity(model) for model in models]

    def save(self, trade: Trade) -> None:
        """トレードを保存"""
        if trade.id is None:
            # 新規作成
            model = TradeModel(
                symbol=trade.symbol.upper(),
                trade_type=trade.trade_type.value,
                quantity=trade.quantity,
                entry_price=float(trade.entry_price),
                exit_price=float(trade.exit_price) if trade.exit_price else None,
                status=trade.status.value,
                traded_at=trade.traded_at,
                closed_at=trade.closed_at,
            )
            self._session.add(model)
        else:
            # 更新
            stmt = select(TradeModel).where(TradeModel.id == trade.id)
            model = self._session.scalars(stmt).first()
            if model:
                model.symbol = trade.symbol.upper()
                model.trade_type = trade.trade_type.value
                model.quantity = trade.quantity
                model.entry_price = float(trade.entry_price)
                model.exit_price = (
                    float(trade.exit_price) if trade.exit_price else None
                )
                model.status = trade.status.value
                model.traded_at = trade.traded_at
                model.closed_at = trade.closed_at

        self._session.commit()

    def _to_entity(self, model: TradeModel) -> Trade:
        """モデルをエンティティに変換"""
        return Trade(
            id=model.id,
            symbol=model.symbol,
            trade_type=TradeType(model.trade_type),
            quantity=model.quantity,
            entry_price=Decimal(str(model.entry_price)),
            exit_price=Decimal(str(model.exit_price)) if model.exit_price else None,
            status=TradeStatus(model.status),
            traded_at=model.traded_at,
            closed_at=model.closed_at,
        )
