"""Stock リポジトリ インターフェース"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.domain.entities.stock import Stock, StockSummary


@dataclass(frozen=True)
class ScreenerFilter:
    """スクリーニングフィルター条件"""

    min_rs_rating: int = 80
    min_eps_growth_quarterly: float = 25.0
    min_eps_growth_annual: float = 25.0
    max_distance_from_52w_high: float = 15.0
    min_volume_ratio: float = 1.5
    min_canslim_score: int = 70
    min_market_cap: float | None = None  # 最小時価総額
    max_market_cap: float | None = None  # 最大時価総額
    symbols: list[str] | None = None  # 対象シンボルのリスト


@dataclass(frozen=True)
class ScreenerResult:
    """スクリーニング結果"""

    total_count: int
    stocks: list[StockSummary]


class StockRepository(ABC):
    """
    Stock リポジトリの抽象インターフェース

    株式銘柄データの取得・保存を抽象化する。
    Infrastructure層で具体的な実装を提供する。
    """

    @abstractmethod
    async def get_by_symbol(self, symbol: str) -> Stock | None:
        """
        シンボルで銘柄を取得

        Args:
            symbol: ティッカーシンボル（例: AAPL）

        Returns:
            Stock: 銘柄エンティティ、見つからない場合はNone
        """
        pass

    @abstractmethod
    async def get_by_symbols(self, symbols: list[str]) -> list[Stock]:
        """
        複数シンボルで銘柄を取得

        Args:
            symbols: ティッカーシンボルのリスト

        Returns:
            list[Stock]: 銘柄エンティティのリスト
        """
        pass

    @abstractmethod
    async def screen(
        self,
        filter_: ScreenerFilter,
        limit: int = 20,
        offset: int = 0,
    ) -> ScreenerResult:
        """
        CAN-SLIM条件でスクリーニング

        Args:
            filter_: スクリーニング条件
            limit: 取得件数
            offset: オフセット

        Returns:
            ScreenerResult: スクリーニング結果
        """
        pass

    @abstractmethod
    async def save(self, stock: Stock) -> None:
        """
        銘柄を保存

        Args:
            stock: 保存する銘柄エンティティ
        """
        pass

    @abstractmethod
    async def save_many(self, stocks: list[Stock]) -> None:
        """
        複数銘柄を一括保存

        Args:
            stocks: 保存する銘柄エンティティのリスト
        """
        pass

    @abstractmethod
    async def get_all_symbols(self) -> list[str]:
        """
        全シンボルを取得

        Returns:
            list[str]: 全ティッカーシンボルのリスト
        """
        pass

    @abstractmethod
    async def delete_by_symbol(self, symbol: str) -> bool:
        """
        シンボルで銘柄を削除

        Args:
            symbol: ティッカーシンボル

        Returns:
            bool: 削除成功したらTrue
        """
        pass
