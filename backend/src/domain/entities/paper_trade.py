"""PaperTrade エンティティ"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TradeType(Enum):
    """トレードタイプ"""

    BUY = "buy"  # 買い
    SELL = "sell"  # 売り


class TradeStatus(Enum):
    """トレードステータス"""

    OPEN = "open"  # オープンポジション
    CLOSED = "closed"  # クローズ済み
    CANCELLED = "cancelled"  # キャンセル


@dataclass(frozen=True)
class PaperTrade:
    """
    ペーパートレード エンティティ

    仮想売買の記録を表すエンティティ。
    買いと売りのペアで1つのトレードサイクルを構成する。
    """

    id: int | None  # データベースID（新規作成時はNone）
    symbol: str  # ティッカーシンボル
    trade_type: TradeType  # 売買タイプ
    quantity: int  # 数量
    entry_price: float  # エントリー価格
    entry_date: datetime  # エントリー日時
    exit_price: float | None  # 決済価格
    exit_date: datetime | None  # 決済日時
    stop_loss_price: float | None  # ストップロス価格
    target_price: float | None  # 目標価格
    status: TradeStatus  # ステータス
    notes: str | None  # メモ
    created_at: datetime  # 作成日時

    @classmethod
    def open_position(
        cls,
        symbol: str,
        trade_type: TradeType,
        quantity: int,
        entry_price: float,
        stop_loss_price: float | None = None,
        target_price: float | None = None,
        notes: str | None = None,
    ) -> "PaperTrade":
        """
        新規ポジションを開く

        Args:
            symbol: ティッカーシンボル
            trade_type: 売買タイプ
            quantity: 数量
            entry_price: エントリー価格
            stop_loss_price: ストップロス価格
            target_price: 目標価格
            notes: メモ

        Returns:
            PaperTrade: 新規作成されたトレード
        """
        now = datetime.now()
        return cls(
            id=None,
            symbol=symbol.upper(),
            trade_type=trade_type,
            quantity=quantity,
            entry_price=entry_price,
            entry_date=now,
            exit_price=None,
            exit_date=None,
            stop_loss_price=stop_loss_price,
            target_price=target_price,
            status=TradeStatus.OPEN,
            notes=notes,
            created_at=now,
        )

    @property
    def is_open(self) -> bool:
        """ポジションがオープンか"""
        return self.status == TradeStatus.OPEN

    @property
    def is_closed(self) -> bool:
        """ポジションがクローズ済みか"""
        return self.status == TradeStatus.CLOSED

    @property
    def holding_days(self) -> int | None:
        """
        保有日数を計算

        Returns:
            int | None: 保有日数（オープン中は現在までの日数）
        """
        if self.exit_date:
            delta = self.exit_date - self.entry_date
        else:
            delta = datetime.now() - self.entry_date

        return delta.days

    @property
    def return_percent(self) -> float | None:
        """
        リターン率を計算

        Returns:
            float | None: リターン率（%）、決済前はNone
        """
        if self.exit_price is None:
            return None

        if self.entry_price == 0:
            return None

        if self.trade_type == TradeType.BUY:
            # 買いの場合: (売却価格 - 購入価格) / 購入価格
            return_pct = (
                (self.exit_price - self.entry_price) / self.entry_price * 100
            )
        else:
            # 売り（ショート）の場合: (購入価格 - 売却価格) / 売却価格
            return_pct = (
                (self.entry_price - self.exit_price) / self.entry_price * 100
            )

        return round(return_pct, 2)

    @property
    def profit_loss(self) -> float | None:
        """
        損益額を計算

        Returns:
            float | None: 損益額、決済前はNone
        """
        if self.exit_price is None:
            return None

        if self.trade_type == TradeType.BUY:
            pl = (self.exit_price - self.entry_price) * self.quantity
        else:
            pl = (self.entry_price - self.exit_price) * self.quantity

        return round(pl, 2)

    @property
    def is_winner(self) -> bool | None:
        """
        勝ちトレードか判定

        Returns:
            bool | None: 勝ちならTrue、負けならFalse、決済前はNone
        """
        if self.return_percent is None:
            return None
        return self.return_percent > 0

    @property
    def position_value(self) -> float:
        """
        ポジション価値（エントリー時）

        Returns:
            float: ポジション価値
        """
        return self.entry_price * self.quantity

    def calculate_unrealized_return(self, current_price: float) -> float:
        """
        含み損益率を計算

        Args:
            current_price: 現在価格

        Returns:
            float: 含み損益率（%）
        """
        if self.entry_price == 0:
            return 0.0

        if self.trade_type == TradeType.BUY:
            return_pct = (current_price - self.entry_price) / self.entry_price * 100
        else:
            return_pct = (self.entry_price - current_price) / self.entry_price * 100

        return round(return_pct, 2)

    def is_stop_loss_triggered(self, current_price: float) -> bool:
        """
        ストップロスがトリガーされたか判定

        Args:
            current_price: 現在価格

        Returns:
            bool: トリガーされたらTrue
        """
        if self.stop_loss_price is None:
            return False

        if self.trade_type == TradeType.BUY:
            return current_price <= self.stop_loss_price
        else:
            return current_price >= self.stop_loss_price

    def is_target_reached(self, current_price: float) -> bool:
        """
        目標価格に到達したか判定

        Args:
            current_price: 現在価格

        Returns:
            bool: 到達したらTrue
        """
        if self.target_price is None:
            return False

        if self.trade_type == TradeType.BUY:
            return current_price >= self.target_price
        else:
            return current_price <= self.target_price
