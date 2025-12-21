"""ポートフォリオAPI"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from src.application.dto.portfolio_dto import (
    AddToWatchlistInput,
    CloseTradeInput,
    OpenTradeInput,
    PerformanceInput,
    TradeFilterInput,
    UpdateWatchlistInput,
    WatchlistFilterInput,
)
from src.application.use_cases.portfolio import (
    GetPerformanceUseCase,
    GetTradesUseCase,
    ManageWatchlistUseCase,
    RecordTradeUseCase,
)
from src.presentation.dependencies import (
    get_manage_watchlist_use_case,
    get_record_trade_use_case,
    get_trades_use_case,
    get_performance_use_case,
)
from src.presentation.schemas.common import ApiResponse
from src.presentation.schemas.portfolio import (
    AddToWatchlistRequest,
    CloseTradeRequest,
    DetailedPerformanceResponse,
    MonthlyReturnSchema,
    OpenPositionSchema,
    OpenTradeRequest,
    PerformanceSchema,
    SymbolStatsSchema,
    TradeListResponse,
    TradeSchema,
    UpdateWatchlistRequest,
    WatchlistItemSchema,
    WatchlistResponse,
)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


# ============================================================
# ウォッチリスト エンドポイント
# ============================================================


@router.get(
    "/watchlist",
    response_model=ApiResponse[WatchlistResponse],
    summary="ウォッチリスト一覧取得",
    description="ウォッチリストに登録された銘柄一覧を取得する",
)
async def get_watchlist(
    status: str | None = Query(None, description="ステータスでフィルタ"),
    limit: int = Query(100, ge=1, le=500, description="取得件数"),
    offset: int = Query(0, ge=0, description="オフセット"),
    use_case: ManageWatchlistUseCase = Depends(get_manage_watchlist_use_case),
) -> ApiResponse[WatchlistResponse]:
    """ウォッチリスト一覧を取得"""
    try:
        filter_input = WatchlistFilterInput(
            status=status,
            limit=limit,
            offset=offset,
        )

        result = await use_case.get_watchlist(filter_input)

        items_schema = [
            WatchlistItemSchema(
                id=item.id,
                symbol=item.symbol,
                added_at=item.added_at,
                target_entry_price=item.target_entry_price,
                stop_loss_price=item.stop_loss_price,
                target_price=item.target_price,
                notes=item.notes,
                status=item.status,
                triggered_at=item.triggered_at,
                risk_reward_ratio=item.risk_reward_ratio,
                potential_loss_percent=item.potential_loss_percent,
                potential_gain_percent=item.potential_gain_percent,
            )
            for item in result.items
        ]

        response = WatchlistResponse(
            items=items_schema,
            total_count=result.total_count,
            watching_count=result.watching_count,
        )

        return ApiResponse(success=True, data=response)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get watchlist: {e}",
        )


@router.post(
    "/watchlist",
    response_model=ApiResponse[WatchlistItemSchema],
    summary="ウォッチリスト追加",
    description="銘柄をウォッチリストに追加する",
)
async def add_to_watchlist(
    request: AddToWatchlistRequest,
    use_case: ManageWatchlistUseCase = Depends(get_manage_watchlist_use_case),
) -> ApiResponse[WatchlistItemSchema]:
    """ウォッチリストに銘柄を追加"""
    try:
        input_dto = AddToWatchlistInput(
            symbol=request.symbol,
            target_entry_price=request.target_entry_price,
            stop_loss_price=request.stop_loss_price,
            target_price=request.target_price,
            notes=request.notes,
        )

        result = await use_case.add_to_watchlist(input_dto)

        response = WatchlistItemSchema(
            id=result.id,
            symbol=result.symbol,
            added_at=result.added_at,
            target_entry_price=result.target_entry_price,
            stop_loss_price=result.stop_loss_price,
            target_price=result.target_price,
            notes=result.notes,
            status=result.status,
            triggered_at=result.triggered_at,
            risk_reward_ratio=result.risk_reward_ratio,
            potential_loss_percent=result.potential_loss_percent,
            potential_gain_percent=result.potential_gain_percent,
        )

        return ApiResponse(success=True, data=response)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add to watchlist: {e}",
        )


@router.put(
    "/watchlist/{item_id}",
    response_model=ApiResponse[WatchlistItemSchema],
    summary="ウォッチリスト更新",
    description="ウォッチリストアイテムを更新する",
)
async def update_watchlist_item(
    item_id: int,
    request: UpdateWatchlistRequest,
    use_case: ManageWatchlistUseCase = Depends(get_manage_watchlist_use_case),
) -> ApiResponse[WatchlistItemSchema]:
    """ウォッチリストアイテムを更新"""
    try:
        input_dto = UpdateWatchlistInput(
            item_id=item_id,
            target_entry_price=request.target_entry_price,
            stop_loss_price=request.stop_loss_price,
            target_price=request.target_price,
            notes=request.notes,
        )

        result = await use_case.update_watchlist_item(input_dto)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Watchlist item not found: {item_id}",
            )

        response = WatchlistItemSchema(
            id=result.id,
            symbol=result.symbol,
            added_at=result.added_at,
            target_entry_price=result.target_entry_price,
            stop_loss_price=result.stop_loss_price,
            target_price=result.target_price,
            notes=result.notes,
            status=result.status,
            triggered_at=result.triggered_at,
            risk_reward_ratio=result.risk_reward_ratio,
            potential_loss_percent=result.potential_loss_percent,
            potential_gain_percent=result.potential_gain_percent,
        )

        return ApiResponse(success=True, data=response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update watchlist item: {e}",
        )


@router.delete(
    "/watchlist/{symbol}",
    response_model=ApiResponse[dict],
    summary="ウォッチリスト削除",
    description="銘柄をウォッチリストから削除する",
)
async def remove_from_watchlist(
    symbol: str,
    use_case: ManageWatchlistUseCase = Depends(get_manage_watchlist_use_case),
) -> ApiResponse[dict]:
    """ウォッチリストから銘柄を削除"""
    try:
        success = await use_case.remove_from_watchlist(symbol)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Symbol not found in watchlist: {symbol}",
            )

        return ApiResponse(
            success=True,
            data={"message": f"Removed {symbol} from watchlist"},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove from watchlist: {e}",
        )


# ============================================================
# トレード エンドポイント
# ============================================================


@router.get(
    "/trades",
    response_model=ApiResponse[TradeListResponse],
    summary="トレード一覧取得",
    description="トレード履歴を取得する",
)
async def get_trades(
    status: str | None = Query(None, description="ステータスでフィルタ（open/closed/cancelled）"),
    trade_type: str | None = Query(None, description="売買タイプでフィルタ（buy/sell）"),
    symbol: str | None = Query(None, description="シンボルでフィルタ"),
    limit: int = Query(100, ge=1, le=500, description="取得件数"),
    offset: int = Query(0, ge=0, description="オフセット"),
    use_case: GetTradesUseCase = Depends(get_trades_use_case),
) -> ApiResponse[TradeListResponse]:
    """トレード一覧を取得"""
    try:
        filter_input = TradeFilterInput(
            status=status,
            trade_type=trade_type,
            symbol=symbol,
            limit=limit,
            offset=offset,
        )

        result = await use_case.get_trades(filter_input)

        trades_schema = [
            TradeSchema(
                id=trade.id,
                symbol=trade.symbol,
                trade_type=trade.trade_type,
                quantity=trade.quantity,
                entry_price=trade.entry_price,
                entry_date=trade.entry_date,
                exit_price=trade.exit_price,
                exit_date=trade.exit_date,
                stop_loss_price=trade.stop_loss_price,
                target_price=trade.target_price,
                status=trade.status,
                notes=trade.notes,
                created_at=trade.created_at,
                position_value=trade.position_value,
                profit_loss=trade.profit_loss,
                return_percent=trade.return_percent,
                holding_days=trade.holding_days,
                is_winner=trade.is_winner,
            )
            for trade in result.trades
        ]

        response = TradeListResponse(
            trades=trades_schema,
            total_count=result.total_count,
            open_count=result.open_count,
            closed_count=result.closed_count,
        )

        return ApiResponse(success=True, data=response)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get trades: {e}",
        )


@router.get(
    "/trades/positions",
    response_model=ApiResponse[list[OpenPositionSchema]],
    summary="オープンポジション取得",
    description="現在のオープンポジション一覧を取得する",
)
async def get_open_positions(
    use_case: GetTradesUseCase = Depends(get_trades_use_case),
) -> ApiResponse[list[OpenPositionSchema]]:
    """オープンポジション一覧を取得"""
    try:
        result = await use_case.get_open_positions()

        positions_schema = [
            OpenPositionSchema(
                id=pos.id,
                symbol=pos.symbol,
                trade_type=pos.trade_type,
                quantity=pos.quantity,
                entry_price=pos.entry_price,
                entry_date=pos.entry_date,
                stop_loss_price=pos.stop_loss_price,
                target_price=pos.target_price,
                position_value=pos.position_value,
                holding_days=pos.holding_days,
                current_price=pos.current_price,
                unrealized_pnl=pos.unrealized_pnl,
                unrealized_return_percent=pos.unrealized_return_percent,
            )
            for pos in result
        ]

        return ApiResponse(success=True, data=positions_schema)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get open positions: {e}",
        )


@router.post(
    "/trades",
    response_model=ApiResponse[TradeSchema],
    summary="新規トレード記録",
    description="新規ポジションを開く（ペーパートレード）",
)
async def open_trade(
    request: OpenTradeRequest,
    use_case: RecordTradeUseCase = Depends(get_record_trade_use_case),
) -> ApiResponse[TradeSchema]:
    """新規ポジションを開く"""
    try:
        input_dto = OpenTradeInput(
            symbol=request.symbol,
            trade_type=request.trade_type,
            quantity=request.quantity,
            entry_price=request.entry_price,
            stop_loss_price=request.stop_loss_price,
            target_price=request.target_price,
            notes=request.notes,
        )

        result = await use_case.open_position(input_dto)

        response = TradeSchema(
            id=result.id,
            symbol=result.symbol,
            trade_type=result.trade_type,
            quantity=result.quantity,
            entry_price=result.entry_price,
            entry_date=result.entry_date,
            exit_price=result.exit_price,
            exit_date=result.exit_date,
            stop_loss_price=result.stop_loss_price,
            target_price=result.target_price,
            status=result.status,
            notes=result.notes,
            created_at=result.created_at,
            position_value=result.position_value,
            profit_loss=result.profit_loss,
            return_percent=result.return_percent,
            holding_days=result.holding_days,
            is_winner=result.is_winner,
        )

        return ApiResponse(success=True, data=response)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to open trade: {e}",
        )


@router.post(
    "/trades/{trade_id}/close",
    response_model=ApiResponse[TradeSchema],
    summary="トレード決済",
    description="ポジションを決済する",
)
async def close_trade(
    trade_id: int,
    request: CloseTradeRequest,
    use_case: RecordTradeUseCase = Depends(get_record_trade_use_case),
) -> ApiResponse[TradeSchema]:
    """ポジションを決済"""
    try:
        input_dto = CloseTradeInput(
            trade_id=trade_id,
            exit_price=request.exit_price,
        )

        result = await use_case.close_position(input_dto)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Trade not found: {trade_id}",
            )

        response = TradeSchema(
            id=result.id,
            symbol=result.symbol,
            trade_type=result.trade_type,
            quantity=result.quantity,
            entry_price=result.entry_price,
            entry_date=result.entry_date,
            exit_price=result.exit_price,
            exit_date=result.exit_date,
            stop_loss_price=result.stop_loss_price,
            target_price=result.target_price,
            status=result.status,
            notes=result.notes,
            created_at=result.created_at,
            position_value=result.position_value,
            profit_loss=result.profit_loss,
            return_percent=result.return_percent,
            holding_days=result.holding_days,
            is_winner=result.is_winner,
        )

        return ApiResponse(success=True, data=response)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to close trade: {e}",
        )


@router.delete(
    "/trades/{trade_id}",
    response_model=ApiResponse[dict],
    summary="トレードキャンセル",
    description="オープンポジションをキャンセルする",
)
async def cancel_trade(
    trade_id: int,
    use_case: RecordTradeUseCase = Depends(get_record_trade_use_case),
) -> ApiResponse[dict]:
    """トレードをキャンセル"""
    try:
        success = await use_case.cancel_trade(trade_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Trade not found: {trade_id}",
            )

        return ApiResponse(
            success=True,
            data={"message": f"Trade {trade_id} cancelled"},
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel trade: {e}",
        )


# ============================================================
# パフォーマンス エンドポイント
# ============================================================


@router.get(
    "/performance",
    response_model=ApiResponse[PerformanceSchema],
    summary="パフォーマンス取得",
    description="トレードパフォーマンス指標を取得する",
)
async def get_performance(
    start_date: datetime | None = Query(None, description="開始日"),
    end_date: datetime | None = Query(None, description="終了日"),
    use_case: GetPerformanceUseCase = Depends(get_performance_use_case),
) -> ApiResponse[PerformanceSchema]:
    """パフォーマンス指標を取得"""
    try:
        input_dto = PerformanceInput(
            start_date=start_date,
            end_date=end_date,
        )

        result = await use_case.get_performance(input_dto)

        response = PerformanceSchema(
            total_trades=result.total_trades,
            winning_trades=result.winning_trades,
            losing_trades=result.losing_trades,
            total_profit_loss=result.total_profit_loss,
            total_return_percent=result.total_return_percent,
            average_return_percent=result.average_return_percent,
            win_rate=result.win_rate,
            average_win=result.average_win,
            average_loss=result.average_loss,
            profit_factor=result.profit_factor,
            expectancy=result.expectancy,
            risk_reward_ratio=result.risk_reward_ratio,
            max_drawdown_percent=result.max_drawdown_percent,
            max_consecutive_wins=result.max_consecutive_wins,
            max_consecutive_losses=result.max_consecutive_losses,
            average_holding_days=result.average_holding_days,
            is_profitable=result.is_profitable,
            has_sufficient_trades=result.has_sufficient_trades,
            calculated_at=result.calculated_at,
        )

        return ApiResponse(success=True, data=response)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance: {e}",
        )


@router.get(
    "/performance/detailed",
    response_model=ApiResponse[DetailedPerformanceResponse],
    summary="詳細パフォーマンス取得",
    description="月別リターン、シンボル別統計を含む詳細パフォーマンスを取得する",
)
async def get_detailed_performance(
    start_date: datetime | None = Query(None, description="開始日"),
    end_date: datetime | None = Query(None, description="終了日"),
    use_case: GetPerformanceUseCase = Depends(get_performance_use_case),
) -> ApiResponse[DetailedPerformanceResponse]:
    """詳細パフォーマンスを取得"""
    try:
        input_dto = PerformanceInput(
            start_date=start_date,
            end_date=end_date,
        )

        result = await use_case.get_detailed_performance(input_dto)

        summary_schema = PerformanceSchema(
            total_trades=result.summary.total_trades,
            winning_trades=result.summary.winning_trades,
            losing_trades=result.summary.losing_trades,
            total_profit_loss=result.summary.total_profit_loss,
            total_return_percent=result.summary.total_return_percent,
            average_return_percent=result.summary.average_return_percent,
            win_rate=result.summary.win_rate,
            average_win=result.summary.average_win,
            average_loss=result.summary.average_loss,
            profit_factor=result.summary.profit_factor,
            expectancy=result.summary.expectancy,
            risk_reward_ratio=result.summary.risk_reward_ratio,
            max_drawdown_percent=result.summary.max_drawdown_percent,
            max_consecutive_wins=result.summary.max_consecutive_wins,
            max_consecutive_losses=result.summary.max_consecutive_losses,
            average_holding_days=result.summary.average_holding_days,
            is_profitable=result.summary.is_profitable,
            has_sufficient_trades=result.summary.has_sufficient_trades,
            calculated_at=result.summary.calculated_at,
        )

        monthly_schema = [
            MonthlyReturnSchema(
                month=mr.month,
                return_percent=mr.return_percent,
                trade_count=mr.trade_count,
            )
            for mr in result.monthly_returns
        ]

        symbol_schema = [
            SymbolStatsSchema(
                symbol=ss.symbol,
                total_trades=ss.total_trades,
                winning_trades=ss.winning_trades,
                total_profit_loss=ss.total_profit_loss,
                win_rate=ss.win_rate,
            )
            for ss in result.symbol_stats
        ]

        response = DetailedPerformanceResponse(
            summary=summary_schema,
            monthly_returns=monthly_schema,
            symbol_stats=symbol_schema,
        )

        return ApiResponse(success=True, data=response)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get detailed performance: {e}",
        )
