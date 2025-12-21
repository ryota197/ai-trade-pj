"""PostgreSQL スクリーナーリポジトリ"""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.domain.entities.stock import Stock, StockSummary
from src.domain.repositories.stock_repository import (
    ScreenerFilter,
    ScreenerResult,
    StockRepository,
)
from src.infrastructure.database.models.screener_result_model import ScreenerResultModel
from src.infrastructure.mappers.stock_model_mapper import StockModelMapper


class PostgresScreenerRepository(StockRepository):
    """
    PostgreSQLによるスクリーナーリポジトリ実装

    StockRepositoryインターフェースを実装し、
    スクリーニング結果をPostgreSQLに保存・取得する。

    責務:
        - 純粋なCRUD操作
        - スクリーニングクエリの実行

    Note:
        Model ↔ Entity の変換は StockModelMapper に委譲している。
    """

    def __init__(
        self,
        session: Session,
        mapper: StockModelMapper | None = None,
    ) -> None:
        self._session = session
        self._mapper = mapper or StockModelMapper()

    async def get_by_symbol(self, symbol: str) -> Stock | None:
        """
        シンボルで銘柄を取得

        Args:
            symbol: ティッカーシンボル

        Returns:
            Stock: 銘柄エンティティ、見つからない場合はNone
        """
        stmt = select(ScreenerResultModel).where(
            ScreenerResultModel.symbol == symbol.upper()
        )
        model = self._session.scalars(stmt).first()

        if model is None:
            return None

        return self._mapper.to_entity(model)

    async def get_by_symbols(self, symbols: list[str]) -> list[Stock]:
        """
        複数シンボルで銘柄を取得

        Args:
            symbols: ティッカーシンボルのリスト

        Returns:
            list[Stock]: 銘柄エンティティのリスト
        """
        upper_symbols = [s.upper() for s in symbols]
        stmt = select(ScreenerResultModel).where(
            ScreenerResultModel.symbol.in_(upper_symbols)
        )
        models = self._session.scalars(stmt).all()

        return [self._mapper.to_entity(model) for model in models]

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
        # ベースクエリ
        stmt = select(ScreenerResultModel)

        # フィルター適用
        stmt = stmt.where(ScreenerResultModel.rs_rating >= filter_.min_rs_rating)
        stmt = stmt.where(
            ScreenerResultModel.canslim_total_score >= filter_.min_canslim_score
        )

        # EPS成長率フィルター（NULLを許容）
        if filter_.min_eps_growth_quarterly > 0:
            stmt = stmt.where(
                (ScreenerResultModel.eps_growth_quarterly >= filter_.min_eps_growth_quarterly)
                | (ScreenerResultModel.eps_growth_quarterly.is_(None))
            )

        if filter_.min_eps_growth_annual > 0:
            stmt = stmt.where(
                (ScreenerResultModel.eps_growth_annual >= filter_.min_eps_growth_annual)
                | (ScreenerResultModel.eps_growth_annual.is_(None))
            )

        # 時価総額フィルター
        if filter_.min_market_cap is not None:
            stmt = stmt.where(
                ScreenerResultModel.market_cap >= filter_.min_market_cap
            )

        if filter_.max_market_cap is not None:
            stmt = stmt.where(
                ScreenerResultModel.market_cap <= filter_.max_market_cap
            )

        # シンボル指定
        if filter_.symbols:
            upper_symbols = [s.upper() for s in filter_.symbols]
            stmt = stmt.where(ScreenerResultModel.symbol.in_(upper_symbols))

        # トータル件数取得
        count_stmt = select(ScreenerResultModel.id).where(stmt.whereclause)
        total_count = len(self._session.scalars(count_stmt).all())

        # ソート・ページネーション
        stmt = (
            stmt.order_by(
                ScreenerResultModel.canslim_total_score.desc(),
                ScreenerResultModel.rs_rating.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        models = self._session.scalars(stmt).all()

        # StockSummaryに変換
        stocks = [
            StockSummary(
                symbol=model.symbol,
                name=model.name,
                price=float(model.price),
                change_percent=float(model.change_percent),
                rs_rating=model.rs_rating,
                canslim_total_score=model.canslim_total_score,
            )
            for model in models
        ]

        return ScreenerResult(total_count=total_count, stocks=stocks)

    async def save(self, stock: Stock) -> None:
        """
        銘柄を保存

        Args:
            stock: 保存する銘柄エンティティ
        """
        # 既存レコードをチェック
        stmt = select(ScreenerResultModel).where(
            ScreenerResultModel.symbol == stock.symbol.upper()
        )
        existing = self._session.scalars(stmt).first()

        # マッパーを使用してモデルに変換
        model = self._mapper.to_model(stock, existing)

        if not existing:
            self._session.add(model)

        self._session.commit()

    async def save_many(self, stocks: list[Stock]) -> None:
        """
        複数銘柄を一括保存

        Args:
            stocks: 保存する銘柄エンティティのリスト
        """
        for stock in stocks:
            await self.save(stock)

    async def get_all_symbols(self) -> list[str]:
        """
        全シンボルを取得

        Returns:
            list[str]: 全ティッカーシンボルのリスト
        """
        stmt = select(ScreenerResultModel.symbol).distinct()
        return list(self._session.scalars(stmt).all())

    async def delete_by_symbol(self, symbol: str) -> bool:
        """
        シンボルで銘柄を削除

        Args:
            symbol: ティッカーシンボル

        Returns:
            bool: 削除成功したらTrue
        """
        stmt = delete(ScreenerResultModel).where(
            ScreenerResultModel.symbol == symbol.upper()
        )
        result = self._session.execute(stmt)
        self._session.commit()

        return result.rowcount > 0
