"""パフォーマンス取得 ユースケース"""

from src.application.dto.portfolio_dto import (
    DetailedPerformanceOutput,
    MonthlyReturnOutput,
    PerformanceInput,
    PerformanceOutput,
    SymbolStatsOutput,
)
from src.domain.repositories.trade_repository import TradeRepository
from src.domain.services.performance_calculator import PerformanceCalculator
from src.domain.models import PerformanceMetrics


class GetPerformanceUseCase:
    """
    パフォーマンス取得 ユースケース

    トレード履歴からパフォーマンス指標を計算して返す。
    """

    def __init__(
        self,
        trade_repository: TradeRepository,
        performance_calculator: PerformanceCalculator | None = None,
    ) -> None:
        self._trade_repo = trade_repository
        self._calculator = performance_calculator or PerformanceCalculator()

    async def get_performance(
        self,
        input_dto: PerformanceInput | None = None,
    ) -> PerformanceOutput:
        """
        パフォーマンス指標を取得

        Args:
            input_dto: 期間指定（オプション）

        Returns:
            PerformanceOutput: パフォーマンス指標
        """
        if input_dto is None:
            input_dto = PerformanceInput()

        # クローズ済みトレードを取得
        trades = await self._trade_repo.get_closed_trades(
            start_date=input_dto.start_date,
            end_date=input_dto.end_date,
            limit=10000,  # パフォーマンス計算には全件必要
        )

        # パフォーマンス計算
        metrics = self._calculator.calculate(trades)

        return self._metrics_to_output(metrics)

    async def get_detailed_performance(
        self,
        input_dto: PerformanceInput | None = None,
    ) -> DetailedPerformanceOutput:
        """
        詳細パフォーマンス指標を取得

        月別リターン、シンボル別統計を含む。

        Args:
            input_dto: 期間指定（オプション）

        Returns:
            DetailedPerformanceOutput: 詳細パフォーマンス指標
        """
        if input_dto is None:
            input_dto = PerformanceInput()

        # クローズ済みトレードを取得
        trades = await self._trade_repo.get_closed_trades(
            start_date=input_dto.start_date,
            end_date=input_dto.end_date,
            limit=10000,
        )

        # 基本パフォーマンス計算
        metrics = self._calculator.calculate(trades)

        # 月別リターン計算
        monthly_returns_dict = self._calculator.calculate_monthly_returns(trades)
        monthly_returns = [
            MonthlyReturnOutput(
                month=month,
                return_percent=return_pct,
                trade_count=sum(
                    1
                    for t in trades
                    if t.exit_date and t.exit_date.strftime("%Y-%m") == month
                ),
            )
            for month, return_pct in monthly_returns_dict.items()
        ]

        # シンボル別統計
        symbol_stats_dict = self._calculator.calculate_symbol_stats(trades)
        symbol_stats = [
            SymbolStatsOutput(
                symbol=symbol,
                total_trades=stats["total_trades"],
                winning_trades=stats["winning_trades"],
                total_profit_loss=stats["total_profit_loss"],
                win_rate=stats["win_rate"],
            )
            for symbol, stats in symbol_stats_dict.items()
        ]

        # 勝率でソート
        symbol_stats.sort(key=lambda x: x.win_rate, reverse=True)

        return DetailedPerformanceOutput(
            summary=self._metrics_to_output(metrics),
            monthly_returns=monthly_returns,
            symbol_stats=symbol_stats,
        )

    async def get_total_profit_loss(
        self,
        input_dto: PerformanceInput | None = None,
    ) -> float:
        """
        総損益を取得

        Args:
            input_dto: 期間指定（オプション）

        Returns:
            float: 総損益額
        """
        if input_dto is None:
            input_dto = PerformanceInput()

        return await self._trade_repo.get_total_profit_loss(
            start_date=input_dto.start_date,
            end_date=input_dto.end_date,
        )

    def _metrics_to_output(self, metrics: PerformanceMetrics) -> PerformanceOutput:
        """PerformanceMetricsを出力DTOに変換"""
        return PerformanceOutput(
            total_trades=metrics.total_trades,
            winning_trades=metrics.winning_trades,
            losing_trades=metrics.losing_trades,
            total_profit_loss=metrics.total_profit_loss,
            total_return_percent=metrics.total_return_percent,
            average_return_percent=metrics.average_return_percent,
            win_rate=metrics.win_rate,
            average_win=metrics.average_win,
            average_loss=metrics.average_loss,
            profit_factor=metrics.profit_factor,
            expectancy=metrics.expectancy,
            risk_reward_ratio=metrics.risk_reward_ratio,
            max_drawdown_percent=metrics.max_drawdown_percent,
            max_consecutive_wins=metrics.max_consecutive_wins,
            max_consecutive_losses=metrics.max_consecutive_losses,
            average_holding_days=metrics.average_holding_days,
            is_profitable=metrics.is_profitable,
            has_sufficient_trades=metrics.has_sufficient_trades,
            calculated_at=metrics.calculated_at,
        )
