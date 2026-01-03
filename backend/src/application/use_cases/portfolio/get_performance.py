"""パフォーマンス取得 ユースケース"""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from src.application.dto.portfolio_dto import (
    PerformanceOutput,
)
from src.domain.models.trade import Trade, TradeStatus
from src.domain.repositories.trade_repository import TradeRepository


class GetPerformanceUseCase:
    """
    パフォーマンス取得 ユースケース

    トレード履歴からパフォーマンス指標を計算して返す。
    """

    def __init__(self, trade_repository: TradeRepository) -> None:
        self._trade_repo = trade_repository

    def get_performance(self, limit: int = 1000) -> PerformanceOutput:
        """
        パフォーマンス指標を取得

        Args:
            limit: 対象トレード数

        Returns:
            PerformanceOutput: パフォーマンス指標
        """
        # クローズ済みトレードを取得
        trades = self._trade_repo.find_closed(limit=limit)

        return self._calculate_metrics(trades)

    def _calculate_metrics(self, trades: list[Trade]) -> PerformanceOutput:
        """トレードからパフォーマンス指標を計算"""
        if not trades:
            return self._empty_output()

        total_trades = len(trades)
        winning_trades = 0
        losing_trades = 0
        total_profit_loss = Decimal("0")
        total_wins = Decimal("0")
        total_losses = Decimal("0")
        holding_days_sum = 0
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0

        for trade in trades:
            pnl = trade.profit_loss()
            if pnl is None:
                continue

            total_profit_loss += pnl

            # 保有日数
            if trade.closed_at and trade.traded_at:
                days = (trade.closed_at - trade.traded_at).days
                holding_days_sum += max(days, 0)

            if pnl > 0:
                winning_trades += 1
                total_wins += pnl
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            else:
                losing_trades += 1
                total_losses += abs(pnl)
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)

        # 勝率
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0

        # 平均利益・損失
        avg_win = float(total_wins / winning_trades) if winning_trades > 0 else 0
        avg_loss = float(total_losses / losing_trades) if losing_trades > 0 else 0

        # プロフィットファクター
        profit_factor = (
            float(total_wins / total_losses) if total_losses > 0 else None
        )

        # 期待値
        expectancy = float(total_profit_loss / total_trades) if total_trades > 0 else 0

        # リスクリワード比率
        risk_reward = avg_win / avg_loss if avg_loss > 0 else None

        # 平均保有日数
        avg_holding_days = holding_days_sum / total_trades if total_trades > 0 else 0

        # 総リターン（簡易計算）
        total_return = float(total_profit_loss)
        avg_return = total_return / total_trades if total_trades > 0 else 0

        return PerformanceOutput(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_profit_loss=total_return,
            total_return_percent=0.0,  # 元本がないため計算不可
            average_return_percent=avg_return,
            win_rate=win_rate,
            average_win=avg_win,
            average_loss=avg_loss,
            profit_factor=profit_factor,
            expectancy=expectancy,
            risk_reward_ratio=risk_reward,
            max_drawdown_percent=0.0,  # 簡易版では計算しない
            max_consecutive_wins=max_consecutive_wins,
            max_consecutive_losses=max_consecutive_losses,
            average_holding_days=avg_holding_days,
            is_profitable=total_profit_loss > 0,
            has_sufficient_trades=total_trades >= 20,
            calculated_at=datetime.now(),
        )

    def _empty_output(self) -> PerformanceOutput:
        """空のパフォーマンス出力"""
        return PerformanceOutput(
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
            risk_reward_ratio=None,
            max_drawdown_percent=0.0,
            max_consecutive_wins=0,
            max_consecutive_losses=0,
            average_holding_days=0.0,
            is_profitable=False,
            has_sufficient_trades=False,
            calculated_at=datetime.now(),
        )
