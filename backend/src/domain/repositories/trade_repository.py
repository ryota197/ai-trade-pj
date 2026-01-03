"""TradeRepository インターフェース"""

from abc import ABC, abstractmethod

from src.domain.models.trade import Trade


class TradeRepository(ABC):
    """トレードリポジトリ"""

    @abstractmethod
    def find_by_id(self, trade_id: int) -> Trade | None:
        """IDでトレードを取得"""
        pass

    @abstractmethod
    def find_open_positions(self) -> list[Trade]:
        """オープンポジション一覧を取得"""
        pass

    @abstractmethod
    def find_by_symbol(self, symbol: str) -> list[Trade]:
        """シンボルでトレード一覧を取得"""
        pass

    @abstractmethod
    def find_closed(self, limit: int = 50) -> list[Trade]:
        """クローズ済みトレード一覧を取得"""
        pass

    @abstractmethod
    def save(self, trade: Trade) -> None:
        """トレードを保存"""
        pass
