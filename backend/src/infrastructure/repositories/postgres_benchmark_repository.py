"""PostgreSQL Benchmark リポジトリ"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.entities import MarketBenchmark
from src.domain.repositories import BenchmarkRepository
from src.infrastructure.database.models import MarketBenchmarkModel


class PostgresBenchmarkRepository(BenchmarkRepository):
    """市場ベンチマークリポジトリ実装"""

    def __init__(self, session: Session) -> None:
        self._session = session

    async def save(self, benchmark: MarketBenchmark) -> None:
        """保存（UPSERT）"""
        model = MarketBenchmarkModel(
            symbol=benchmark.symbol,
            performance_1y=benchmark.performance_1y,
            performance_9m=benchmark.performance_9m,
            performance_6m=benchmark.performance_6m,
            performance_3m=benchmark.performance_3m,
            performance_1m=benchmark.performance_1m,
            weighted_performance=benchmark.weighted_performance,
            recorded_at=benchmark.recorded_at,
        )
        self._session.add(model)
        self._session.commit()

    async def get_latest(self, symbol: str) -> MarketBenchmark | None:
        """最新取得"""
        stmt = (
            select(MarketBenchmarkModel)
            .where(MarketBenchmarkModel.symbol == symbol)
            .order_by(MarketBenchmarkModel.recorded_at.desc())
            .limit(1)
        )
        model = self._session.scalars(stmt).first()

        if model is None:
            return None

        return self._to_entity(model)

    async def get_latest_weighted_performance(self, symbol: str) -> float | None:
        """最新のIBD式加重パフォーマンス取得"""
        stmt = (
            select(MarketBenchmarkModel.weighted_performance)
            .where(MarketBenchmarkModel.symbol == symbol)
            .order_by(MarketBenchmarkModel.recorded_at.desc())
            .limit(1)
        )
        result = self._session.scalars(stmt).first()
        return float(result) if result else None

    async def get_all_latest(self) -> list[MarketBenchmark]:
        """全指数の最新ベンチマークを取得"""
        # サブクエリで各シンボルの最新日時を取得
        from sqlalchemy import func

        subq = (
            select(
                MarketBenchmarkModel.symbol,
                func.max(MarketBenchmarkModel.recorded_at).label("max_recorded_at"),
            )
            .group_by(MarketBenchmarkModel.symbol)
            .subquery()
        )

        stmt = select(MarketBenchmarkModel).join(
            subq,
            (MarketBenchmarkModel.symbol == subq.c.symbol)
            & (MarketBenchmarkModel.recorded_at == subq.c.max_recorded_at),
        )
        models = self._session.scalars(stmt).all()

        return [self._to_entity(model) for model in models]

    def _to_entity(self, model: MarketBenchmarkModel) -> MarketBenchmark:
        """モデルをエンティティに変換"""
        return MarketBenchmark(
            symbol=model.symbol,
            performance_1y=(
                float(model.performance_1y) if model.performance_1y else None
            ),
            performance_9m=(
                float(model.performance_9m) if model.performance_9m else None
            ),
            performance_6m=(
                float(model.performance_6m) if model.performance_6m else None
            ),
            performance_3m=(
                float(model.performance_3m) if model.performance_3m else None
            ),
            performance_1m=(
                float(model.performance_1m) if model.performance_1m else None
            ),
            weighted_performance=(
                float(model.weighted_performance)
                if model.weighted_performance
                else None
            ),
            recorded_at=model.recorded_at,
        )
