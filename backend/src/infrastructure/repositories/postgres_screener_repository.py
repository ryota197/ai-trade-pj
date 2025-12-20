"""PostgreSQL スクリーナーリポジトリ"""

import json
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.domain.entities.stock import Stock, StockSummary
from src.domain.repositories.stock_repository import (
    ScreenerFilter,
    ScreenerResult,
    StockRepository,
)
from src.domain.value_objects.canslim_score import CANSLIMScore
from src.infrastructure.database.models.screener_result_model import ScreenerResultModel


class PostgresScreenerRepository(StockRepository):
    """
    PostgreSQLによるスクリーナーリポジトリ実装

    StockRepositoryインターフェースを実装し、
    スクリーニング結果をPostgreSQLに保存・取得する。
    """

    def __init__(self, session: Session) -> None:
        self._session = session

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

        return self._model_to_entity(model)

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

        return [self._model_to_entity(model) for model in models]

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

        # CAN-SLIMスコアをJSON化
        canslim_detail = None
        if stock.canslim_score:
            canslim_detail = json.dumps(
                {
                    "c_score": stock.canslim_score.c_score.score,
                    "a_score": stock.canslim_score.a_score.score,
                    "n_score": stock.canslim_score.n_score.score,
                    "s_score": stock.canslim_score.s_score.score,
                    "l_score": stock.canslim_score.l_score.score,
                    "i_score": stock.canslim_score.i_score.score,
                }
            )

        if existing:
            # 更新
            existing.name = stock.name
            existing.price = stock.price
            existing.change_percent = stock.change_percent
            existing.volume = stock.volume
            existing.avg_volume = stock.avg_volume
            existing.market_cap = stock.market_cap
            existing.pe_ratio = stock.pe_ratio
            existing.week_52_high = stock.week_52_high
            existing.week_52_low = stock.week_52_low
            existing.eps_growth_quarterly = stock.eps_growth_quarterly
            existing.eps_growth_annual = stock.eps_growth_annual
            existing.rs_rating = stock.rs_rating
            existing.institutional_ownership = stock.institutional_ownership
            existing.canslim_total_score = (
                stock.canslim_score.total_score if stock.canslim_score else 0
            )
            existing.canslim_detail = canslim_detail
            existing.updated_at = datetime.now()
        else:
            # 新規作成
            model = ScreenerResultModel(
                symbol=stock.symbol.upper(),
                name=stock.name,
                price=stock.price,
                change_percent=stock.change_percent,
                volume=stock.volume,
                avg_volume=stock.avg_volume,
                market_cap=stock.market_cap,
                pe_ratio=stock.pe_ratio,
                week_52_high=stock.week_52_high,
                week_52_low=stock.week_52_low,
                eps_growth_quarterly=stock.eps_growth_quarterly,
                eps_growth_annual=stock.eps_growth_annual,
                rs_rating=stock.rs_rating,
                institutional_ownership=stock.institutional_ownership,
                canslim_total_score=(
                    stock.canslim_score.total_score if stock.canslim_score else 0
                ),
                canslim_detail=canslim_detail,
            )
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

    def _model_to_entity(self, model: ScreenerResultModel) -> Stock:
        """
        SQLAlchemyモデルをドメインエンティティに変換

        Args:
            model: SQLAlchemyモデル

        Returns:
            Stock: ドメインエンティティ
        """
        # CAN-SLIMスコアを復元
        canslim_score = None
        if model.canslim_detail:
            try:
                detail = json.loads(model.canslim_detail)
                # 簡易的に復元（詳細情報は失われる）
                canslim_score = CANSLIMScore.calculate(
                    eps_growth_quarterly=float(model.eps_growth_quarterly)
                    if model.eps_growth_quarterly
                    else None,
                    eps_growth_annual=float(model.eps_growth_annual)
                    if model.eps_growth_annual
                    else None,
                    distance_from_52w_high=self._calc_distance_from_high(
                        float(model.price), float(model.week_52_high)
                    ),
                    volume_ratio=model.volume / model.avg_volume
                    if model.avg_volume > 0
                    else 0,
                    rs_rating=model.rs_rating,
                    institutional_ownership=float(model.institutional_ownership)
                    if model.institutional_ownership
                    else None,
                )
            except Exception:
                pass

        return Stock(
            symbol=model.symbol,
            name=model.name,
            price=float(model.price),
            change_percent=float(model.change_percent),
            volume=model.volume,
            avg_volume=model.avg_volume,
            market_cap=float(model.market_cap) if model.market_cap else None,
            pe_ratio=float(model.pe_ratio) if model.pe_ratio else None,
            week_52_high=float(model.week_52_high),
            week_52_low=float(model.week_52_low),
            eps_growth_quarterly=float(model.eps_growth_quarterly)
            if model.eps_growth_quarterly
            else None,
            eps_growth_annual=float(model.eps_growth_annual)
            if model.eps_growth_annual
            else None,
            rs_rating=model.rs_rating,
            institutional_ownership=float(model.institutional_ownership)
            if model.institutional_ownership
            else None,
            canslim_score=canslim_score,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _calc_distance_from_high(price: float, week_52_high: float) -> float:
        """52週高値からの乖離率を計算"""
        if week_52_high == 0:
            return 0.0
        return ((week_52_high - price) / week_52_high) * 100
