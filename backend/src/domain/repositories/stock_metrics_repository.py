"""計算指標 リポジトリ インターフェース"""

from abc import ABC, abstractmethod

from src.domain.entities import StockMetrics


class StockMetricsRepository(ABC):
    """
    計算指標 リポジトリ

    対応テーブル: stock_metrics
    """

    @abstractmethod
    async def save(self, metrics: StockMetrics) -> None:
        """保存"""
        pass

    @abstractmethod
    async def get_latest(self, symbol: str) -> StockMetrics | None:
        """最新取得"""
        pass

    # ----- Job 2用 -----

    @abstractmethod
    async def get_all_latest_relative_strength(self) -> list[tuple[str, float]]:
        """
        全銘柄の最新 relative_strength を取得

        各銘柄の最新レコードから relative_strength を取得する。
        当日分だけでなく、全追跡銘柄を母集団としてパーセンタイル計算するため。

        Returns:
            list[tuple[str, float]]: [(symbol, relative_strength), ...]
        """
        pass

    @abstractmethod
    async def bulk_update_rs_rating(self, updates: list[tuple[str, int]]) -> int:
        """rs_ratingを一括更新"""
        pass

    # ----- Job 3用 -----

    @abstractmethod
    async def bulk_update_canslim_score(self, updates: list[tuple[str, int]]) -> int:
        """canslim_scoreを一括更新"""
        pass
