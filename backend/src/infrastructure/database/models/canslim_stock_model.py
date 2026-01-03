"""CAN-SLIM銘柄 SQLAlchemyモデル"""

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.connection import Base


class CANSLIMStockModel(Base):
    """
    CAN-SLIM分析銘柄

    canslim_stocks テーブルに対応するSQLAlchemyモデル。
    複合主キー（symbol, date）を使用。
    """

    __tablename__ = "canslim_stocks"

    # 主キー（複合）
    symbol: Mapped[str] = mapped_column(String(10), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)

    # 銘柄情報
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 価格データ
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    change_percent: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_volume_50d: Mapped[int | None] = mapped_column(Integer, nullable=True)
    market_cap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    week_52_high: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    week_52_low: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # 財務データ
    eps_growth_quarterly: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    eps_growth_annual: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    institutional_ownership: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )

    # RS関連
    relative_strength: Mapped[float | None] = mapped_column(
        Numeric(10, 4), nullable=True
    )
    rs_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # CAN-SLIMスコア
    canslim_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_c: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_a: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_n: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_l: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_i: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_m: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # メタデータ
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<CANSLIMStock("
            f"symbol={self.symbol}, "
            f"date={self.date}, "
            f"rs_rating={self.rs_rating}, "
            f"canslim_score={self.canslim_score}"
            f")>"
        )
