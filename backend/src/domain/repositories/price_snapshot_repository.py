"""価格スナップショット リポジトリ インターフェース"""

from abc import ABC, abstractmethod
from datetime import date

from src.domain.entities import PriceSnapshot


class PriceSnapshotRepository(ABC):
    """
    価格スナップショット リポジトリ

    対応テーブル: stock_prices
    """

    @abstractmethod
    async def save(self, snapshot: PriceSnapshot) -> None:
        """保存"""
        pass

    @abstractmethod
    async def get_latest(self, symbol: str) -> PriceSnapshot | None:
        """最新取得"""
        pass

    @abstractmethod
    async def get_by_date(self, symbol: str, target_date: date) -> PriceSnapshot | None:
        """日付指定取得"""
        pass
