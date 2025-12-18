"""マーケットスナップショットリポジトリ インターフェース"""

from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.entities.market_status import MarketStatus


class MarketSnapshotRepository(ABC):
    """
    マーケットスナップショットリポジトリの抽象インターフェース

    マーケット状態の履歴保存・取得を抽象化する。
    Infrastructure層で具体的な実装を提供する。
    """

    @abstractmethod
    def save(self, market_status: MarketStatus) -> int:
        """
        マーケット状態を保存

        Args:
            market_status: 保存するマーケット状態

        Returns:
            int: 保存されたレコードのID
        """
        pass

    @abstractmethod
    def get_latest(self) -> MarketStatus | None:
        """
        最新のマーケット状態を取得

        Returns:
            MarketStatus | None: 最新のマーケット状態、存在しない場合はNone
        """
        pass

    @abstractmethod
    def get_history(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[MarketStatus]:
        """
        マーケット状態の履歴を取得

        Args:
            start_date: 開始日時（指定しない場合は制限なし）
            end_date: 終了日時（指定しない場合は現在まで）
            limit: 取得件数上限

        Returns:
            list[MarketStatus]: マーケット状態のリスト（新しい順）
        """
        pass
