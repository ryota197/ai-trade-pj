"""トレード取得 ユースケース"""

from src.application.dto.portfolio_dto import (
    OpenPositionOutput,
    TradeFilterInput,
    TradeListOutput,
    TradeOutput,
)
from src.application.interfaces.financial_data_gateway import FinancialDataGateway
from src.domain.entities.paper_trade import PaperTrade, TradeStatus, TradeType
from src.domain.repositories.trade_repository import TradeRepository


class GetTradesUseCase:
    """
    トレード取得 ユースケース

    トレード履歴の取得、オープンポジションの取得を行う。
    """

    def __init__(
        self,
        trade_repository: TradeRepository,
        financial_gateway: FinancialDataGateway | None = None,
    ) -> None:
        self._trade_repo = trade_repository
        self._financial_gateway = financial_gateway

    async def get_trades(
        self,
        filter_input: TradeFilterInput | None = None,
    ) -> TradeListOutput:
        """
        トレード一覧を取得

        Args:
            filter_input: フィルター条件

        Returns:
            TradeListOutput: トレード一覧
        """
        if filter_input is None:
            filter_input = TradeFilterInput()

        # ステータス・タイプの変換
        status = None
        trade_type = None

        if filter_input.status:
            try:
                status = TradeStatus(filter_input.status)
            except ValueError:
                pass

        if filter_input.trade_type:
            try:
                trade_type = TradeType(filter_input.trade_type)
            except ValueError:
                pass

        # シンボルでフィルタする場合
        if filter_input.symbol:
            trades = await self._trade_repo.get_by_symbol(
                symbol=filter_input.symbol.upper(),
                status=status,
            )
        else:
            trades = await self._trade_repo.get_all(
                status=status,
                trade_type=trade_type,
                limit=filter_input.limit,
                offset=filter_input.offset,
            )

        # カウント取得
        total_count = await self._trade_repo.count()
        open_count = await self._trade_repo.count(status=TradeStatus.OPEN)
        closed_count = await self._trade_repo.count(status=TradeStatus.CLOSED)

        return TradeListOutput(
            trades=[self._to_output(trade) for trade in trades],
            total_count=total_count,
            open_count=open_count,
            closed_count=closed_count,
        )

    async def get_open_positions(self) -> list[OpenPositionOutput]:
        """
        オープンポジション一覧を取得

        現在価格と含み損益も含めて返す。

        Returns:
            list[OpenPositionOutput]: オープンポジションのリスト
        """
        trades = await self._trade_repo.get_open_positions()

        result = []
        for trade in trades:
            current_price = None
            unrealized_pnl = None
            unrealized_return = None

            # 現在価格を取得（Gatewayが設定されている場合）
            if self._financial_gateway:
                try:
                    quote = await self._financial_gateway.get_quote(trade.symbol)
                    if quote:
                        current_price = quote.price
                        unrealized_return = trade.calculate_unrealized_return(
                            current_price
                        )
                        unrealized_pnl = (
                            unrealized_return / 100 * trade.position_value
                        )
                except Exception:
                    pass

            result.append(
                OpenPositionOutput(
                    id=trade.id,
                    symbol=trade.symbol,
                    trade_type=trade.trade_type.value,
                    quantity=trade.quantity,
                    entry_price=trade.entry_price,
                    entry_date=trade.entry_date,
                    stop_loss_price=trade.stop_loss_price,
                    target_price=trade.target_price,
                    position_value=trade.position_value,
                    holding_days=trade.holding_days or 0,
                    current_price=current_price,
                    unrealized_pnl=(
                        round(unrealized_pnl, 2) if unrealized_pnl else None
                    ),
                    unrealized_return_percent=unrealized_return,
                )
            )

        return result

    async def get_closed_trades(
        self,
        filter_input: TradeFilterInput | None = None,
    ) -> list[TradeOutput]:
        """
        クローズ済みトレード一覧を取得

        Args:
            filter_input: フィルター条件

        Returns:
            list[TradeOutput]: クローズ済みトレードのリスト
        """
        if filter_input is None:
            filter_input = TradeFilterInput()

        trades = await self._trade_repo.get_closed_trades(
            start_date=filter_input.start_date,
            end_date=filter_input.end_date,
            limit=filter_input.limit,
            offset=filter_input.offset,
        )

        return [self._to_output(trade) for trade in trades]

    async def get_trades_by_symbol(self, symbol: str) -> list[TradeOutput]:
        """
        シンボル別のトレード履歴を取得

        Args:
            symbol: ティッカーシンボル

        Returns:
            list[TradeOutput]: トレードのリスト
        """
        trades = await self._trade_repo.get_by_symbol(symbol.upper())
        return [self._to_output(trade) for trade in trades]

    def _to_output(self, trade: PaperTrade) -> TradeOutput:
        """エンティティを出力DTOに変換"""
        return TradeOutput(
            id=trade.id,
            symbol=trade.symbol,
            trade_type=trade.trade_type.value,
            quantity=trade.quantity,
            entry_price=trade.entry_price,
            entry_date=trade.entry_date,
            exit_price=trade.exit_price,
            exit_date=trade.exit_date,
            stop_loss_price=trade.stop_loss_price,
            target_price=trade.target_price,
            status=trade.status.value,
            notes=trade.notes,
            created_at=trade.created_at,
            position_value=trade.position_value,
            profit_loss=trade.profit_loss,
            return_percent=trade.return_percent,
            holding_days=trade.holding_days,
            is_winner=trade.is_winner,
        )
