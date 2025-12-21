"""PerformanceMetrics Value Object"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PerformanceMetrics:
    """
    トレードパフォーマンス指標 Value Object

    ペーパートレードの成績を評価するための各種指標を保持する。
    """

    # 基本統計
    total_trades: int  # 総トレード数
    winning_trades: int  # 勝ちトレード数
    losing_trades: int  # 負けトレード数

    # 損益
    total_profit_loss: float  # 総損益額
    total_return_percent: float  # 総リターン率（%）
    average_return_percent: float  # 平均リターン率（%）

    # 勝率・期待値
    win_rate: float  # 勝率（%）
    average_win: float  # 平均勝ち額
    average_loss: float  # 平均負け額（絶対値）
    profit_factor: float | None  # プロフィットファクター（総利益/総損失）
    expectancy: float  # 期待値（1トレードあたりの期待利益）

    # リスク指標
    max_drawdown_percent: float  # 最大ドローダウン（%）
    max_consecutive_wins: int  # 最大連勝数
    max_consecutive_losses: int  # 最大連敗数

    # 期間
    average_holding_days: float  # 平均保有日数
    calculated_at: datetime  # 計算日時

    @classmethod
    def empty(cls) -> "PerformanceMetrics":
        """
        空のパフォーマンス指標を作成

        トレード履歴がない場合に使用する。

        Returns:
            PerformanceMetrics: ゼロ値で初期化された指標
        """
        return cls(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            total_profit_loss=0.0,
            total_return_percent=0.0,
            average_return_percent=0.0,
            win_rate=0.0,
            average_win=0.0,
            average_loss=0.0,
            profit_factor=None,
            expectancy=0.0,
            max_drawdown_percent=0.0,
            max_consecutive_wins=0,
            max_consecutive_losses=0,
            average_holding_days=0.0,
            calculated_at=datetime.now(),
        )

    @property
    def risk_reward_ratio(self) -> float | None:
        """
        リスクリワード比を計算

        Returns:
            float | None: 平均勝ち / 平均負け（計算不可の場合はNone）
        """
        if self.average_loss == 0:
            return None
        return round(self.average_win / self.average_loss, 2)

    @property
    def is_profitable(self) -> bool:
        """
        全体として利益が出ているか

        Returns:
            bool: 利益が出ていればTrue
        """
        return self.total_profit_loss > 0

    @property
    def has_sufficient_trades(self) -> bool:
        """
        統計的に有意なトレード数があるか

        Returns:
            bool: 30トレード以上あればTrue
        """
        return self.total_trades >= 30

    def to_dict(self) -> dict:
        """
        辞書形式に変換

        Returns:
            dict: パフォーマンス指標の辞書表現
        """
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "total_profit_loss": self.total_profit_loss,
            "total_return_percent": self.total_return_percent,
            "average_return_percent": self.average_return_percent,
            "win_rate": self.win_rate,
            "average_win": self.average_win,
            "average_loss": self.average_loss,
            "profit_factor": self.profit_factor,
            "expectancy": self.expectancy,
            "max_drawdown_percent": self.max_drawdown_percent,
            "max_consecutive_wins": self.max_consecutive_wins,
            "max_consecutive_losses": self.max_consecutive_losses,
            "average_holding_days": self.average_holding_days,
            "risk_reward_ratio": self.risk_reward_ratio,
            "is_profitable": self.is_profitable,
            "calculated_at": self.calculated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PerformanceMetrics":
        """
        辞書から復元

        Args:
            data: パフォーマンス指標の辞書

        Returns:
            PerformanceMetrics: 復元されたインスタンス
        """
        calculated_at = data.get("calculated_at")
        if isinstance(calculated_at, str):
            calculated_at = datetime.fromisoformat(calculated_at)
        elif calculated_at is None:
            calculated_at = datetime.now()

        return cls(
            total_trades=data.get("total_trades", 0),
            winning_trades=data.get("winning_trades", 0),
            losing_trades=data.get("losing_trades", 0),
            total_profit_loss=data.get("total_profit_loss", 0.0),
            total_return_percent=data.get("total_return_percent", 0.0),
            average_return_percent=data.get("average_return_percent", 0.0),
            win_rate=data.get("win_rate", 0.0),
            average_win=data.get("average_win", 0.0),
            average_loss=data.get("average_loss", 0.0),
            profit_factor=data.get("profit_factor"),
            expectancy=data.get("expectancy", 0.0),
            max_drawdown_percent=data.get("max_drawdown_percent", 0.0),
            max_consecutive_wins=data.get("max_consecutive_wins", 0),
            max_consecutive_losses=data.get("max_consecutive_losses", 0),
            average_holding_days=data.get("average_holding_days", 0.0),
            calculated_at=calculated_at,
        )
