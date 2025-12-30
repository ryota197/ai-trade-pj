"""WatchlistRepository Interface"""

from abc import ABC, abstractmethod

from src.domain.models.watchlist_item import WatchlistItem, WatchlistStatus


class WatchlistRepository(ABC):
    """
    ウォッチリストリポジトリ インターフェース

    ウォッチリストアイテムの永続化を担当する。
    """

    @abstractmethod
    async def get_by_id(self, item_id: int) -> WatchlistItem | None:
        """
        IDでウォッチリストアイテムを取得

        Args:
            item_id: アイテムID

        Returns:
            WatchlistItem | None: 見つかったアイテム、存在しない場合はNone
        """
        pass

    @abstractmethod
    async def get_by_symbol(self, symbol: str) -> WatchlistItem | None:
        """
        シンボルでウォッチリストアイテムを取得

        Args:
            symbol: ティッカーシンボル

        Returns:
            WatchlistItem | None: 見つかったアイテム、存在しない場合はNone
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        status: WatchlistStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[WatchlistItem]:
        """
        ウォッチリストアイテム一覧を取得

        Args:
            status: フィルタするステータス（Noneの場合は全て）
            limit: 取得件数上限
            offset: オフセット

        Returns:
            list[WatchlistItem]: ウォッチリストアイテムのリスト
        """
        pass

    @abstractmethod
    async def get_watching(self) -> list[WatchlistItem]:
        """
        監視中のアイテム一覧を取得

        Returns:
            list[WatchlistItem]: 監視中のアイテムのリスト
        """
        pass

    @abstractmethod
    async def save(self, item: WatchlistItem) -> WatchlistItem:
        """
        ウォッチリストアイテムを保存

        Args:
            item: 保存するアイテム

        Returns:
            WatchlistItem: 保存されたアイテム（IDが設定済み）
        """
        pass

    @abstractmethod
    async def update(self, item: WatchlistItem) -> WatchlistItem:
        """
        ウォッチリストアイテムを更新

        Args:
            item: 更新するアイテム

        Returns:
            WatchlistItem: 更新されたアイテム
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        item_id: int,
        status: WatchlistStatus,
    ) -> bool:
        """
        ステータスを更新

        Args:
            item_id: アイテムID
            status: 新しいステータス

        Returns:
            bool: 更新成功したらTrue
        """
        pass

    @abstractmethod
    async def delete(self, item_id: int) -> bool:
        """
        ウォッチリストアイテムを削除

        Args:
            item_id: 削除するアイテムのID

        Returns:
            bool: 削除成功したらTrue
        """
        pass

    @abstractmethod
    async def count(self, status: WatchlistStatus | None = None) -> int:
        """
        アイテム数をカウント

        Args:
            status: フィルタするステータス（Noneの場合は全て）

        Returns:
            int: アイテム数
        """
        pass

    @abstractmethod
    async def exists(self, symbol: str) -> bool:
        """
        シンボルが既にウォッチリストに存在するか確認

        Args:
            symbol: ティッカーシンボル

        Returns:
            bool: 存在すればTrue
        """
        pass
