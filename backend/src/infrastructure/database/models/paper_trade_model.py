"""ペーパートレード SQLAlchemyモデル"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.connection import Base


class PaperTradeModel(Base):
    """
    ペーパートレードモデル

    仮想売買の記録を保存。
    """

    __tablename__ = "paper_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 銘柄情報
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    # トレード情報
    trade_type: Mapped[str] = mapped_column(String(10), nullable=False)  # buy, sell
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # エントリー
    entry_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    entry_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # エグジット
    exit_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    exit_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # リスク管理
    stop_loss_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    target_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    # ステータス
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open", index=True
    )

    # メモ
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # メタデータ
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<PaperTradeModel("
            f"id={self.id}, "
            f"symbol={self.symbol}, "
            f"type={self.trade_type}, "
            f"status={self.status}"
            f")>"
        )
