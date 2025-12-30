"""Stock Model Mapper"""

import json
from datetime import datetime

from src.domain.entities.stock import Stock
from src.domain.models import CANSLIMScore
from src.infrastructure.database.models.screener_result_model import ScreenerResultModel


class StockModelMapper:
    """
    Stock Entity ↔ ScreenerResultModel の変換

    責務:
        - SQLAlchemy Model から Domain Entity への変換
        - Domain Entity から SQLAlchemy Model への変換
        - CANSLIMScore の JSON シリアライズ/デシリアライズ

    Note:
        リポジトリから変換ロジックを分離することで、
        リポジトリの責務を純粋なCRUD操作に限定する。
    """

    @staticmethod
    def to_entity(model: ScreenerResultModel) -> Stock:
        """
        SQLAlchemyモデルをドメインエンティティに変換

        Args:
            model: SQLAlchemyモデル

        Returns:
            Stock: ドメインエンティティ
        """
        # CAN-SLIMスコアを復元（再計算なし）
        canslim_score = None
        if model.canslim_detail:
            try:
                detail = json.loads(model.canslim_detail)
                canslim_score = CANSLIMScore.from_dict(detail)
            except (json.JSONDecodeError, KeyError, TypeError):
                # JSONパースエラーまたはデータ不整合の場合はNone
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
    def to_model(
        entity: Stock,
        existing: ScreenerResultModel | None = None,
    ) -> ScreenerResultModel:
        """
        ドメインエンティティをSQLAlchemyモデルに変換

        Args:
            entity: ドメインエンティティ
            existing: 既存のモデル（更新時）

        Returns:
            ScreenerResultModel: SQLAlchemyモデル
        """
        # CAN-SLIMスコアをJSON化
        canslim_detail = None
        if entity.canslim_score:
            canslim_detail = json.dumps(entity.canslim_score.to_dict())

        canslim_total_score = (
            entity.canslim_score.total_score if entity.canslim_score else 0
        )

        if existing:
            # 既存レコードを更新
            existing.name = entity.name
            existing.price = entity.price
            existing.change_percent = entity.change_percent
            existing.volume = entity.volume
            existing.avg_volume = entity.avg_volume
            existing.market_cap = entity.market_cap
            existing.pe_ratio = entity.pe_ratio
            existing.week_52_high = entity.week_52_high
            existing.week_52_low = entity.week_52_low
            existing.eps_growth_quarterly = entity.eps_growth_quarterly
            existing.eps_growth_annual = entity.eps_growth_annual
            existing.rs_rating = entity.rs_rating
            existing.institutional_ownership = entity.institutional_ownership
            existing.canslim_total_score = canslim_total_score
            existing.canslim_detail = canslim_detail
            existing.updated_at = datetime.now()
            return existing
        else:
            # 新規作成
            return ScreenerResultModel(
                symbol=entity.symbol.upper(),
                name=entity.name,
                price=entity.price,
                change_percent=entity.change_percent,
                volume=entity.volume,
                avg_volume=entity.avg_volume,
                market_cap=entity.market_cap,
                pe_ratio=entity.pe_ratio,
                week_52_high=entity.week_52_high,
                week_52_low=entity.week_52_low,
                eps_growth_quarterly=entity.eps_growth_quarterly,
                eps_growth_annual=entity.eps_growth_annual,
                rs_rating=entity.rs_rating,
                institutional_ownership=entity.institutional_ownership,
                canslim_total_score=canslim_total_score,
                canslim_detail=canslim_detail,
            )
