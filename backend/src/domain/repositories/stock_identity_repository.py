"""銘柄マスター リポジトリ インターフェース"""

from abc import ABC, abstractmethod

from src.domain.entities import StockIdentity


class StockIdentityRepository(ABC):
    """
    銘柄マスター リポジトリ

    対応テーブル: stocks
    """

    @abstractmethod
    async def save(self, identity: StockIdentity) -> None:
        """保存（UPSERT）"""
        pass

    @abstractmethod
    async def get(self, symbol: str) -> StockIdentity | None:
        """取得"""
        pass

    @abstractmethod
    async def get_all_symbols(self) -> list[str]:
        """全シンボル取得"""
        pass

    @abstractmethod
    async def delete(self, symbol: str) -> bool:
        """削除"""
        pass
