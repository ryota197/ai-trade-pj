"""市場ベンチマーク リポジトリ インターフェース"""

from abc import ABC, abstractmethod

from src.domain.models import MarketBenchmark


class BenchmarkRepository(ABC):
    """
    市場ベンチマーク リポジトリ

    対応テーブル: market_benchmarks
    """

    @abstractmethod
    async def save(self, benchmark: MarketBenchmark) -> None:
        """
        ベンチマークを保存（UPSERT）

        同日のデータが存在する場合は上書き。

        Args:
            benchmark: 市場ベンチマーク
        """
        pass

    @abstractmethod
    async def get_latest(self, symbol: str) -> MarketBenchmark | None:
        """
        最新のベンチマークを取得

        Args:
            symbol: 指数シンボル（例: "^GSPC", "^NDX"）

        Returns:
            MarketBenchmark: 最新のベンチマーク、見つからない場合はNone
        """
        pass

    @abstractmethod
    async def get_latest_weighted_performance(self, symbol: str) -> float | None:
        """
        最新のIBD式加重パフォーマンスを取得（Job 1用）

        Args:
            symbol: 指数シンボル（例: "^GSPC"）

        Returns:
            float: IBD式加重パフォーマンス（%）、見つからない場合はNone
        """
        pass

    @abstractmethod
    async def get_all_latest(self) -> list[MarketBenchmark]:
        """
        全指数の最新ベンチマークを取得

        Returns:
            list[MarketBenchmark]: 最新のベンチマークリスト
        """
        pass
