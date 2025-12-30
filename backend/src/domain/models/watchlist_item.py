"""WatchlistItem エンティティ"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class WatchlistStatus(Enum):
    """ウォッチリストステータス"""

    WATCHING = "watching"  # 監視中
    TRIGGERED = "triggered"  # 条件達成
    EXPIRED = "expired"  # 期限切れ
    REMOVED = "removed"  # 削除済み


@dataclass(frozen=True)
class WatchlistItem:
    """
    ウォッチリストアイテム エンティティ

    CAN-SLIMスクリーニングで見つけた銘柄を監視するためのエンティティ。
    目標エントリー価格、ストップロス価格、メモなどを記録する。
    """

    id: int | None  # データベースID（新規作成時はNone）
    symbol: str  # ティッカーシンボル
    added_at: datetime  # 追加日時
    target_entry_price: float | None  # 目標エントリー価格
    stop_loss_price: float | None  # ストップロス価格
    target_price: float | None  # 目標利確価格
    notes: str | None  # メモ
    status: WatchlistStatus  # ステータス
    triggered_at: datetime | None  # 条件達成日時

    @classmethod
    def create(
        cls,
        symbol: str,
        target_entry_price: float | None = None,
        stop_loss_price: float | None = None,
        target_price: float | None = None,
        notes: str | None = None,
    ) -> "WatchlistItem":
        """
        新規ウォッチリストアイテムを作成

        Args:
            symbol: ティッカーシンボル
            target_entry_price: 目標エントリー価格
            stop_loss_price: ストップロス価格
            target_price: 目標利確価格
            notes: メモ

        Returns:
            WatchlistItem: 新規作成されたウォッチリストアイテム
        """
        return cls(
            id=None,
            symbol=symbol.upper(),
            added_at=datetime.now(),
            target_entry_price=target_entry_price,
            stop_loss_price=stop_loss_price,
            target_price=target_price,
            notes=notes,
            status=WatchlistStatus.WATCHING,
            triggered_at=None,
        )

    def is_entry_triggered(self, current_price: float) -> bool:
        """
        エントリー条件が達成されたか判定

        Args:
            current_price: 現在価格

        Returns:
            bool: 条件達成ならTrue
        """
        if self.target_entry_price is None:
            return False
        # 目標価格以下になったらエントリー条件達成
        return current_price <= self.target_entry_price

    def calculate_risk_reward_ratio(self) -> float | None:
        """
        リスクリワード比を計算

        Returns:
            float | None: リスクリワード比（計算不可の場合はNone）
        """
        if (
            self.target_entry_price is None
            or self.stop_loss_price is None
            or self.target_price is None
        ):
            return None

        risk = self.target_entry_price - self.stop_loss_price
        reward = self.target_price - self.target_entry_price

        if risk <= 0:
            return None

        return round(reward / risk, 2)

    def calculate_potential_loss_percent(self) -> float | None:
        """
        ストップロス時の損失率を計算

        Returns:
            float | None: 損失率（%）
        """
        if self.target_entry_price is None or self.stop_loss_price is None:
            return None

        if self.target_entry_price == 0:
            return None

        loss = (
            (self.target_entry_price - self.stop_loss_price)
            / self.target_entry_price
            * 100
        )
        return round(loss, 2)

    def calculate_potential_gain_percent(self) -> float | None:
        """
        目標達成時の利益率を計算

        Returns:
            float | None: 利益率（%）
        """
        if self.target_entry_price is None or self.target_price is None:
            return None

        if self.target_entry_price == 0:
            return None

        gain = (
            (self.target_price - self.target_entry_price)
            / self.target_entry_price
            * 100
        )
        return round(gain, 2)
