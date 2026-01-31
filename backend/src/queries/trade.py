"""トレードクエリ"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Trade, TradeStatus


class TradeQuery:
    """トレードデータアクセス"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, trade_id: int) -> Trade | None:
        """IDでトレードを取得"""
        stmt = select(Trade).where(Trade.id == trade_id)
        return self._session.scalars(stmt).first()

    def find_open_positions(self) -> list[Trade]:
        """オープンポジション一覧を取得"""
        stmt = (
            select(Trade)
            .where(Trade.status == TradeStatus.OPEN.value)
            .order_by(Trade.traded_at.desc())
        )
        return list(self._session.scalars(stmt).all())

    def find_by_symbol(self, symbol: str) -> list[Trade]:
        """シンボルでトレード一覧を取得"""
        stmt = (
            select(Trade)
            .where(Trade.symbol == symbol.upper())
            .order_by(Trade.traded_at.desc())
        )
        return list(self._session.scalars(stmt).all())

    def find_closed(self, limit: int = 50) -> list[Trade]:
        """クローズ済みトレード一覧を取得"""
        stmt = (
            select(Trade)
            .where(Trade.status == TradeStatus.CLOSED.value)
            .order_by(Trade.closed_at.desc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt).all())

    def save(self, trade: Trade) -> Trade:
        """トレードを保存"""
        if trade.id is None:
            # 新規作成
            self._session.add(trade)
        # 既存の場合はセッションで追跡されているので変更が自動反映

        self._session.commit()
        self._session.refresh(trade)
        return trade
