"""Stock リポジトリ インターフェース（正規化構造対応）"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.domain.entities.stock import (
    Stock,
    StockIdentity,
    StockMetrics,
    StockSummary,
    PriceSnapshot,
)


@dataclass(frozen=True)
class ScreenerFilter:
    """スクリーニングフィルター条件"""

    min_rs_rating: int = 80
    min_eps_growth_quarterly: float = 25.0
    min_eps_growth_annual: float = 25.0
    max_distance_from_52w_high: float = 15.0
    min_volume_ratio: float = 1.5
    min_canslim_score: int = 70
    min_market_cap: float | None = None
    max_market_cap: float | None = None
    symbols: list[str] | None = None


@dataclass(frozen=True)
class ScreenerResult:
    """スクリーニング結果"""

    total_count: int
    stocks: list[StockSummary]


class StockRepository(ABC):
    """
    Stock リポジトリの抽象インターフェース

    正規化されたテーブル（stocks, stock_prices, stock_metrics）を扱う。
    """

    # ----- 銘柄マスター操作 -----

    @abstractmethod
    async def save_identity(self, identity: StockIdentity) -> None:
        """
        銘柄マスターを保存（UPSERT）

        Args:
            identity: 銘柄マスター情報
        """
        pass

    @abstractmethod
    async def get_identity(self, symbol: str) -> StockIdentity | None:
        """
        銘柄マスターを取得

        Args:
            symbol: ティッカーシンボル

        Returns:
            StockIdentity: 銘柄マスター、見つからない場合はNone
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

    # ----- 価格スナップショット操作 -----

    @abstractmethod
    async def save_price(self, price: PriceSnapshot) -> None:
        """
        価格スナップショットを保存

        Args:
            price: 価格スナップショット
        """
        pass

    @abstractmethod
    async def get_latest_price(self, symbol: str) -> PriceSnapshot | None:
        """
        最新の価格スナップショットを取得

        Args:
            symbol: ティッカーシンボル

        Returns:
            PriceSnapshot: 最新の価格、見つからない場合はNone
        """
        pass

    # ----- 計算指標操作 -----

    @abstractmethod
    async def save_metrics(self, metrics: StockMetrics) -> None:
        """
        計算指標を保存

        Args:
            metrics: 計算指標
        """
        pass

    @abstractmethod
    async def get_latest_metrics(self, symbol: str) -> StockMetrics | None:
        """
        最新の計算指標を取得

        Args:
            symbol: ティッカーシンボル

        Returns:
            StockMetrics: 最新の指標、見つからない場合はNone
        """
        pass

    # ----- 集約操作 -----

    @abstractmethod
    async def get_stock(self, symbol: str) -> Stock | None:
        """
        銘柄を集約して取得（identity + 最新price + 最新metrics）

        Args:
            symbol: ティッカーシンボル

        Returns:
            Stock: 集約された銘柄エンティティ
        """
        pass

    @abstractmethod
    async def get_stocks(self, symbols: list[str]) -> list[Stock]:
        """
        複数銘柄を集約して取得

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

    # ----- 一括保存操作（Job 1用） -----

    @abstractmethod
    async def save_stock_data(
        self,
        identity: StockIdentity,
        price: PriceSnapshot,
        metrics: StockMetrics,
    ) -> None:
        """
        銘柄データを一括保存（Job 1用）

        3テーブルにまとめて保存する。トランザクションで実行。

        Args:
            identity: 銘柄マスター
            price: 価格スナップショット
            metrics: 計算指標
        """
        pass

    # ----- Job 2用メソッド -----

    @abstractmethod
    async def get_all_with_relative_strength(self) -> list[tuple[str, float]]:
        """
        relative_strengthを持つ全銘柄を取得（Job 2用）

        当日の stock_metrics から取得。

        Returns:
            list[tuple[str, float]]: (symbol, relative_strength) のリスト
        """
        pass

    @abstractmethod
    async def bulk_update_rs_rating(self, updates: list[tuple[str, int]]) -> int:
        """
        rs_ratingを一括更新（Job 2用）

        当日の stock_metrics を更新。

        Args:
            updates: (symbol, rs_rating) のリスト

        Returns:
            int: 更新件数
        """
        pass

    # ----- Job 3用メソッド -----

    @abstractmethod
    async def get_all_for_canslim(self) -> list[Stock]:
        """
        CAN-SLIMスコア計算に必要な全銘柄を取得（Job 3用）

        Returns:
            list[Stock]: rs_ratingが設定されている銘柄のリスト
        """
        pass

    @abstractmethod
    async def bulk_update_canslim_score(self, updates: list[tuple[str, int]]) -> int:
        """
        canslim_scoreを一括更新（Job 3用）

        当日の stock_metrics を更新。

        Args:
            updates: (symbol, canslim_score) のリスト

        Returns:
            int: 更新件数
        """
        pass

    # ----- 削除操作 -----

    @abstractmethod
    async def delete_by_symbol(self, symbol: str) -> bool:
        """
        シンボルで銘柄を削除（CASCADE）

        Args:
            symbol: ティッカーシンボル

        Returns:
            bool: 削除成功したらTrue
        """
        pass
