"""PostgreSQL Stock リポジトリ"""

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.domain.entities.stock import Stock, StockSummary
from src.domain.repositories.stock_repository import (
    ScreenerFilter,
    ScreenerResult,
    StockRepository,
)
from src.infrastructure.database.models.stock_model import StockModel
from src.infrastructure.mappers.stock_mapper import StockMapper


class PostgresStockRepository(StockRepository):
    """
    PostgreSQLによるStockリポジトリ実装

    StockRepositoryインターフェースを実装し、
    銘柄データをPostgreSQLに保存・取得する。
    """

    def __init__(
        self,
        session: Session,
        mapper: StockMapper | None = None,
    ) -> None:
        self._session = session
        self._mapper = mapper or StockMapper()

    async def get_by_symbol(self, symbol: str) -> Stock | None:
        """シンボルで銘柄を取得"""
        stmt = select(StockModel).where(StockModel.symbol == symbol.upper())
        model = self._session.scalars(stmt).first()

        if model is None:
            return None

        return self._mapper.to_entity(model)

    async def get_by_symbols(self, symbols: list[str]) -> list[Stock]:
        """複数シンボルで銘柄を取得"""
        upper_symbols = [s.upper() for s in symbols]
        stmt = select(StockModel).where(StockModel.symbol.in_(upper_symbols))
        models = self._session.scalars(stmt).all()

        return [self._mapper.to_entity(model) for model in models]

    async def screen(
        self,
        filter_: ScreenerFilter,
        limit: int = 20,
        offset: int = 0,
    ) -> ScreenerResult:
        """CAN-SLIM条件でスクリーニング"""
        # ベースクエリ
        stmt = select(StockModel)

        # rs_rating, canslim_score が NULL でないものだけ対象
        stmt = stmt.where(StockModel.rs_rating.isnot(None))
        stmt = stmt.where(StockModel.canslim_score.isnot(None))

        # フィルター適用
        stmt = stmt.where(StockModel.rs_rating >= filter_.min_rs_rating)
        stmt = stmt.where(StockModel.canslim_score >= filter_.min_canslim_score)

        # EPS成長率フィルター（NULLを許容）
        if filter_.min_eps_growth_quarterly > 0:
            stmt = stmt.where(
                (StockModel.eps_growth_quarterly >= filter_.min_eps_growth_quarterly)
                | (StockModel.eps_growth_quarterly.is_(None))
            )

        if filter_.min_eps_growth_annual > 0:
            stmt = stmt.where(
                (StockModel.eps_growth_annual >= filter_.min_eps_growth_annual)
                | (StockModel.eps_growth_annual.is_(None))
            )

        # 時価総額フィルター
        if filter_.min_market_cap is not None:
            stmt = stmt.where(StockModel.market_cap >= filter_.min_market_cap)

        if filter_.max_market_cap is not None:
            stmt = stmt.where(StockModel.market_cap <= filter_.max_market_cap)

        # シンボル指定
        if filter_.symbols:
            upper_symbols = [s.upper() for s in filter_.symbols]
            stmt = stmt.where(StockModel.symbol.in_(upper_symbols))

        # トータル件数取得
        count_stmt = select(StockModel.id).where(stmt.whereclause)
        total_count = len(self._session.scalars(count_stmt).all())

        # ソート・ページネーション
        stmt = (
            stmt.order_by(
                StockModel.canslim_score.desc(),
                StockModel.rs_rating.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        models = self._session.scalars(stmt).all()

        # StockSummaryに変換
        stocks = [self._mapper.to_summary(model) for model in models]

        return ScreenerResult(total_count=total_count, stocks=stocks)

    async def save(self, stock: Stock) -> None:
        """銘柄を保存（UPSERT）"""
        # 既存レコードをチェック
        stmt = select(StockModel).where(StockModel.symbol == stock.symbol.upper())
        existing = self._session.scalars(stmt).first()

        # マッパーを使用してモデルに変換
        model = self._mapper.to_model(stock, existing)

        if not existing:
            self._session.add(model)

        self._session.commit()

    async def save_many(self, stocks: list[Stock]) -> None:
        """複数銘柄を一括保存"""
        for stock in stocks:
            await self.save(stock)

    async def get_all_symbols(self) -> list[str]:
        """全シンボルを取得"""
        stmt = select(StockModel.symbol).distinct()
        return list(self._session.scalars(stmt).all())

    async def delete_by_symbol(self, symbol: str) -> bool:
        """シンボルで銘柄を削除"""
        stmt = delete(StockModel).where(StockModel.symbol == symbol.upper())
        result = self._session.execute(stmt)
        self._session.commit()

        return result.rowcount > 0

    # ----- Job 2, 3 用メソッド -----

    async def get_all_with_relative_strength(self) -> list[tuple[str, float]]:
        """relative_strengthを持つ全銘柄を取得（Job 2用）"""
        stmt = select(StockModel.symbol, StockModel.relative_strength).where(
            StockModel.relative_strength.isnot(None)
        )
        rows = self._session.execute(stmt).all()
        return [(row[0], float(row[1])) for row in rows]

    async def bulk_update_rs_rating(self, updates: list[tuple[str, int]]) -> int:
        """rs_ratingを一括更新（Job 2用）"""
        updated_count = 0
        for symbol, rs_rating in updates:
            stmt = (
                update(StockModel)
                .where(StockModel.symbol == symbol)
                .values(rs_rating=rs_rating)
            )
            result = self._session.execute(stmt)
            updated_count += result.rowcount

        self._session.commit()
        return updated_count

    async def get_all_for_canslim(self) -> list[Stock]:
        """CAN-SLIMスコア計算に必要な全銘柄を取得（Job 3用）"""
        stmt = select(StockModel).where(StockModel.rs_rating.isnot(None))
        models = self._session.scalars(stmt).all()
        return [self._mapper.to_entity(model) for model in models]

    async def bulk_update_canslim_score(self, updates: list[tuple[str, int]]) -> int:
        """canslim_scoreを一括更新（Job 3用）"""
        updated_count = 0
        for symbol, canslim_score in updates:
            stmt = (
                update(StockModel)
                .where(StockModel.symbol == symbol)
                .values(canslim_score=canslim_score)
            )
            result = self._session.execute(stmt)
            updated_count += result.rowcount

        self._session.commit()
        return updated_count
