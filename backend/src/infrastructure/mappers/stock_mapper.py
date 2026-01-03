"""Stock Mapper - Entity ↔ Model 変換"""

from datetime import datetime, timezone

from src.domain.entities.stock import Stock, StockSummary
from src.infrastructure.database.models.stock_model import StockModel


class StockMapper:
    """
    Stock Entity ↔ StockModel の変換

    責務:
        - SQLAlchemy Model から Domain Entity への変換
        - Domain Entity から SQLAlchemy Model への変換
    """

    @staticmethod
    def to_entity(model: StockModel) -> Stock:
        """
        SQLAlchemyモデルをドメインエンティティに変換

        Args:
            model: SQLAlchemyモデル

        Returns:
            Stock: ドメインエンティティ
        """
        return Stock(
            symbol=model.symbol,
            name=model.name,
            industry=model.industry,
            price=float(model.price) if model.price else None,
            change_percent=float(model.change_percent) if model.change_percent else None,
            volume=model.volume,
            avg_volume_50d=model.avg_volume_50d,
            market_cap=model.market_cap,
            week_52_high=float(model.week_52_high) if model.week_52_high else None,
            week_52_low=float(model.week_52_low) if model.week_52_low else None,
            eps_growth_quarterly=float(model.eps_growth_quarterly)
            if model.eps_growth_quarterly
            else None,
            eps_growth_annual=float(model.eps_growth_annual)
            if model.eps_growth_annual
            else None,
            institutional_ownership=float(model.institutional_ownership)
            if model.institutional_ownership
            else None,
            relative_strength=float(model.relative_strength)
            if model.relative_strength
            else None,
            rs_rating=model.rs_rating,
            canslim_score=model.canslim_score,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_summary(model: StockModel) -> StockSummary:
        """
        SQLAlchemyモデルをStockSummaryに変換

        Args:
            model: SQLAlchemyモデル

        Returns:
            StockSummary: サマリー
        """
        return StockSummary(
            symbol=model.symbol,
            name=model.name,
            price=float(model.price) if model.price else None,
            change_percent=float(model.change_percent) if model.change_percent else None,
            rs_rating=model.rs_rating,
            canslim_score=model.canslim_score,
        )

    @staticmethod
    def to_model(
        entity: Stock,
        existing: StockModel | None = None,
    ) -> StockModel:
        """
        ドメインエンティティをSQLAlchemyモデルに変換

        Args:
            entity: ドメインエンティティ
            existing: 既存のモデル（更新時）

        Returns:
            StockModel: SQLAlchemyモデル
        """
        now = datetime.now(timezone.utc)

        if existing:
            # 既存レコードを更新
            existing.name = entity.name
            existing.industry = entity.industry
            existing.price = entity.price
            existing.change_percent = entity.change_percent
            existing.volume = entity.volume
            existing.avg_volume_50d = entity.avg_volume_50d
            existing.market_cap = entity.market_cap
            existing.week_52_high = entity.week_52_high
            existing.week_52_low = entity.week_52_low
            existing.eps_growth_quarterly = entity.eps_growth_quarterly
            existing.eps_growth_annual = entity.eps_growth_annual
            existing.institutional_ownership = entity.institutional_ownership
            existing.relative_strength = entity.relative_strength
            existing.rs_rating = entity.rs_rating
            existing.canslim_score = entity.canslim_score
            existing.updated_at = now
            return existing
        else:
            # 新規作成
            return StockModel(
                symbol=entity.symbol.upper(),
                name=entity.name,
                industry=entity.industry,
                price=entity.price,
                change_percent=entity.change_percent,
                volume=entity.volume,
                avg_volume_50d=entity.avg_volume_50d,
                market_cap=entity.market_cap,
                week_52_high=entity.week_52_high,
                week_52_low=entity.week_52_low,
                eps_growth_quarterly=entity.eps_growth_quarterly,
                eps_growth_annual=entity.eps_growth_annual,
                institutional_ownership=entity.institutional_ownership,
                relative_strength=entity.relative_strength,
                rs_rating=entity.rs_rating,
                canslim_score=entity.canslim_score,
                updated_at=now,
                created_at=now,
            )
