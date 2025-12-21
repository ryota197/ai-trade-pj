"""TradeRepository Interface"""

from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.entities.paper_trade import PaperTrade, TradeStatus, TradeType


class TradeRepository(ABC):
    """
    トレードリポジトリ インターフェース

    ペーパートレードの永続化を担当する。
    """

    @abstractmethod
    async def get_by_id(self, trade_id: int) -> PaperTrade | None:
        """
        IDでトレードを取得

        Args:
            trade_id: トレードID

        Returns:
            PaperTrade | None: 見つかったトレード、存在しない場合はNone
        """
        pass

    @abstractmethod
    async def get_by_symbol(
        self,
        symbol: str,
        status: TradeStatus | None = None,
    ) -> list[PaperTrade]:
        """
        シンボルでトレード一覧を取得

        Args:
            symbol: ティッカーシンボル
            status: フィルタするステータス（Noneの場合は全て）

        Returns:
            list[PaperTrade]: トレードのリスト
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        status: TradeStatus | None = None,
        trade_type: TradeType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PaperTrade]:
        """
        トレード一覧を取得

        Args:
            status: フィルタするステータス（Noneの場合は全て）
            trade_type: フィルタするトレードタイプ（Noneの場合は全て）
            limit: 取得件数上限
            offset: オフセット

        Returns:
            list[PaperTrade]: トレードのリスト
        """
        pass

    @abstractmethod
    async def get_open_positions(self) -> list[PaperTrade]:
        """
        オープンポジション一覧を取得

        Returns:
            list[PaperTrade]: オープンポジションのリスト
        """
        pass

    @abstractmethod
    async def get_closed_trades(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PaperTrade]:
        """
        クローズ済みトレード一覧を取得

        Args:
            start_date: 開始日（Noneの場合は制限なし）
            end_date: 終了日（Noneの場合は制限なし）
            limit: 取得件数上限
            offset: オフセット

        Returns:
            list[PaperTrade]: クローズ済みトレードのリスト
        """
        pass

    @abstractmethod
    async def save(self, trade: PaperTrade) -> PaperTrade:
        """
        トレードを保存

        Args:
            trade: 保存するトレード

        Returns:
            PaperTrade: 保存されたトレード（IDが設定済み）
        """
        pass

    @abstractmethod
    async def update(self, trade: PaperTrade) -> PaperTrade:
        """
        トレードを更新

        Args:
            trade: 更新するトレード

        Returns:
            PaperTrade: 更新されたトレード
        """
        pass

    @abstractmethod
    async def close_position(
        self,
        trade_id: int,
        exit_price: float,
        exit_date: datetime | None = None,
    ) -> PaperTrade | None:
        """
        ポジションをクローズ

        Args:
            trade_id: トレードID
            exit_price: 決済価格
            exit_date: 決済日時（Noneの場合は現在時刻）

        Returns:
            PaperTrade | None: クローズされたトレード、存在しない場合はNone
        """
        pass

    @abstractmethod
    async def cancel_trade(self, trade_id: int) -> bool:
        """
        トレードをキャンセル

        Args:
            trade_id: トレードID

        Returns:
            bool: キャンセル成功したらTrue
        """
        pass

    @abstractmethod
    async def delete(self, trade_id: int) -> bool:
        """
        トレードを削除

        Args:
            trade_id: 削除するトレードのID

        Returns:
            bool: 削除成功したらTrue
        """
        pass

    @abstractmethod
    async def count(
        self,
        status: TradeStatus | None = None,
        trade_type: TradeType | None = None,
    ) -> int:
        """
        トレード数をカウント

        Args:
            status: フィルタするステータス（Noneの場合は全て）
            trade_type: フィルタするトレードタイプ（Noneの場合は全て）

        Returns:
            int: トレード数
        """
        pass

    @abstractmethod
    async def get_total_profit_loss(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> float:
        """
        期間内の総損益を取得

        Args:
            start_date: 開始日（Noneの場合は制限なし）
            end_date: 終了日（Noneの場合は制限なし）

        Returns:
            float: 総損益額
        """
        pass
