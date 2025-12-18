"""マーケットスナップショット SQLAlchemyモデル"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.connection import Base


class MarketSnapshotModel(Base):
    """
    マーケットスナップショット

    市場指標と判定結果を履歴として保存するためのモデル。
    1時間ごとのスナップショットを想定。
    """

    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 記録日時
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    # VIX関連
    vix: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    vix_signal: Mapped[str] = mapped_column(String(20), nullable=False)

    # S&P500指標
    sp500_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    sp500_rsi: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    sp500_rsi_signal: Mapped[str] = mapped_column(String(20), nullable=False)
    sp500_ma200: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    sp500_above_ma200: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Put/Call Ratio
    put_call_ratio: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    put_call_signal: Mapped[str] = mapped_column(String(20), nullable=False)

    # 判定結果
    market_condition: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # risk_on, risk_off, neutral
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(500), nullable=False)

    # メタデータ
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<MarketSnapshot("
            f"id={self.id}, "
            f"recorded_at={self.recorded_at}, "
            f"condition={self.market_condition}, "
            f"score={self.score}"
            f")>"
        )
