"""MarketSnapshot SQLAlchemyモデル"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.connection import Base


class MarketSnapshotModel(Base):
    """
    マーケットスナップショット

    market_snapshots テーブルに対応するSQLAlchemyモデル。
    """

    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 記録日時
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    # 指標
    vix: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sp500_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    sp500_rsi: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    sp500_ma200: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    put_call_ratio: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)

    # 判定結果
    condition: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<MarketSnapshot("
            f"id={self.id}, "
            f"recorded_at={self.recorded_at}, "
            f"condition={self.condition}, "
            f"score={self.score}"
            f")>"
        )
