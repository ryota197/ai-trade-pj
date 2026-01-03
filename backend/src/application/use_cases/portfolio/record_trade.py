"""トレード記録 ユースケース"""

from src.application.dto.portfolio_dto import (
    CloseTradeInput,
    OpenTradeInput,
    TradeOutput,
)
from src.domain.models.trade import Trade, TradeType
from src.domain.repositories.trade_repository import TradeRepository


class RecordTradeUseCase:
    """
    トレード記録 ユースケース

    ペーパートレードの記録（新規ポジション、決済、キャンセル）を行う。
    """

    def __init__(self, trade_repository: TradeRepository) -> None:
        self._trade_repo = trade_repository

    def open_position(self, input_dto: OpenTradeInput) -> TradeOutput:
        """
        新規ポジションを開く

        Args:
            input_dto: ポジション情報

        Returns:
            TradeOutput: 作成されたトレード

        Raises:
            ValueError: 不正なトレードタイプの場合
        """
        # トレードタイプの変換
        try:
            trade_type = TradeType(input_dto.trade_type)
        except ValueError:
            raise ValueError(
                f"Invalid trade type: {input_dto.trade_type}. "
                "Must be 'buy' or 'sell'"
            )

        # エンティティ作成
        trade = Trade(
            symbol=input_dto.symbol.upper(),
            trade_type=trade_type,
            quantity=input_dto.quantity,
            entry_price=input_dto.entry_price,
        )

        # 保存
        self._trade_repo.save(trade)

        return self._to_output(trade)

    def close_position(self, input_dto: CloseTradeInput) -> TradeOutput | None:
        """
        ポジションを決済

        Args:
            input_dto: 決済情報

        Returns:
            TradeOutput | None: 決済されたトレード、存在しない場合はNone

        Raises:
            ValueError: トレードが既にクローズ済みの場合
        """
        # 既存トレードを取得
        trade = self._trade_repo.find_by_id(input_dto.trade_id)
        if trade is None:
            return None

        # 決済（ドメインロジック）
        trade.close(input_dto.exit_price)

        # 保存
        self._trade_repo.save(trade)

        return self._to_output(trade)

    def cancel_trade(self, trade_id: int) -> TradeOutput | None:
        """
        トレードをキャンセル

        Args:
            trade_id: トレードID

        Returns:
            TradeOutput | None: キャンセルされたトレード、存在しない場合はNone

        Raises:
            ValueError: トレードがオープン状態でない場合
        """
        trade = self._trade_repo.find_by_id(trade_id)
        if trade is None:
            return None

        # キャンセル（ドメインロジック）
        trade.cancel()

        # 保存
        self._trade_repo.save(trade)

        return self._to_output(trade)

    def get_trade(self, trade_id: int) -> TradeOutput | None:
        """
        IDでトレードを取得

        Args:
            trade_id: トレードID

        Returns:
            TradeOutput | None: トレード、存在しない場合はNone
        """
        trade = self._trade_repo.find_by_id(trade_id)
        if trade is None:
            return None
        return self._to_output(trade)

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
