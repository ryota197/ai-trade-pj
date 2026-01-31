"""ポートフォリオAPI"""

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.adapters.database import get_db
from src.adapters.yfinance import YFinanceGateway
from src.models import Trade, TradeStatus, TradeType, Watchlist, WatchlistStatus
from src.queries import TradeQuery, WatchlistQuery
from src.presentation.schemas.common import ApiResponse
from src.presentation.schemas.portfolio import (
    AddToWatchlistRequest,
    CloseTradeRequest,
    OpenPositionSchema,
    OpenTradeRequest,
    PerformanceSchema,
    TradeListResponse,
    TradeSchema,
    UpdateWatchlistRequest,
    WatchlistItemSchema,
    WatchlistResponse,
)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

# Gateway インスタンス（オープンポジションの現在価格取得用）
_gateway = YFinanceGateway()


# ========================================
# ヘルパー関数（ドメインロジックのインライン化）
# ========================================


def _calculate_risk_reward_ratio(item: Watchlist) -> float | None:
    """リスクリワード比を計算"""
    if (
        item.target_entry_price is None
        or item.stop_loss_price is None
        or item.target_price is None
    ):
        return None

    risk = item.target_entry_price - item.stop_loss_price
    reward = item.target_price - item.target_entry_price

    if risk <= 0:
        return None

    return round(reward / risk, 2)


def _calculate_potential_loss_percent(item: Watchlist) -> float | None:
    """ストップロス時の損失率を計算"""
    if item.target_entry_price is None or item.stop_loss_price is None:
        return None

    if item.target_entry_price == 0:
        return None

    loss = (item.target_entry_price - item.stop_loss_price) / item.target_entry_price * 100
    return round(loss, 2)


def _calculate_potential_gain_percent(item: Watchlist) -> float | None:
    """目標達成時の利益率を計算"""
    if item.target_entry_price is None or item.target_price is None:
        return None

    if item.target_entry_price == 0:
        return None

    gain = (item.target_price - item.target_entry_price) / item.target_entry_price * 100
    return round(gain, 2)


def _trade_profit_loss(trade: Trade) -> Decimal | None:
    """損益額を計算"""
    if trade.status != TradeStatus.CLOSED.value or trade.exit_price is None:
        return None

    entry = Decimal(str(trade.entry_price))
    exit_price = Decimal(str(trade.exit_price))

    if trade.trade_type == TradeType.BUY.value:
        return (exit_price - entry) * trade.quantity
    else:
        return (entry - exit_price) * trade.quantity


def _trade_profit_loss_percent(trade: Trade) -> Decimal | None:
    """損益率を計算"""
    if trade.status != TradeStatus.CLOSED.value or trade.exit_price is None:
        return None

    entry = Decimal(str(trade.entry_price))
    exit_price = Decimal(str(trade.exit_price))

    if trade.trade_type == TradeType.BUY.value:
        return (exit_price - entry) / entry * 100
    else:
        return (entry - exit_price) / entry * 100


def _watchlist_to_schema(item: Watchlist) -> WatchlistItemSchema:
    """Watchlistをスキーマに変換"""
    return WatchlistItemSchema(
        id=item.id,
        symbol=item.symbol,
        added_at=item.added_at,
        target_entry_price=item.target_entry_price,
        stop_loss_price=item.stop_loss_price,
        target_price=item.target_price,
        notes=item.notes,
        status=item.status,
        triggered_at=item.triggered_at,
        risk_reward_ratio=_calculate_risk_reward_ratio(item),
        potential_loss_percent=_calculate_potential_loss_percent(item),
        potential_gain_percent=_calculate_potential_gain_percent(item),
    )


def _trade_to_schema(trade: Trade) -> TradeSchema:
    """Tradeをスキーマに変換"""
    pnl = _trade_profit_loss(trade)
    pnl_pct = _trade_profit_loss_percent(trade)

    return TradeSchema(
        id=trade.id,
        symbol=trade.symbol,
        trade_type=trade.trade_type,
        quantity=trade.quantity,
        entry_price=Decimal(str(trade.entry_price)),
        status=trade.status,
        traded_at=trade.traded_at,
        exit_price=Decimal(str(trade.exit_price)) if trade.exit_price else None,
        closed_at=trade.closed_at,
        profit_loss=pnl,
        profit_loss_percent=pnl_pct,
    )


