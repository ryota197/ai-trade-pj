"""PostgreSQL StockQuery リポジトリ"""

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from src.domain.entities import PriceSnapshot, StockIdentity, StockMetrics
from src.domain.repositories import (
    ScreenerFilter,
    ScreenerResult,
    StockData,
    StockQueryRepository,
)
from src.infrastructure.database.models import (
    StockMetricsModel,
    StockModel,
    StockPriceModel,
)


class PostgresStockQueryRepository(StockQueryRepository):
    """銘柄クエリリポジトリ実装（読み取り専用）"""

    def __init__(self, session: Session) -> None:
        self._session = session

    async def get_stock(self, symbol: str) -> StockData | None:
        """銘柄を集約して取得"""
        upper_symbol = symbol.upper()

        # 銘柄マスター取得
        stock_stmt = select(StockModel).where(StockModel.symbol == upper_symbol)
        stock_model = self._session.scalars(stock_stmt).first()

        if stock_model is None:
            return None

        # 最新価格取得
        price_stmt = (
            select(StockPriceModel)
            .where(StockPriceModel.symbol == upper_symbol)
            .order_by(StockPriceModel.recorded_at.desc())
            .limit(1)
        )
        price_model = self._session.scalars(price_stmt).first()

        # 最新指標取得
        metrics_stmt = (
            select(StockMetricsModel)
            .where(StockMetricsModel.symbol == upper_symbol)
            .order_by(StockMetricsModel.calculated_at.desc())
            .limit(1)
        )
        metrics_model = self._session.scalars(metrics_stmt).first()

        return StockData(
            identity=self._to_identity(stock_model),
            price=self._to_price(price_model) if price_model else None,
            metrics=self._to_metrics(metrics_model) if metrics_model else None,
        )

    async def get_stocks(self, symbols: list[str]) -> list[StockData]:
        """複数銘柄を集約して取得"""
        result = []
        for symbol in symbols:
            stock_data = await self.get_stock(symbol)
            if stock_data:
                result.append(stock_data)
        return result

    async def screen(
        self,
        filter_: ScreenerFilter,
        limit: int = 20,
        offset: int = 0,
    ) -> ScreenerResult:
        """CAN-SLIM条件でスクリーニング"""
        today = func.current_date()

        # 当日のメトリクスと価格をJOIN
        stmt = (
            select(StockModel, StockPriceModel, StockMetricsModel)
            .join(StockPriceModel, StockModel.symbol == StockPriceModel.symbol)
            .join(StockMetricsModel, StockModel.symbol == StockMetricsModel.symbol)
            .where(func.date(StockPriceModel.recorded_at) == today)
            .where(func.date(StockMetricsModel.calculated_at) == today)
            .where(StockMetricsModel.rs_rating.isnot(None))
            .where(StockMetricsModel.canslim_score.isnot(None))
        )

        # フィルター適用
        stmt = stmt.where(StockMetricsModel.rs_rating >= filter_.min_rs_rating)
        stmt = stmt.where(StockMetricsModel.canslim_score >= filter_.min_canslim_score)

        if filter_.min_eps_growth_quarterly > 0:
            stmt = stmt.where(
                (StockMetricsModel.eps_growth_quarterly >= filter_.min_eps_growth_quarterly)
                | (StockMetricsModel.eps_growth_quarterly.is_(None))
            )

        if filter_.min_eps_growth_annual > 0:
            stmt = stmt.where(
                (StockMetricsModel.eps_growth_annual >= filter_.min_eps_growth_annual)
                | (StockMetricsModel.eps_growth_annual.is_(None))
            )

        # トータル件数
        count_rows = self._session.execute(stmt).all()
        total_count = len(count_rows)

        # ソート・ページネーション
        stmt = (
            stmt.order_by(
                StockMetricsModel.canslim_score.desc(),
                StockMetricsModel.rs_rating.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        rows = self._session.execute(stmt).all()

        stocks = [
            StockData(
                identity=self._to_identity(row[0]),
                price=self._to_price(row[1]),
                metrics=self._to_metrics(row[2]),
            )
            for row in rows
        ]

        return ScreenerResult(total_count=total_count, stocks=stocks)

    async def get_all_for_canslim(self) -> list[StockData]:
        """CAN-SLIMスコア計算に必要な全銘柄を取得"""
        today = func.current_date()

        stmt = (
            select(StockModel, StockPriceModel, StockMetricsModel)
            .join(StockPriceModel, StockModel.symbol == StockPriceModel.symbol)
            .join(StockMetricsModel, StockModel.symbol == StockMetricsModel.symbol)
            .where(func.date(StockPriceModel.recorded_at) == today)
            .where(func.date(StockMetricsModel.calculated_at) == today)
            .where(StockMetricsModel.rs_rating.isnot(None))
        )

        rows = self._session.execute(stmt).all()

        return [
            StockData(
                identity=self._to_identity(row[0]),
                price=self._to_price(row[1]),
                metrics=self._to_metrics(row[2]),
            )
            for row in rows
        ]

    def _to_identity(self, model: StockModel) -> StockIdentity:
        return StockIdentity(
            symbol=model.symbol,
            name=model.name,
            industry=model.industry,
        )

    def _to_price(self, model: StockPriceModel) -> PriceSnapshot:
        return PriceSnapshot(
            symbol=model.symbol,
            price=float(model.price) if model.price else None,
            change_percent=float(model.change_percent) if model.change_percent else None,
            volume=model.volume,
            avg_volume_50d=model.avg_volume_50d,
            market_cap=model.market_cap,
            week_52_high=float(model.week_52_high) if model.week_52_high else None,
            week_52_low=float(model.week_52_low) if model.week_52_low else None,
            recorded_at=model.recorded_at,
        )

    def _to_metrics(self, model: StockMetricsModel) -> StockMetrics:
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
