"""マーケットスナップショットクエリ"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import MarketSnapshot
from src.services._lib import MarketAnalysisResult


class MarketSnapshotQuery:
    """マーケットスナップショットデータアクセス"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_latest(self) -> MarketSnapshot | None:
        """最新のマーケット状態を取得"""
        stmt = (
            select(MarketSnapshot)
            .order_by(MarketSnapshot.recorded_at.desc())
            .limit(1)
        )
        return self._session.scalars(stmt).first()

    def save(self, result: MarketAnalysisResult) -> MarketSnapshot:
        """マーケット分析結果を保存"""
        model = MarketSnapshot(
            recorded_at=result.recorded_at,
            vix=float(result.vix),
            sp500_price=float(result.sp500_price),
            sp500_rsi=float(result.sp500_rsi),
            sp500_ma200=float(result.sp500_ma200),
            put_call_ratio=float(result.put_call_ratio),
            condition=result.condition.value,
            score=result.score,
        )

        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)

        return model
