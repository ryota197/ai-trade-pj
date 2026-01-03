"""MarketSnapshotRepository インターフェース"""

from abc import ABC, abstractmethod

from src.domain.models.market_snapshot import MarketSnapshot


class MarketSnapshotRepository(ABC):
    """市場スナップショットリポジトリ"""

    @abstractmethod
    def find_latest(self) -> MarketSnapshot | None:
        """最新のマーケット状態を取得"""
        pass

    @abstractmethod
    def save(self, snapshot: MarketSnapshot) -> None:
        """マーケット状態を保存"""
        pass
