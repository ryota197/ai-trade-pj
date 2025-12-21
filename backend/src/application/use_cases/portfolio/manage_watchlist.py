"""ウォッチリスト管理 ユースケース"""

from datetime import datetime

from src.application.dto.portfolio_dto import (
    AddToWatchlistInput,
    UpdateWatchlistInput,
    WatchlistFilterInput,
    WatchlistItemOutput,
    WatchlistOutput,
)
from src.domain.entities.watchlist_item import WatchlistItem, WatchlistStatus
from src.domain.repositories.watchlist_repository import WatchlistRepository


class ManageWatchlistUseCase:
    """
    ウォッチリスト管理 ユースケース

    ウォッチリストへの銘柄追加・削除・更新・取得を行う。
    """

    def __init__(self, watchlist_repository: WatchlistRepository) -> None:
        self._watchlist_repo = watchlist_repository

    async def add_to_watchlist(
        self,
        input_dto: AddToWatchlistInput,
    ) -> WatchlistItemOutput:
        """
        ウォッチリストに銘柄を追加

        Args:
            input_dto: 追加情報

        Returns:
            WatchlistItemOutput: 追加されたアイテム

        Raises:
            ValueError: 既に同じ銘柄がウォッチリストに存在する場合
        """
        # 既存チェック
        if await self._watchlist_repo.exists(input_dto.symbol):
            raise ValueError(f"Symbol {input_dto.symbol} already exists in watchlist")

        # エンティティ作成
        item = WatchlistItem.create(
            symbol=input_dto.symbol,
            target_entry_price=input_dto.target_entry_price,
            stop_loss_price=input_dto.stop_loss_price,
            target_price=input_dto.target_price,
            notes=input_dto.notes,
        )

        # 保存
        saved_item = await self._watchlist_repo.save(item)

        return self._to_output(saved_item)

    async def remove_from_watchlist(self, symbol: str) -> bool:
        """
        ウォッチリストから銘柄を削除

        Args:
            symbol: ティッカーシンボル

        Returns:
            bool: 削除成功したらTrue
        """
        item = await self._watchlist_repo.get_by_symbol(symbol.upper())
        if item is None:
            return False

        return await self._watchlist_repo.delete(item.id)

    async def remove_by_id(self, item_id: int) -> bool:
        """
        IDでウォッチリストアイテムを削除

        Args:
            item_id: アイテムID

        Returns:
            bool: 削除成功したらTrue
        """
        return await self._watchlist_repo.delete(item_id)

    async def update_watchlist_item(
        self,
        input_dto: UpdateWatchlistInput,
    ) -> WatchlistItemOutput | None:
        """
        ウォッチリストアイテムを更新

        Args:
            input_dto: 更新情報

        Returns:
            WatchlistItemOutput | None: 更新されたアイテム、存在しない場合はNone
        """
        existing = await self._watchlist_repo.get_by_id(input_dto.item_id)
        if existing is None:
            return None

        # 新しいエンティティを作成（frozen dataclass のため）
        updated_item = WatchlistItem(
            id=existing.id,
            symbol=existing.symbol,
            added_at=existing.added_at,
            target_entry_price=(
                input_dto.target_entry_price
                if input_dto.target_entry_price is not None
                else existing.target_entry_price
            ),
            stop_loss_price=(
                input_dto.stop_loss_price
                if input_dto.stop_loss_price is not None
                else existing.stop_loss_price
            ),
            target_price=(
                input_dto.target_price
                if input_dto.target_price is not None
                else existing.target_price
            ),
            notes=(
                input_dto.notes if input_dto.notes is not None else existing.notes
            ),
            status=existing.status,
            triggered_at=existing.triggered_at,
        )

        saved_item = await self._watchlist_repo.update(updated_item)
        return self._to_output(saved_item)

    async def get_watchlist(
        self,
        filter_input: WatchlistFilterInput | None = None,
    ) -> WatchlistOutput:
        """
        ウォッチリスト一覧を取得

        Args:
            filter_input: フィルター条件

        Returns:
            WatchlistOutput: ウォッチリスト一覧
        """
        if filter_input is None:
            filter_input = WatchlistFilterInput()

        # ステータスの変換
        status = None
        if filter_input.status:
            try:
                status = WatchlistStatus(filter_input.status)
            except ValueError:
                pass

        items = await self._watchlist_repo.get_all(
            status=status,
            limit=filter_input.limit,
            offset=filter_input.offset,
        )

        total_count = await self._watchlist_repo.count()
        watching_count = await self._watchlist_repo.count(WatchlistStatus.WATCHING)

        return WatchlistOutput(
            items=[self._to_output(item) for item in items],
            total_count=total_count,
            watching_count=watching_count,
        )

    async def get_watchlist_item(self, item_id: int) -> WatchlistItemOutput | None:
        """
        IDでウォッチリストアイテムを取得

        Args:
            item_id: アイテムID

        Returns:
            WatchlistItemOutput | None: アイテム、存在しない場合はNone
        """
        item = await self._watchlist_repo.get_by_id(item_id)
        if item is None:
            return None
        return self._to_output(item)

    async def get_watchlist_item_by_symbol(
        self,
        symbol: str,
    ) -> WatchlistItemOutput | None:
        """
        シンボルでウォッチリストアイテムを取得

        Args:
            symbol: ティッカーシンボル

        Returns:
            WatchlistItemOutput | None: アイテム、存在しない場合はNone
        """
        item = await self._watchlist_repo.get_by_symbol(symbol.upper())
        if item is None:
            return None
        return self._to_output(item)

    async def mark_as_triggered(self, item_id: int) -> bool:
        """
        アイテムをトリガー済みにマーク

        Args:
            item_id: アイテムID

        Returns:
            bool: 成功したらTrue
        """
        return await self._watchlist_repo.update_status(
            item_id, WatchlistStatus.TRIGGERED
        )

    async def get_watching_items(self) -> list[WatchlistItemOutput]:
        """
        監視中のアイテム一覧を取得

        Returns:
            list[WatchlistItemOutput]: 監視中のアイテムリスト
        """
        items = await self._watchlist_repo.get_watching()
        return [self._to_output(item) for item in items]

    def _to_output(self, item: WatchlistItem) -> WatchlistItemOutput:
        """エンティティを出力DTOに変換"""
        return WatchlistItemOutput(
            id=item.id,
            symbol=item.symbol,
            added_at=item.added_at,
            target_entry_price=item.target_entry_price,
            stop_loss_price=item.stop_loss_price,
            target_price=item.target_price,
            notes=item.notes,
            status=item.status.value,
            triggered_at=item.triggered_at,
            risk_reward_ratio=item.calculate_risk_reward_ratio(),
            potential_loss_percent=item.calculate_potential_loss_percent(),
            potential_gain_percent=item.calculate_potential_gain_percent(),
        )
