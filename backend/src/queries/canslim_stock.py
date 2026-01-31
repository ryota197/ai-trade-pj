"""CAN-SLIM銘柄クエリ"""

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.models import CANSLIMStock
from src.services._lib import ScreeningCriteria


class CANSLIMStockQuery:
    """CAN-SLIM銘柄データアクセス"""

    def __init__(self, session: Session) -> None:
        self._session = session

    # === 取得系 ===

    def find_by_symbol_and_date(
        self, symbol: str, target_date: date
    ) -> CANSLIMStock | None:
        """シンボルと日付で取得"""
        stmt = select(CANSLIMStock).where(
            CANSLIMStock.symbol == symbol.upper(),
            CANSLIMStock.date == target_date,
        )
        return self._session.scalars(stmt).first()

    def find_all_by_date(self, target_date: date) -> list[CANSLIMStock]:
        """指定日の全銘柄を取得"""
        stmt = (
            select(CANSLIMStock)
            .where(CANSLIMStock.date == target_date)
            .order_by(CANSLIMStock.symbol)
        )
        return list(self._session.scalars(stmt).all())

    def find_by_criteria(
        self,
        target_date: date,
        criteria: ScreeningCriteria,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CANSLIMStock]:
        """条件でスクリーニング（計算完了銘柄のみ）"""
        stmt = (
            select(CANSLIMStock)
            .where(
                CANSLIMStock.date == target_date,
                CANSLIMStock.rs_rating.isnot(None),
                CANSLIMStock.canslim_score.isnot(None),
                CANSLIMStock.rs_rating >= criteria.min_rs_rating,
                CANSLIMStock.canslim_score >= criteria.min_canslim_score,
            )
            .order_by(CANSLIMStock.canslim_score.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self._session.scalars(stmt).all())

    def find_all_with_relative_strength(
        self, target_date: date
    ) -> list[CANSLIMStock]:
        """relative_strength が計算済みの全銘柄を取得（Job 2 用）"""
        stmt = (
            select(CANSLIMStock)
            .where(
                CANSLIMStock.date == target_date,
                CANSLIMStock.relative_strength.isnot(None),
            )
            .order_by(CANSLIMStock.symbol)
        )
        return list(self._session.scalars(stmt).all())

    def get_all_symbols(self) -> list[str]:
        """全シンボル一覧を取得"""
        stmt = select(CANSLIMStock.symbol).distinct()
        return list(self._session.scalars(stmt).all())

    # === 保存系 ===

    def save(self, stock: CANSLIMStock) -> None:
        """保存（UPSERT）"""
        values = self._to_dict(stock)
        stmt = insert(CANSLIMStock).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "date"],
            set_=values,
        )
        self._session.execute(stmt)
        self._session.commit()

    def save_all(self, stocks: list[CANSLIMStock]) -> None:
        """一括保存"""
        if not stocks:
            return

        for stock in stocks:
            values = self._to_dict(stock)
            stmt = insert(CANSLIMStock).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["symbol", "date"],
                set_=values,
            )
            self._session.execute(stmt)

        self._session.commit()

    # === 部分更新系 ===

    def update_rs_ratings(
        self,
        target_date: date,
        rs_ratings: dict[str, int],
    ) -> None:
        """RS Rating を一括更新（Job 2 用）"""
        for symbol, rs_rating in rs_ratings.items():
            stmt = (
                update(CANSLIMStock)
                .where(
                    CANSLIMStock.symbol == symbol,
                    CANSLIMStock.date == target_date,
                )
                .values(
                    rs_rating=rs_rating,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            self._session.execute(stmt)

        self._session.commit()

    def update_canslim_scores(
        self,
        target_date: date,
        scores: dict[str, dict[str, Any]],
    ) -> None:
        """CAN-SLIM スコアを一括更新（Job 3 用）"""
        for symbol, score_data in scores.items():
            stmt = (
                update(CANSLIMStock)
                .where(
                    CANSLIMStock.symbol == symbol,
                    CANSLIMStock.date == target_date,
                )
                .values(
                    canslim_score=score_data.get("canslim_score"),
                    score_c=score_data.get("score_c"),
                    score_a=score_data.get("score_a"),
                    score_n=score_data.get("score_n"),
                    score_s=score_data.get("score_s"),
                    score_l=score_data.get("score_l"),
                    score_i=score_data.get("score_i"),
                    score_m=score_data.get("score_m"),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            self._session.execute(stmt)

        self._session.commit()

    # === ヘルパーメソッド ===

    def _to_dict(self, stock: CANSLIMStock) -> dict[str, Any]:
        """モデルを辞書に変換（INSERT/UPDATE用）"""
        return {
            "symbol": stock.symbol.upper() if stock.symbol else None,
            "date": stock.date,
            "name": stock.name,
            "industry": stock.industry,
            "price": float(stock.price) if stock.price else None,
            "change_percent": (
                float(stock.change_percent) if stock.change_percent else None
            ),
            "volume": stock.volume,
            "avg_volume_50d": stock.avg_volume_50d,
            "market_cap": stock.market_cap,
            "week_52_high": (
                float(stock.week_52_high) if stock.week_52_high else None
            ),
            "week_52_low": float(stock.week_52_low) if stock.week_52_low else None,
            "eps_growth_quarterly": (
                float(stock.eps_growth_quarterly)
                if stock.eps_growth_quarterly
                else None
            ),
            "eps_growth_annual": (
                float(stock.eps_growth_annual) if stock.eps_growth_annual else None
            ),
            "institutional_ownership": (
                float(stock.institutional_ownership)
                if stock.institutional_ownership
                else None
            ),
            "relative_strength": (
                float(stock.relative_strength) if stock.relative_strength else None
            ),
            "rs_rating": stock.rs_rating,
            "canslim_score": stock.canslim_score,
            "score_c": stock.score_c,
            "score_a": stock.score_a,
            "score_n": stock.score_n,
            "score_s": stock.score_s,
            "score_l": stock.score_l,
            "score_i": stock.score_i,
            "score_m": stock.score_m,
            "updated_at": datetime.now(timezone.utc),
        }
