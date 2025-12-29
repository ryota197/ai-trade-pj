"""銘柄クエリ リポジトリ インターフェース"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.domain.entities import PriceSnapshot, StockIdentity, StockMetrics


@dataclass
class StockData:
    """クエリ結果用のデータクラス"""

    identity: StockIdentity
    price: PriceSnapshot | None
    metrics: StockMetrics | None


@dataclass(frozen=True)
class ScreenerFilter:
    """スクリーニングフィルター条件"""

    min_rs_rating: int = 80
    min_eps_growth_quarterly: float = 25.0
    min_eps_growth_annual: float = 25.0
    max_distance_from_52w_high: float = 15.0
    min_volume_ratio: float = 1.5
    min_canslim_score: int = 70


@dataclass
class ScreenerResult:
    """スクリーニング結果"""

    total_count: int
    stocks: list[StockData]


class StockQueryRepository(ABC):
    """
    銘柄クエリ リポジトリ（読み取り専用）

    複数テーブルのJOIN/集約操作を担当。
    """

    @abstractmethod
    async def get_stock(self, symbol: str) -> StockData | None:
        """銘柄を集約して取得（identity + price + metrics）"""
        pass

    @abstractmethod
    async def get_stocks(self, symbols: list[str]) -> list[StockData]:
        """複数銘柄を集約して取得"""
        pass

    @abstractmethod
    async def screen(
        self,
        filter_: ScreenerFilter,
        limit: int = 20,
        offset: int = 0,
    ) -> ScreenerResult:
        """CAN-SLIM条件でスクリーニング"""
        pass

    @abstractmethod
    async def get_all_for_canslim(self) -> list[StockData]:
        """CAN-SLIMスコア計算に必要な全銘柄を取得（Job 3用）"""
        pass