def _trade_to_open_position(trade: Trade) -> OpenPositionSchema:
    """Tradeをオープンポジションスキーマに変換"""
    current_price: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    unrealized_pnl_percent: Decimal | None = None

    try:
        quote = _gateway.get_quote(trade.symbol)
        if quote:
            current_price = Decimal(str(quote.price))
            entry = Decimal(str(trade.entry_price))
            if trade.trade_type == TradeType.BUY.value:
                unrealized_pnl = (current_price - entry) * trade.quantity
                unrealized_pnl_percent = (current_price - entry) / entry * 100
            else:
                unrealized_pnl = (entry - current_price) * trade.quantity
                unrealized_pnl_percent = (entry - current_price) / entry * 100
    except Exception:
        pass

    return OpenPositionSchema(
        id=trade.id,
        symbol=trade.symbol,
        trade_type=trade.trade_type,
        quantity=trade.quantity,
        entry_price=Decimal(str(trade.entry_price)),
        traded_at=trade.traded_at,
        current_price=current_price,
        unrealized_pnl=unrealized_pnl,
        unrealized_pnl_percent=unrealized_pnl_percent,
    )


def _calculate_performance(trades: list[Trade]) -> PerformanceSchema:
    """トレードからパフォーマンス指標を計算"""
    if not trades:
        return PerformanceSchema(
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
        pnl = _trade_profit_loss(trade)
        if pnl is None:
            continue

        total_profit_loss += pnl

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

    win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
    avg_win = float(total_wins / winning_trades) if winning_trades > 0 else 0
    avg_loss = float(total_losses / losing_trades) if losing_trades > 0 else 0
    profit_factor = float(total_wins / total_losses) if total_losses > 0 else None
    expectancy = float(total_profit_loss / total_trades) if total_trades > 0 else 0
    risk_reward = avg_win / avg_loss if avg_loss > 0 else None
    avg_holding_days = holding_days_sum / total_trades if total_trades > 0 else 0
    total_return = float(total_profit_loss)
    avg_return = total_return / total_trades if total_trades > 0 else 0

    return PerformanceSchema(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        total_profit_loss=total_return,
        total_return_percent=0.0,
        average_return_percent=avg_return,
        win_rate=win_rate,
        average_win=avg_win,
        average_loss=avg_loss,
        profit_factor=profit_factor,
        expectancy=expectancy,
        risk_reward_ratio=risk_reward,
        max_drawdown_percent=0.0,
        max_consecutive_wins=max_consecutive_wins,
        max_consecutive_losses=max_consecutive_losses,
        average_holding_days=avg_holding_days,
        is_profitable=total_profit_loss > 0,
        has_sufficient_trades=total_trades >= 20,
        calculated_at=datetime.now(),
    )


# ============================================================
# ウォッチリスト エンドポイント
# ============================================================


@router.get("/watchlist", response_model=ApiResponse[WatchlistResponse])
async def get_watchlist(
    status: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ApiResponse[WatchlistResponse]:
    """ウォッチリスト一覧を取得"""
    try:
        query = WatchlistQuery(db)

        filter_status = None
        if status:
            try:
                filter_status = WatchlistStatus(status)
            except ValueError:
                pass

        items = await query.get_all(status=filter_status, limit=limit, offset=offset)
        total_count = await query.count()
        watching_count = await query.count(WatchlistStatus.WATCHING)

        response = WatchlistResponse(
            items=[_watchlist_to_schema(item) for item in items],
            total_count=total_count,
            watching_count=watching_count,
        )

        return ApiResponse(success=True, data=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get watchlist: {e}")


@router.post("/watchlist", response_model=ApiResponse[WatchlistItemSchema])
async def add_to_watchlist(
    request: AddToWatchlistRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[WatchlistItemSchema]:
    """ウォッチリストに銘柄を追加"""
    try:
        query = WatchlistQuery(db)

        if await query.exists(request.symbol):
            raise ValueError(f"Symbol {request.symbol} already exists in watchlist")

        item = Watchlist(
            symbol=request.symbol.upper(),
            target_entry_price=request.target_entry_price,
            stop_loss_price=request.stop_loss_price,
            target_price=request.target_price,
            notes=request.notes,
            status=WatchlistStatus.WATCHING.value,
            added_at=datetime.now(timezone.utc),
        )

        saved_item = await query.save(item)
        return ApiResponse(success=True, data=_watchlist_to_schema(saved_item))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add to watchlist: {e}")


@router.put("/watchlist/{item_id}", response_model=ApiResponse[WatchlistItemSchema])
async def update_watchlist_item(
    item_id: int,
    request: UpdateWatchlistRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[WatchlistItemSchema]:
    """ウォッチリストアイテムを更新"""
    try:
        query = WatchlistQuery(db)

        existing = await query.get_by_id(item_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")

        # Update fields
        if request.target_entry_price is not None:
            existing.target_entry_price = request.target_entry_price
        if request.stop_loss_price is not None:
            existing.stop_loss_price = request.stop_loss_price
        if request.target_price is not None:
            existing.target_price = request.target_price
        if request.notes is not None:
            existing.notes = request.notes

        saved_item = await query.update(existing)
        return ApiResponse(success=True, data=_watchlist_to_schema(saved_item))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update watchlist item: {e}")


@router.delete("/watchlist/{symbol}", response_model=ApiResponse[dict])
async def remove_from_watchlist(
    symbol: str,
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """ウォッチリストから銘柄を削除"""
    try:
        query = WatchlistQuery(db)

        item = await query.get_by_symbol(symbol.upper())
        if item is None:
            raise HTTPException(status_code=404, detail=f"Symbol not found: {symbol}")

        await query.delete(item.id)
        return ApiResponse(success=True, data={"message": f"Removed {symbol}"})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove from watchlist: {e}")


# ============================================================
# トレード エンドポイント
# ============================================================


@router.get("/trades", response_model=ApiResponse[TradeListResponse])
def get_trades(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> ApiResponse[TradeListResponse]:
    """トレード一覧を取得"""
    try:
        query = TradeQuery(db)

        open_trades = query.find_open_positions()
        closed_trades = query.find_closed(limit=limit)
        all_trades = open_trades + closed_trades

        response = TradeListResponse(
            trades=[_trade_to_schema(trade) for trade in all_trades[:limit]],
            total_count=len(all_trades),
            open_count=len(open_trades),
            closed_count=len(closed_trades),
        )

        return ApiResponse(success=True, data=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trades: {e}")


@router.get("/trades/positions", response_model=ApiResponse[list[OpenPositionSchema]])
def get_open_positions(
    db: Session = Depends(get_db),
) -> ApiResponse[list[OpenPositionSchema]]:
    """オープンポジション一覧を取得"""
    try:
        query = TradeQuery(db)
        trades = query.find_open_positions()

        return ApiResponse(
            success=True,
            data=[_trade_to_open_position(trade) for trade in trades],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get open positions: {e}")


@router.post("/trades", response_model=ApiResponse[TradeSchema])
def open_trade(
    request: OpenTradeRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[TradeSchema]:
    """新規ポジションを開く"""
    try:
        query = TradeQuery(db)

        try:
            trade_type = TradeType(request.trade_type)
        except ValueError:
            raise ValueError(f"Invalid trade type: {request.trade_type}")

        trade = Trade(
            symbol=request.symbol.upper(),
            trade_type=trade_type.value,
            quantity=request.quantity,
            entry_price=float(request.entry_price),
            status=TradeStatus.OPEN.value,
            traded_at=datetime.now(timezone.utc),
        )

        saved_trade = query.save(trade)
        return ApiResponse(success=True, data=_trade_to_schema(saved_trade))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open trade: {e}")


@router.post("/trades/{trade_id}/close", response_model=ApiResponse[TradeSchema])
def close_trade(
    trade_id: int,
    request: CloseTradeRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[TradeSchema]:
    """ポジションを決済"""
    try:
        query = TradeQuery(db)

        trade = query.find_by_id(trade_id)
        if trade is None:
            raise HTTPException(status_code=404, detail=f"Trade not found: {trade_id}")

        if trade.status != TradeStatus.OPEN.value:
            raise ValueError("Can only close open trades")

        trade.exit_price = float(request.exit_price)
        trade.status = TradeStatus.CLOSED.value
        trade.closed_at = datetime.now(timezone.utc)

        saved_trade = query.save(trade)
        return ApiResponse(success=True, data=_trade_to_schema(saved_trade))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close trade: {e}")


@router.delete("/trades/{trade_id}", response_model=ApiResponse[dict])
def cancel_trade(
    trade_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """トレードをキャンセル"""
    try:
        query = TradeQuery(db)

        trade = query.find_by_id(trade_id)
        if trade is None:
            raise HTTPException(status_code=404, detail=f"Trade not found: {trade_id}")

        if trade.status != TradeStatus.OPEN.value:
            raise ValueError("Can only cancel open trades")

        trade.status = TradeStatus.CANCELLED.value
        trade.closed_at = datetime.now(timezone.utc)

        query.save(trade)
        return ApiResponse(success=True, data={"message": f"Trade {trade_id} cancelled"})

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel trade: {e}")


# ============================================================
# パフォーマンス エンドポイント
# ============================================================


@router.get("/performance", response_model=ApiResponse[PerformanceSchema])
def get_performance(
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
) -> ApiResponse[PerformanceSchema]:
    """パフォーマンス指標を取得"""
    try:
        query = TradeQuery(db)
        trades = query.find_closed(limit=limit)

        return ApiResponse(success=True, data=_calculate_performance(trades))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance: {e}")
