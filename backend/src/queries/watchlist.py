"""ウォッチリストクエリ"""

from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from src.models import Watchlist, WatchlistStatus


class WatchlistQuery:
    """ウォッチリストデータアクセス"""

    def __init__(self, session: Session) -> None:
        self._session = session

    async def get_by_id(self, item_id: int) -> Watchlist | None:
        """IDでウォッチリストアイテムを取得"""
        stmt = select(Watchlist).where(Watchlist.id == item_id)
        return self._session.scalars(stmt).first()

    async def get_by_symbol(self, symbol: str) -> Watchlist | None:
        """シンボルでウォッチリストアイテムを取得"""
        stmt = select(Watchlist).where(Watchlist.symbol == symbol.upper())
        return self._session.scalars(stmt).first()

    async def get_all(
        self,
        status: WatchlistStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Watchlist]:
        """ウォッチリストアイテム一覧を取得"""
        stmt = select(Watchlist)

        if status is not None:
            stmt = stmt.where(Watchlist.status == status.value)

        stmt = stmt.order_by(Watchlist.added_at.desc()).offset(offset).limit(limit)
        return list(self._session.scalars(stmt).all())

    async def get_watching(self) -> list[Watchlist]:
        """監視中のアイテム一覧を取得"""
        stmt = (
            select(Watchlist)
            .where(Watchlist.status == WatchlistStatus.WATCHING.value)
            .order_by(Watchlist.added_at.desc())
        )
        return list(self._session.scalars(stmt).all())

    async def save(self, item: Watchlist) -> Watchlist:
        """ウォッチリストアイテムを保存"""
        self._session.add(item)
        self._session.commit()
        self._session.refresh(item)
        return item

    async def update(self, item: Watchlist) -> Watchlist | None:
        """ウォッチリストアイテムを更新"""
        stmt = (
            update(Watchlist)
            .where(Watchlist.id == item.id)
            .values(
                target_entry_price=item.target_entry_price,
                stop_loss_price=item.stop_loss_price,
                target_price=item.target_price,
                notes=item.notes,
                status=item.status,
                triggered_at=item.triggered_at,
                updated_at=datetime.now(timezone.utc),
            )
        )

        self._session.execute(stmt)
        self._session.commit()

        return await self.get_by_id(item.id)

    async def update_status(
        self,
        item_id: int,
        status: WatchlistStatus,
    ) -> bool:
        """ステータスを更新"""
        values: dict = {
            "status": status.value,
            "updated_at": datetime.now(timezone.utc),
        }

        if status == WatchlistStatus.TRIGGERED:
            values["triggered_at"] = datetime.now(timezone.utc)

        stmt = update(Watchlist).where(Watchlist.id == item_id).values(**values)

        result = self._session.execute(stmt)
        self._session.commit()

        return result.rowcount > 0

    async def delete(self, item_id: int) -> bool:
        """ウォッチリストアイテムを削除"""
        stmt = delete(Watchlist).where(Watchlist.id == item_id)
        result = self._session.execute(stmt)
        self._session.commit()

        return result.rowcount > 0

    async def count(self, status: WatchlistStatus | None = None) -> int:
        """アイテム数をカウント"""
        stmt = select(func.count(Watchlist.id))

        if status is not None:
            stmt = stmt.where(Watchlist.status == status.value)

        return self._session.scalar(stmt) or 0

    async def exists(self, symbol: str) -> bool:
        """シンボルが既にウォッチリストに存在するか確認"""
        stmt = select(func.count(Watchlist.id)).where(
            Watchlist.symbol == symbol.upper()
        )
        count = self._session.scalar(stmt) or 0
        return count > 0
