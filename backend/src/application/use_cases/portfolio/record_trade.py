"""トレード記録 ユースケース"""

from datetime import datetime

from src.application.dto.portfolio_dto import (
    CloseTradeInput,
    OpenTradeInput,
    TradeOutput,
)
from src.domain.models.paper_trade import PaperTrade, TradeStatus, TradeType
from src.domain.repositories.trade_repository import TradeRepository


class RecordTradeUseCase:
    """
    トレード記録 ユースケース

    ペーパートレードの記録（新規ポジション、決済、キャンセル）を行う。
    """

    def __init__(self, trade_repository: TradeRepository) -> None:
        self._trade_repo = trade_repository

    async def open_position(self, input_dto: OpenTradeInput) -> TradeOutput:
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
        trade = PaperTrade.open_position(
            symbol=input_dto.symbol,
            trade_type=trade_type,
            quantity=input_dto.quantity,
            entry_price=input_dto.entry_price,
            stop_loss_price=input_dto.stop_loss_price,
            target_price=input_dto.target_price,
            notes=input_dto.notes,
        )

        # 保存
        saved_trade = await self._trade_repo.save(trade)

        return self._to_output(saved_trade)

    async def close_position(
        self,
        input_dto: CloseTradeInput,
    ) -> TradeOutput | None:
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
        existing = await self._trade_repo.get_by_id(input_dto.trade_id)
        if existing is None:
            return None

        # ステータスチェック
        if existing.status != TradeStatus.OPEN:
            raise ValueError(
                f"Trade {input_dto.trade_id} is not open. "
                f"Current status: {existing.status.value}"
            )

        # 決済
        exit_date = input_dto.exit_date or datetime.now()
        closed_trade = await self._trade_repo.close_position(
            trade_id=input_dto.trade_id,
            exit_price=input_dto.exit_price,
            exit_date=exit_date,
        )

        if closed_trade is None:
            return None

        return self._to_output(closed_trade)

    async def cancel_trade(self, trade_id: int) -> bool:
        """
        トレードをキャンセル

        Args:
            trade_id: トレードID

        Returns:
            bool: キャンセル成功したらTrue

        Raises:
            ValueError: トレードがオープン状態でない場合
        """
        existing = await self._trade_repo.get_by_id(trade_id)
        if existing is None:
            return False

        if existing.status != TradeStatus.OPEN:
            raise ValueError(
                f"Trade {trade_id} is not open. "
                f"Current status: {existing.status.value}"
            )

        return await self._trade_repo.cancel_trade(trade_id)

    async def update_trade_notes(
        self,
        trade_id: int,
        notes: str,
    ) -> TradeOutput | None:
        """
        トレードのメモを更新

        Args:
            trade_id: トレードID
            notes: 新しいメモ

        Returns:
            TradeOutput | None: 更新されたトレード、存在しない場合はNone
        """
        existing = await self._trade_repo.get_by_id(trade_id)
        if existing is None:
            return None

        # 新しいエンティティを作成（frozen dataclass のため）
        updated_trade = PaperTrade(
            id=existing.id,
            symbol=existing.symbol,
            trade_type=existing.trade_type,
            quantity=existing.quantity,
            entry_price=existing.entry_price,
            entry_date=existing.entry_date,
            exit_price=existing.exit_price,
            exit_date=existing.exit_date,
            stop_loss_price=existing.stop_loss_price,
            target_price=existing.target_price,
            status=existing.status,
            notes=notes,
            created_at=existing.created_at,
        )

        saved_trade = await self._trade_repo.update(updated_trade)
        return self._to_output(saved_trade)

    async def get_trade(self, trade_id: int) -> TradeOutput | None:
        """
        IDでトレードを取得

        Args:
            trade_id: トレードID

        Returns:
            TradeOutput | None: トレード、存在しない場合はNone
        """
        trade = await self._trade_repo.get_by_id(trade_id)
        if trade is None:
            return None
        return self._to_output(trade)

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
