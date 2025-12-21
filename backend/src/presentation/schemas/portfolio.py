"""ポートフォリオ関連スキーマ"""

from datetime import datetime

from pydantic import BaseModel, Field


# ============================================================
# ウォッチリスト リクエストスキーマ
# ============================================================


class AddToWatchlistRequest(BaseModel):
    """ウォッチリスト追加リクエスト"""

    symbol: str = Field(..., min_length=1, max_length=10, description="ティッカーシンボル")
    target_entry_price: float | None = Field(None, gt=0, description="目標エントリー価格")
    stop_loss_price: float | None = Field(None, gt=0, description="ストップロス価格")
    target_price: float | None = Field(None, gt=0, description="目標利確価格")
    notes: str | None = Field(None, max_length=1000, description="メモ")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "NVDA",
                "target_entry_price": 440.00,
                "stop_loss_price": 420.00,
                "target_price": 500.00,
                "notes": "CAN-SLIM条件クリア、ブレイクアウト待ち",
            }
        }
    }


class UpdateWatchlistRequest(BaseModel):
    """ウォッチリスト更新リクエスト"""

    target_entry_price: float | None = Field(None, gt=0, description="目標エントリー価格")
    stop_loss_price: float | None = Field(None, gt=0, description="ストップロス価格")
    target_price: float | None = Field(None, gt=0, description="目標利確価格")
    notes: str | None = Field(None, max_length=1000, description="メモ")


# ============================================================
# ウォッチリスト レスポンススキーマ
# ============================================================


class WatchlistItemSchema(BaseModel):
    """ウォッチリストアイテムスキーマ"""

    id: int = Field(..., description="アイテムID")
    symbol: str = Field(..., description="ティッカーシンボル")
    added_at: datetime = Field(..., description="追加日時")
    target_entry_price: float | None = Field(None, description="目標エントリー価格")
    stop_loss_price: float | None = Field(None, description="ストップロス価格")
    target_price: float | None = Field(None, description="目標利確価格")
    notes: str | None = Field(None, description="メモ")
    status: str = Field(..., description="ステータス")
    triggered_at: datetime | None = Field(None, description="トリガー日時")
    risk_reward_ratio: float | None = Field(None, description="リスクリワード比")
    potential_loss_percent: float | None = Field(None, description="潜在損失率（%）")
    potential_gain_percent: float | None = Field(None, description="潜在利益率（%）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "symbol": "NVDA",
                "added_at": "2024-01-15T10:30:00Z",
                "target_entry_price": 440.00,
                "stop_loss_price": 420.00,
                "target_price": 500.00,
                "notes": "CAN-SLIM条件クリア",
                "status": "watching",
                "triggered_at": None,
                "risk_reward_ratio": 3.0,
                "potential_loss_percent": 4.55,
                "potential_gain_percent": 13.64,
            }
        }
    }


class WatchlistResponse(BaseModel):
    """ウォッチリスト一覧レスポンス"""

    items: list[WatchlistItemSchema] = Field(..., description="アイテムリスト")
    total_count: int = Field(..., description="総件数")
    watching_count: int = Field(..., description="監視中件数")


# ============================================================
# トレード リクエストスキーマ
# ============================================================


class OpenTradeRequest(BaseModel):
    """新規トレードリクエスト"""

    symbol: str = Field(..., min_length=1, max_length=10, description="ティッカーシンボル")
    trade_type: str = Field(..., pattern="^(buy|sell)$", description="売買タイプ（buy/sell）")
    quantity: int = Field(..., gt=0, description="数量")
    entry_price: float = Field(..., gt=0, description="エントリー価格")
    stop_loss_price: float | None = Field(None, gt=0, description="ストップロス価格")
    target_price: float | None = Field(None, gt=0, description="目標価格")
    notes: str | None = Field(None, max_length=1000, description="メモ")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "AAPL",
                "trade_type": "buy",
                "quantity": 10,
                "entry_price": 180.00,
                "stop_loss_price": 170.00,
                "target_price": 200.00,
                "notes": "ブレイクアウトエントリー",
            }
        }
    }


class CloseTradeRequest(BaseModel):
    """トレード決済リクエスト"""

    exit_price: float = Field(..., gt=0, description="決済価格")

    model_config = {
        "json_schema_extra": {
            "example": {
                "exit_price": 195.00,
            }
        }
    }


# ============================================================
# トレード レスポンススキーマ
# ============================================================


