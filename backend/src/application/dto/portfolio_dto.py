"""ポートフォリオ関連 DTO"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


# ============================================================
# ウォッチリスト 入力DTO
# ============================================================


@dataclass(frozen=True)
class AddToWatchlistInput:
    """ウォッチリスト追加 入力DTO"""

    symbol: str
    target_entry_price: float | None = None
    stop_loss_price: float | None = None
    target_price: float | None = None
    notes: str | None = None


@dataclass(frozen=True)
class UpdateWatchlistInput:
    """ウォッチリスト更新 入力DTO"""

    item_id: int
    target_entry_price: float | None = None
    stop_loss_price: float | None = None
    target_price: float | None = None
    notes: str | None = None


@dataclass(frozen=True)
class WatchlistFilterInput:
    """ウォッチリスト取得 入力DTO"""

    status: str | None = None  # watching, triggered, expired, removed
    limit: int = 100
    offset: int = 0


# ============================================================
# トレード 入力DTO
# ============================================================


@dataclass(frozen=True)
class OpenTradeInput:
    """新規トレード（ポジションオープン）入力DTO"""

    symbol: str
    trade_type: str  # buy, sell
    quantity: int
    entry_price: Decimal


@dataclass(frozen=True)
class CloseTradeInput:
    """トレード決済 入力DTO"""

    trade_id: int
    exit_price: Decimal


# ============================================================
# ウォッチリスト 出力DTO
# ============================================================


@dataclass(frozen=True)
class WatchlistItemOutput:
    """ウォッチリストアイテム 出力DTO"""

    id: int
    symbol: str
    added_at: datetime
    target_entry_price: float | None
    stop_loss_price: float | None
    target_price: float | None
    notes: str | None
    status: str
    triggered_at: datetime | None
    risk_reward_ratio: float | None
    potential_loss_percent: float | None
    potential_gain_percent: float | None


@dataclass(frozen=True)
class WatchlistOutput:
    """ウォッチリスト一覧 出力DTO"""

    items: list[WatchlistItemOutput]
    total_count: int
    watching_count: int


# ============================================================
# トレード 出力DTO
# ============================================================


@dataclass(frozen=True)
class TradeOutput:
    """トレード 出力DTO"""

    symbol: str
    trade_type: str
    quantity: int
    entry_price: Decimal
    status: str
    traded_at: datetime
    id: int | None = None  # 新規作成直後はNone（DBから再取得後に設定される）
    exit_price: Decimal | None = None
    closed_at: datetime | None = None
    profit_loss: Decimal | None = None
    profit_loss_percent: Decimal | None = None


@dataclass(frozen=True)
class TradeListOutput:
    """トレード一覧 出力DTO"""

    trades: list[TradeOutput]
    total_count: int
    open_count: int
    closed_count: int


@dataclass(frozen=True)
class OpenPositionOutput:
    """オープンポジション 出力DTO"""

    symbol: str
    trade_type: str
    quantity: int
    entry_price: Decimal
    traded_at: datetime
    id: int | None = None
    # 含み損益（現在価格が必要なので別途計算）
    current_price: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    unrealized_pnl_percent: Decimal | None = None


# ============================================================
# パフォーマンス 出力DTO
# ============================================================


@dataclass(frozen=True)
class PerformanceOutput:
    """パフォーマンス 出力DTO"""

    # 基本統計
    total_trades: int
    winning_trades: int
    losing_trades: int
    # 損益
    total_profit_loss: float
    total_return_percent: float
    average_return_percent: float
    # 勝率・期待値
    win_rate: float
    average_win: float
    average_loss: float
    profit_factor: float | None
    expectancy: float
    risk_reward_ratio: float | None
    # リスク指標
    max_drawdown_percent: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    # 期間
    average_holding_days: float
    # メタ情報
    is_profitable: bool
    has_sufficient_trades: bool
    calculated_at: datetime
