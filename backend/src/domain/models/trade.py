"""Trade 集約ルート"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum


class TradeType(Enum):
    """トレードタイプ"""

    BUY = "buy"
    SELL = "sell"


class TradeStatus(Enum):
    """トレードステータス"""

    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


@dataclass
class Trade:
    """
    ペーパートレード（集約ルート）

    仮想売買の記録を表すエンティティ。
    """

    id: int
    symbol: str
    trade_type: TradeType
    quantity: int
    entry_price: Decimal
    status: TradeStatus = TradeStatus.OPEN
    exit_price: Decimal | None = None
    traded_at: datetime = field(default_factory=datetime.now)
    closed_at: datetime | None = None

    def __post_init__(self) -> None:
        """不変条件チェック"""
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.entry_price <= 0:
            raise ValueError("Entry price must be positive")

    def close(self, exit_price: Decimal) -> None:
        """トレードを決済"""
        if self.status != TradeStatus.OPEN:
            raise ValueError("Can only close open trades")
        if exit_price <= 0:
            raise ValueError("Exit price must be positive")

        self.exit_price = exit_price
        self.status = TradeStatus.CLOSED
        self.closed_at = datetime.now()

    def cancel(self) -> None:
        """トレードをキャンセル"""
        if self.status != TradeStatus.OPEN:
            raise ValueError("Can only cancel open trades")

        self.status = TradeStatus.CANCELLED
        self.closed_at = datetime.now()

    def profit_loss(self) -> Decimal | None:
        """損益額を計算"""
        if self.status != TradeStatus.CLOSED or self.exit_price is None:
            return None

        if self.trade_type == TradeType.BUY:
            return (self.exit_price - self.entry_price) * self.quantity
        else:  # SELL
            return (self.entry_price - self.exit_price) * self.quantity

    def profit_loss_percent(self) -> Decimal | None:
        """損益率を計算"""
        if self.status != TradeStatus.CLOSED or self.exit_price is None:
            return None

        if self.trade_type == TradeType.BUY:
            return (self.exit_price - self.entry_price) / self.entry_price * 100
        else:  # SELL
            return (self.entry_price - self.exit_price) / self.entry_price * 100
