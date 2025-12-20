"""スクリーニング結果 SQLAlchemyモデル"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.connection import Base


class ScreenerResultModel(Base):
    """
    スクリーニング結果モデル

    CAN-SLIMスクリーニングで抽出された銘柄のスナップショットを保存。
    銘柄データのキャッシュとしても機能する。
    """

    __tablename__ = "screener_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 銘柄基本情報
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # 株価情報
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    change_percent: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    volume: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_volume: Mapped[int] = mapped_column(Integer, nullable=False)
    market_cap: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    pe_ratio: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    week_52_high: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    week_52_low: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # CAN-SLIM指標
    eps_growth_quarterly: Mapped[float | None] = mapped_column(
        Numeric(8, 2), nullable=True
    )
    eps_growth_annual: Mapped[float | None] = mapped_column(
        Numeric(8, 2), nullable=True
    )
    rs_rating: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    institutional_ownership: Mapped[float | None] = mapped_column(
        Numeric(6, 2), nullable=True
    )

    # CAN-SLIMスコア（JSON形式で保存）
    canslim_total_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    canslim_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    # メタデータ
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<ScreenerResult("
            f"symbol={self.symbol}, "
            f"rs_rating={self.rs_rating}, "
            f"canslim_score={self.canslim_total_score}"
            f")>"
        )
