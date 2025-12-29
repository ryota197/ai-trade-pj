"""Benchmark リポジトリ インターフェース"""

from abc import ABC, abstractmethod

from src.domain.entities.stock import MarketBenchmark


class BenchmarkRepository(ABC):
    """
    Benchmark リポジトリの抽象インターフェース

    市場ベンチマーク（S&P500, NASDAQ100）のパフォーマンスデータを扱う。
    Job 0 で更新、Job 1 で参照する。
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
    async def get_latest_performance_1y(self, symbol: str) -> float | None:
        """
        最新の1年パフォーマンスを取得（Job 1用の簡易メソッド）

        Args:
            symbol: 指数シンボル（例: "^GSPC"）

        Returns:
            float: 1年パフォーマンス（%）、見つからない場合はNone
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
