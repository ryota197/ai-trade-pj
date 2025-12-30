"""PerformanceCalculator Domain Service"""

from datetime import datetime

from src.domain.models import PaperTrade
from src.domain.models import PerformanceMetrics


class PerformanceCalculator:
    """
    パフォーマンス計算 ドメインサービス

    クローズ済みトレードからパフォーマンス指標を計算する。
    """

    @classmethod
    def calculate(cls, trades: list[PaperTrade]) -> PerformanceMetrics:
        """
        トレード履歴からパフォーマンス指標を計算

        Args:
            trades: クローズ済みトレードのリスト

        Returns:
            PerformanceMetrics: 計算されたパフォーマンス指標
        """
        # クローズ済みのトレードのみをフィルタ
        closed_trades = [t for t in trades if t.is_closed and t.profit_loss is not None]

        if not closed_trades:
            return PerformanceMetrics.empty()

        # 基本統計
        total_trades = len(closed_trades)
        winning_trades = [t for t in closed_trades if t.is_winner]
        losing_trades = [t for t in closed_trades if not t.is_winner]

        winning_count = len(winning_trades)
        losing_count = len(losing_trades)

        # 損益計算
        total_profit_loss = sum(t.profit_loss for t in closed_trades)
        total_investment = sum(t.position_value for t in closed_trades)

        total_return_percent = (
            (total_profit_loss / total_investment * 100) if total_investment > 0 else 0.0
        )

        returns = [t.return_percent for t in closed_trades if t.return_percent is not None]
        average_return_percent = sum(returns) / len(returns) if returns else 0.0

        # 勝率
        win_rate = (winning_count / total_trades * 100) if total_trades > 0 else 0.0

        # 平均勝ち・負け
        wins = [t.profit_loss for t in winning_trades if t.profit_loss is not None]
        losses = [abs(t.profit_loss) for t in losing_trades if t.profit_loss is not None]

        average_win = sum(wins) / len(wins) if wins else 0.0
        average_loss = sum(losses) / len(losses) if losses else 0.0

        # プロフィットファクター
        total_wins = sum(wins)
        total_losses = sum(losses)
        profit_factor = (total_wins / total_losses) if total_losses > 0 else None

        # 期待値
        expectancy = cls._calculate_expectancy(win_rate / 100, average_win, average_loss)

        # 最大ドローダウン
        max_drawdown = cls._calculate_max_drawdown(closed_trades)

        # 連勝・連敗
        max_consecutive_wins, max_consecutive_losses = cls._calculate_streaks(closed_trades)

        # 平均保有日数
        holding_days = [t.holding_days for t in closed_trades if t.holding_days is not None]
        average_holding_days = sum(holding_days) / len(holding_days) if holding_days else 0.0

        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_count,
            losing_trades=losing_count,
            total_profit_loss=round(total_profit_loss, 2),
            total_return_percent=round(total_return_percent, 2),
            average_return_percent=round(average_return_percent, 2),
            win_rate=round(win_rate, 2),
            average_win=round(average_win, 2),
            average_loss=round(average_loss, 2),
            profit_factor=round(profit_factor, 2) if profit_factor else None,
            expectancy=round(expectancy, 2),
            max_drawdown_percent=round(max_drawdown, 2),
            max_consecutive_wins=max_consecutive_wins,
            max_consecutive_losses=max_consecutive_losses,
            average_holding_days=round(average_holding_days, 1),
            calculated_at=datetime.now(),
        )

    @staticmethod
    def _calculate_expectancy(
        win_rate: float,
        average_win: float,
        average_loss: float,
    ) -> float:
        """
        期待値を計算

        期待値 = (勝率 × 平均勝ち) - (負け率 × 平均負け)

        Args:
            win_rate: 勝率（0-1）
            average_win: 平均勝ち額
            average_loss: 平均負け額

        Returns:
            float: 期待値
        """
        lose_rate = 1 - win_rate
        return (win_rate * average_win) - (lose_rate * average_loss)

    @staticmethod
    def _calculate_max_drawdown(trades: list[PaperTrade]) -> float:
        """
        最大ドローダウンを計算

        Args:
            trades: トレードのリスト（時系列順）

        Returns:
            float: 最大ドローダウン（%）
        """
        if not trades:
            return 0.0

        # 日付順にソート
        sorted_trades = sorted(trades, key=lambda t: t.exit_date or t.entry_date)

        cumulative_pnl = 0.0
        peak = 0.0
        max_drawdown = 0.0

        for trade in sorted_trades:
            if trade.profit_loss is not None:
                cumulative_pnl += trade.profit_loss

                if cumulative_pnl > peak:
                    peak = cumulative_pnl

                if peak > 0:
                    drawdown = (peak - cumulative_pnl) / peak * 100
                    max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    @staticmethod
    def _calculate_streaks(trades: list[PaperTrade]) -> tuple[int, int]:
        """
        最大連勝数・連敗数を計算

        Args:
            trades: トレードのリスト

        Returns:
            tuple[int, int]: (最大連勝数, 最大連敗数)
        """
        if not trades:
            return 0, 0

        # 日付順にソート
        sorted_trades = sorted(trades, key=lambda t: t.exit_date or t.entry_date)

        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0

        for trade in sorted_trades:
            if trade.is_winner:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)

        return max_wins, max_losses

    @classmethod
    def calculate_monthly_returns(
        cls,
        trades: list[PaperTrade],
    ) -> dict[str, float]:
        """
        月別リターンを計算

        Args:
            trades: クローズ済みトレードのリスト

        Returns:
            dict[str, float]: 月別リターン（キー: "YYYY-MM", 値: リターン%）
        """
        closed_trades = [t for t in trades if t.is_closed and t.exit_date is not None]

        if not closed_trades:
            return {}

        monthly_pnl: dict[str, float] = {}
        monthly_investment: dict[str, float] = {}

        for trade in closed_trades:
            month_key = trade.exit_date.strftime("%Y-%m")

            if month_key not in monthly_pnl:
                monthly_pnl[month_key] = 0.0
                monthly_investment[month_key] = 0.0

            if trade.profit_loss is not None:
                monthly_pnl[month_key] += trade.profit_loss
                monthly_investment[month_key] += trade.position_value

        monthly_returns: dict[str, float] = {}
        for month_key in sorted(monthly_pnl.keys()):
            if monthly_investment[month_key] > 0:
                ret = monthly_pnl[month_key] / monthly_investment[month_key] * 100
                monthly_returns[month_key] = round(ret, 2)
            else:
                monthly_returns[month_key] = 0.0

        return monthly_returns

    @classmethod
    def calculate_symbol_stats(
        cls,
        trades: list[PaperTrade],
    ) -> dict[str, dict]:
        """
        シンボル別統計を計算

        Args:
            trades: クローズ済みトレードのリスト

        Returns:
            dict[str, dict]: シンボル別統計
        """
        closed_trades = [t for t in trades if t.is_closed]

        if not closed_trades:
            return {}

        symbol_trades: dict[str, list[PaperTrade]] = {}
        for trade in closed_trades:
            if trade.symbol not in symbol_trades:
                symbol_trades[trade.symbol] = []
            symbol_trades[trade.symbol].append(trade)

        symbol_stats: dict[str, dict] = {}
        for symbol, sym_trades in symbol_trades.items():
            pnl_list = [t.profit_loss for t in sym_trades if t.profit_loss is not None]
            winners = [t for t in sym_trades if t.is_winner]

            symbol_stats[symbol] = {
                "total_trades": len(sym_trades),
                "winning_trades": len(winners),
                "total_profit_loss": round(sum(pnl_list), 2),
                "win_rate": round(len(winners) / len(sym_trades) * 100, 2),
            }

        return symbol_stats
