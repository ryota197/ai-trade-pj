"""PostgreSQL StockMetrics リポジトリ"""

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from src.domain.entities import StockMetrics
from src.domain.repositories import StockMetricsRepository
from src.infrastructure.database.models import StockMetricsModel


class PostgresStockMetricsRepository(StockMetricsRepository):
    """計算指標リポジトリ実装"""

    def __init__(self, session: Session) -> None:
        self._session = session

    async def save(self, metrics: StockMetrics) -> None:
        """保存"""
        model = StockMetricsModel(
            symbol=metrics.symbol.upper(),
            eps_growth_quarterly=metrics.eps_growth_quarterly,
            eps_growth_annual=metrics.eps_growth_annual,
            institutional_ownership=metrics.institutional_ownership,
            relative_strength=metrics.relative_strength,
            rs_rating=metrics.rs_rating,
            canslim_score=metrics.canslim_score,
            calculated_at=metrics.calculated_at,
        )
        self._session.add(model)
        self._session.commit()

    async def get_latest(self, symbol: str) -> StockMetrics | None:
        """最新取得"""
        stmt = (
            select(StockMetricsModel)
            .where(StockMetricsModel.symbol == symbol.upper())
            .order_by(StockMetricsModel.calculated_at.desc())
            .limit(1)
        )
        model = self._session.scalars(stmt).first()

        if model is None:
            return None

        return self._to_entity(model)

    async def get_all_latest_relative_strength(self) -> list[tuple[str, float]]:
        """全銘柄の最新 relative_strength を取得"""
        # DISTINCT ON で各銘柄の最新レコードを取得（PostgreSQL専用）
        stmt = (
            select(StockMetricsModel.symbol, StockMetricsModel.relative_strength)
            .where(StockMetricsModel.relative_strength.isnot(None))
            .distinct(StockMetricsModel.symbol)
            .order_by(
                StockMetricsModel.symbol,
                StockMetricsModel.calculated_at.desc(),
            )
        )
        rows = self._session.execute(stmt).all()
        return [(row[0], float(row[1])) for row in rows]

    async def bulk_update_rs_rating(self, updates: list[tuple[str, int]]) -> int:
        """rs_ratingを一括更新（当日分）"""
        today = func.current_date()
        updated_count = 0

        for symbol, rs_rating in updates:
            stmt = (
                update(StockMetricsModel)
                .where(StockMetricsModel.symbol == symbol)
                .where(func.date(StockMetricsModel.calculated_at) == today)
                .values(rs_rating=rs_rating)
            )
            result = self._session.execute(stmt)
            updated_count += result.rowcount

        self._session.commit()
        return updated_count

    async def bulk_update_canslim_score(self, updates: list[tuple[str, int]]) -> int:
        """canslim_scoreを一括更新（当日分）"""
        today = func.current_date()
        updated_count = 0

        for symbol, canslim_score in updates:
            stmt = (
                update(StockMetricsModel)
                .where(StockMetricsModel.symbol == symbol)
                .where(func.date(StockMetricsModel.calculated_at) == today)
                .values(canslim_score=canslim_score)
            )
            result = self._session.execute(stmt)
            updated_count += result.rowcount

        self._session.commit()
        return updated_count

    def _to_entity(self, model: StockMetricsModel) -> StockMetrics:
        """モデルをエンティティに変換"""
        return StockMetrics(
            symbol=model.symbol,
            eps_growth_quarterly=(
                float(model.eps_growth_quarterly)
                if model.eps_growth_quarterly
                else None
            ),
            eps_growth_annual=(
                float(model.eps_growth_annual) if model.eps_growth_annual else None
            ),
            institutional_ownership=(
                float(model.institutional_ownership)
                if model.institutional_ownership
                else None
            ),
            relative_strength=(
                float(model.relative_strength) if model.relative_strength else None
            ),
            rs_rating=model.rs_rating,
            canslim_score=model.canslim_score,
            calculated_at=model.calculated_at,
        )
