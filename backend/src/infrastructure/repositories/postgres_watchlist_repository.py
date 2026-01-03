"""PostgreSQL ウォッチリストリポジトリ"""

from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from src.domain.models.watchlist_item import WatchlistItem, WatchlistStatus
from src.domain.repositories.watchlist_repository import WatchlistRepository
from src.infrastructure.database.models.watchlist_model import WatchlistModel


class PostgresWatchlistRepository(WatchlistRepository):
    """
    PostgreSQLによるウォッチリストリポジトリ実装

    WatchlistRepositoryインターフェースを実装し、
    ウォッチリストアイテムをPostgreSQLに保存・取得する。
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    async def get_by_id(self, item_id: int) -> WatchlistItem | None:
        """IDでウォッチリストアイテムを取得"""
        stmt = select(WatchlistModel).where(WatchlistModel.id == item_id)
        model = self._session.scalars(stmt).first()

        if model is None:
            return None

        return self._to_entity(model)

    async def get_by_symbol(self, symbol: str) -> WatchlistItem | None:
        """シンボルでウォッチリストアイテムを取得"""
        stmt = select(WatchlistModel).where(
            WatchlistModel.symbol == symbol.upper()
        )
        model = self._session.scalars(stmt).first()

        if model is None:
            return None

        return self._to_entity(model)

    async def get_all(
        self,
        status: WatchlistStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[WatchlistItem]:
        """ウォッチリストアイテム一覧を取得"""
        stmt = select(WatchlistModel)

        if status is not None:
            stmt = stmt.where(WatchlistModel.status == status.value)

        stmt = stmt.order_by(WatchlistModel.added_at.desc()).offset(offset).limit(limit)

        models = self._session.scalars(stmt).all()
        return [self._to_entity(model) for model in models]

    async def get_watching(self) -> list[WatchlistItem]:
        """監視中のアイテム一覧を取得"""
        stmt = (
            select(WatchlistModel)
            .where(WatchlistModel.status == WatchlistStatus.WATCHING.value)
            .order_by(WatchlistModel.added_at.desc())
        )

        models = self._session.scalars(stmt).all()
        return [self._to_entity(model) for model in models]

    async def save(self, item: WatchlistItem) -> WatchlistItem:
        """ウォッチリストアイテムを保存"""
        model = WatchlistModel(
            symbol=item.symbol.upper(),
            target_entry_price=item.target_entry_price,
            stop_loss_price=item.stop_loss_price,
            target_price=item.target_price,
            notes=item.notes,
            status=item.status.value,
            triggered_at=item.triggered_at,
            added_at=item.added_at,
        )

        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)

        return self._to_entity(model)

    async def update(self, item: WatchlistItem) -> WatchlistItem:
        """ウォッチリストアイテムを更新"""
        stmt = (
            update(WatchlistModel)
            .where(WatchlistModel.id == item.id)
            .values(
                target_entry_price=item.target_entry_price,
                stop_loss_price=item.stop_loss_price,
                target_price=item.target_price,
                notes=item.notes,
                status=item.status.value,
                triggered_at=item.triggered_at,
                updated_at=datetime.now(timezone.utc),
            )
        )

        self._session.execute(stmt)
        self._session.commit()

        # 更新後のエンティティを取得
        return await self.get_by_id(item.id)

    async def update_status(
        self,
        item_id: int,
        status: WatchlistStatus,
    ) -> bool:
        """ステータスを更新"""
        values = {
            "status": status.value,
            "updated_at": datetime.now(timezone.utc),
        }

        # トリガー済みの場合はtriggered_atも更新
        if status == WatchlistStatus.TRIGGERED:
            values["triggered_at"] = datetime.now(timezone.utc)

        stmt = (
            update(WatchlistModel)
            .where(WatchlistModel.id == item_id)
            .values(**values)
        )

        result = self._session.execute(stmt)
        self._session.commit()

        return result.rowcount > 0

    async def delete(self, item_id: int) -> bool:
        """ウォッチリストアイテムを削除"""
        stmt = delete(WatchlistModel).where(WatchlistModel.id == item_id)
        result = self._session.execute(stmt)
        self._session.commit()

        return result.rowcount > 0

    async def count(self, status: WatchlistStatus | None = None) -> int:
        """アイテム数をカウント"""
        stmt = select(func.count(WatchlistModel.id))

        if status is not None:
            stmt = stmt.where(WatchlistModel.status == status.value)

        return self._session.scalar(stmt) or 0

    async def exists(self, symbol: str) -> bool:
        """シンボルが既にウォッチリストに存在するか確認"""
        stmt = select(func.count(WatchlistModel.id)).where(
            WatchlistModel.symbol == symbol.upper()
        )
        count = self._session.scalar(stmt) or 0
        return count > 0

    def _to_entity(self, model: WatchlistModel) -> WatchlistItem:
        """モデルをエンティティに変換"""
        return WatchlistItem(
            id=model.id,
            symbol=model.symbol,
            added_at=model.added_at,
            target_entry_price=(
                float(model.target_entry_price) if model.target_entry_price else None
            ),
            stop_loss_price=(
                float(model.stop_loss_price) if model.stop_loss_price else None
            ),
            target_price=float(model.target_price) if model.target_price else None,
            notes=model.notes,
            status=WatchlistStatus(model.status),
            triggered_at=model.triggered_at,
        )