class TradeSchema(BaseModel):
    """トレードスキーマ"""

    id: int = Field(..., description="トレードID")
    symbol: str = Field(..., description="ティッカーシンボル")
    trade_type: str = Field(..., description="売買タイプ")
    quantity: int = Field(..., description="数量")
    entry_price: float = Field(..., description="エントリー価格")
    entry_date: datetime = Field(..., description="エントリー日時")
    exit_price: float | None = Field(None, description="決済価格")
    exit_date: datetime | None = Field(None, description="決済日時")
    stop_loss_price: float | None = Field(None, description="ストップロス価格")
    target_price: float | None = Field(None, description="目標価格")
    status: str = Field(..., description="ステータス")
    notes: str | None = Field(None, description="メモ")
    created_at: datetime = Field(..., description="作成日時")
    position_value: float = Field(..., description="ポジション価値")
    profit_loss: float | None = Field(None, description="損益額")
    return_percent: float | None = Field(None, description="リターン率（%）")
    holding_days: int | None = Field(None, description="保有日数")
    is_winner: bool | None = Field(None, description="勝ちトレードか")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "symbol": "AAPL",
                "trade_type": "buy",
                "quantity": 10,
                "entry_price": 180.00,
                "entry_date": "2024-01-10T10:00:00Z",
                "exit_price": 195.00,
                "exit_date": "2024-01-20T14:00:00Z",
                "stop_loss_price": 170.00,
                "target_price": 200.00,
                "status": "closed",
                "notes": "ブレイクアウトエントリー",
                "created_at": "2024-01-10T10:00:00Z",
                "position_value": 1800.00,
                "profit_loss": 150.00,
                "return_percent": 8.33,
                "holding_days": 10,
                "is_winner": True,
            }
        }
    }


class TradeListResponse(BaseModel):
    """トレード一覧レスポンス"""

    trades: list[TradeSchema] = Field(..., description="トレードリスト")
    total_count: int = Field(..., description="総件数")
    open_count: int = Field(..., description="オープン件数")
    closed_count: int = Field(..., description="クローズ件数")


class OpenPositionSchema(BaseModel):
    """オープンポジションスキーマ"""

    id: int = Field(..., description="トレードID")
    symbol: str = Field(..., description="ティッカーシンボル")
    trade_type: str = Field(..., description="売買タイプ")
    quantity: int = Field(..., description="数量")
    entry_price: float = Field(..., description="エントリー価格")
    entry_date: datetime = Field(..., description="エントリー日時")
    stop_loss_price: float | None = Field(None, description="ストップロス価格")
    target_price: float | None = Field(None, description="目標価格")
    position_value: float = Field(..., description="ポジション価値")
    holding_days: int = Field(..., description="保有日数")
    current_price: float | None = Field(None, description="現在価格")
    unrealized_pnl: float | None = Field(None, description="含み損益額")
    unrealized_return_percent: float | None = Field(None, description="含み損益率（%）")


# ============================================================
# パフォーマンス レスポンススキーマ
# ============================================================


class PerformanceSchema(BaseModel):
    """パフォーマンススキーマ"""

    total_trades: int = Field(..., description="総トレード数")
    winning_trades: int = Field(..., description="勝ちトレード数")
    losing_trades: int = Field(..., description="負けトレード数")
    total_profit_loss: float = Field(..., description="総損益額")
    total_return_percent: float = Field(..., description="総リターン率（%）")
    average_return_percent: float = Field(..., description="平均リターン率（%）")
    win_rate: float = Field(..., description="勝率（%）")
    average_win: float = Field(..., description="平均勝ち額")
    average_loss: float = Field(..., description="平均負け額")
    profit_factor: float | None = Field(None, description="プロフィットファクター")
    expectancy: float = Field(..., description="期待値")
    risk_reward_ratio: float | None = Field(None, description="リスクリワード比")
    max_drawdown_percent: float = Field(..., description="最大ドローダウン（%）")
    max_consecutive_wins: int = Field(..., description="最大連勝数")
    max_consecutive_losses: int = Field(..., description="最大連敗数")
    average_holding_days: float = Field(..., description="平均保有日数")
    is_profitable: bool = Field(..., description="利益が出ているか")
    has_sufficient_trades: bool = Field(..., description="統計的に有意なトレード数か")
    calculated_at: datetime = Field(..., description="計算日時")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_trades": 25,
                "winning_trades": 18,
                "losing_trades": 7,
                "total_profit_loss": 2500.00,
                "total_return_percent": 12.5,
                "average_return_percent": 8.5,
                "win_rate": 72.0,
                "average_win": 200.00,
                "average_loss": 100.00,
                "profit_factor": 2.5,
                "expectancy": 100.00,
                "risk_reward_ratio": 2.0,
                "max_drawdown_percent": 5.2,
                "max_consecutive_wins": 5,
                "max_consecutive_losses": 2,
                "average_holding_days": 8.5,
                "is_profitable": True,
                "has_sufficient_trades": False,
                "calculated_at": "2024-01-15T10:30:00Z",
            }
        }
    }


class MonthlyReturnSchema(BaseModel):
    """月別リターンスキーマ"""

    month: str = Field(..., description="月（YYYY-MM）")
    return_percent: float = Field(..., description="リターン率（%）")
    trade_count: int = Field(..., description="トレード数")


class SymbolStatsSchema(BaseModel):
    """シンボル別統計スキーマ"""

    symbol: str = Field(..., description="ティッカーシンボル")
    total_trades: int = Field(..., description="トレード数")
    winning_trades: int = Field(..., description="勝ちトレード数")
    total_profit_loss: float = Field(..., description="総損益")
    win_rate: float = Field(..., description="勝率（%）")


class DetailedPerformanceResponse(BaseModel):
    """詳細パフォーマンスレスポンス"""

    summary: PerformanceSchema = Field(..., description="サマリー")
    monthly_returns: list[MonthlyReturnSchema] = Field(..., description="月別リターン")
    symbol_stats: list[SymbolStatsSchema] = Field(..., description="シンボル別統計")
