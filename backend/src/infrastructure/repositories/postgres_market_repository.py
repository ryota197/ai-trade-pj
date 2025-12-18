"""PostgreSQL マーケットリポジトリ"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.entities.market_status import MarketCondition, MarketStatus
from src.domain.repositories.market_snapshot_repository import MarketSnapshotRepository
from src.domain.value_objects.market_indicators import (
    MarketIndicators,
    MovingAverageIndicator,
    PutCallRatioIndicator,
    RsiIndicator,
    VixIndicator,
)
from src.infrastructure.database.models.market_snapshot_model import MarketSnapshotModel


class PostgresMarketRepository(MarketSnapshotRepository):
    """
    PostgreSQLによるマーケットスナップショットリポジトリ実装

    MarketSnapshotRepositoryインターフェースを実装し、
    マーケット状態の履歴をPostgreSQLに保存・取得する。
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, market_status: MarketStatus) -> int:
        """
        マーケット状態を保存

        Args:
            market_status: 保存するマーケット状態

        Returns:
            int: 保存されたレコードのID
        """
        model = MarketSnapshotModel(
            recorded_at=market_status.analyzed_at,
            # VIX
            vix=market_status.indicators.vix.value,
            vix_signal=market_status.indicators.vix.signal.value,
            # S&P500
            sp500_price=market_status.indicators.sp500_ma.current_price,
            sp500_rsi=market_status.indicators.sp500_rsi.value,
            sp500_rsi_signal=market_status.indicators.sp500_rsi.signal.value,
            sp500_ma200=market_status.indicators.sp500_ma.ma_200,
            sp500_above_ma200=market_status.indicators.sp500_ma.is_above_ma,
            # Put/Call Ratio
            put_call_ratio=market_status.indicators.put_call_ratio.value,
            put_call_signal=market_status.indicators.put_call_ratio.signal.value,
            # 判定結果
            market_condition=market_status.condition.value,
            confidence=market_status.confidence,
            score=market_status.score,
            recommendation=market_status.recommendation,
        )

        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)

        return model.id

    def get_latest(self) -> MarketStatus | None:
        """
        最新のマーケット状態を取得

        Returns:
            MarketStatus | None: 最新のマーケット状態、存在しない場合はNone
        """
        stmt = (
            select(MarketSnapshotModel)
            .order_by(MarketSnapshotModel.recorded_at.desc())
            .limit(1)
        )
        model = self._session.scalars(stmt).first()

        if model is None:
            return None

        return self._model_to_entity(model)

    def get_history(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[MarketStatus]:
        """
        マーケット状態の履歴を取得

        Args:
            start_date: 開始日時（指定しない場合は制限なし）
            end_date: 終了日時（指定しない場合は現在まで）
            limit: 取得件数上限

        Returns:
            list[MarketStatus]: マーケット状態のリスト（新しい順）
        """
        stmt = select(MarketSnapshotModel)

        if start_date is not None:
            stmt = stmt.where(MarketSnapshotModel.recorded_at >= start_date)

        if end_date is not None:
            stmt = stmt.where(MarketSnapshotModel.recorded_at <= end_date)

        stmt = stmt.order_by(MarketSnapshotModel.recorded_at.desc()).limit(limit)

        models = self._session.scalars(stmt).all()

        return [self._model_to_entity(model) for model in models]

    def _model_to_entity(self, model: MarketSnapshotModel) -> MarketStatus:
        """
        SQLAlchemyモデルをドメインエンティティに変換

        Args:
            model: SQLAlchemyモデル

        Returns:
            MarketStatus: ドメインエンティティ
        """
        indicators = MarketIndicators(
            vix=VixIndicator(value=float(model.vix)),
            sp500_rsi=RsiIndicator(value=float(model.sp500_rsi)),
            sp500_ma=MovingAverageIndicator(
                current_price=float(model.sp500_price),
                ma_200=float(model.sp500_ma200),
            ),
            put_call_ratio=PutCallRatioIndicator(value=float(model.put_call_ratio)),
        )

        return MarketStatus(
            condition=MarketCondition(model.market_condition),
            confidence=float(model.confidence),
            score=model.score,
            indicators=indicators,
            recommendation=model.recommendation,
            analyzed_at=model.recorded_at,
        )
