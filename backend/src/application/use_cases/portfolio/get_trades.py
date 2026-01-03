"""トレード取得 ユースケース"""

from decimal import Decimal

from src.application.dto.portfolio_dto import (
    OpenPositionOutput,
    TradeListOutput,
    TradeOutput,
)
from src.application.interfaces.financial_data_gateway import FinancialDataGateway
from src.domain.models.trade import Trade, TradeType
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

    def get_open_positions(self) -> list[OpenPositionOutput]:
        """
        オープンポジション一覧を取得

        Returns:
            list[OpenPositionOutput]: オープンポジションのリスト
        """
        trades = self._trade_repo.find_open_positions()
        return [self._to_open_position_output(trade) for trade in trades]

    def get_closed_trades(self, limit: int = 50) -> list[TradeOutput]:
        """
        クローズ済みトレード一覧を取得

        Args:
            limit: 取得件数

        Returns:
            list[TradeOutput]: クローズ済みトレードのリスト
        """
        trades = self._trade_repo.find_closed(limit=limit)
        return [self._to_output(trade) for trade in trades]

    def get_trades_by_symbol(self, symbol: str) -> list[TradeOutput]:
        """
        シンボル別のトレード履歴を取得

        Args:
            symbol: ティッカーシンボル

        Returns:
            list[TradeOutput]: トレードのリスト
        """
        trades = self._trade_repo.find_by_symbol(symbol.upper())
        return [self._to_output(trade) for trade in trades]

    def get_trade_summary(self) -> TradeListOutput:
        """
        トレードサマリーを取得

        Returns:
            TradeListOutput: トレードサマリー
        """
        open_trades = self._trade_repo.find_open_positions()
        closed_trades = self._trade_repo.find_closed(limit=100)

        all_trades = open_trades + closed_trades

        return TradeListOutput(
            trades=[self._to_output(trade) for trade in all_trades],
            total_count=len(all_trades),
            open_count=len(open_trades),
            closed_count=len(closed_trades),
        )

    def _to_output(self, trade: Trade) -> TradeOutput:
        """エンティティを出力DTOに変換"""
        return TradeOutput(
            symbol=trade.symbol,
            trade_type=trade.trade_type.value,
            quantity=trade.quantity,
            entry_price=trade.entry_price,
            status=trade.status.value,
            traded_at=trade.traded_at,
            id=trade.id,
            exit_price=trade.exit_price,
            closed_at=trade.closed_at,
            profit_loss=trade.profit_loss(),
            profit_loss_percent=trade.profit_loss_percent(),
        )

    def _to_open_position_output(self, trade: Trade) -> OpenPositionOutput:
        """オープンポジション出力DTOに変換"""
        current_price: Decimal | None = None
        unrealized_pnl: Decimal | None = None
        unrealized_pnl_percent: Decimal | None = None

        # 現在価格を取得（Gatewayが設定されている場合）
        if self._financial_gateway:
            try:
                quote = self._financial_gateway.get_quote(trade.symbol)
                if quote:
                    current_price = Decimal(str(quote.price))
                    # 含み損益計算
                    if trade.trade_type == TradeType.BUY:
                        unrealized_pnl = (
                            current_price - trade.entry_price
                        ) * trade.quantity
                        unrealized_pnl_percent = (
                            (current_price - trade.entry_price)
                            / trade.entry_price
                            * 100
                        )
                    else:  # SELL
                        unrealized_pnl = (
                            trade.entry_price - current_price
                        ) * trade.quantity
                        unrealized_pnl_percent = (
                            (trade.entry_price - current_price)
                            / trade.entry_price
                            * 100
                        )
            except Exception:
                pass

        return OpenPositionOutput(
            symbol=trade.symbol,
            trade_type=trade.trade_type.value,
            quantity=trade.quantity,
            entry_price=trade.entry_price,
            traded_at=trade.traded_at,
            id=trade.id,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percent=unrealized_pnl_percent,
        )
