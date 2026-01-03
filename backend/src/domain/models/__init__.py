"""Domain Models（Entity / Value Object）"""

from src.domain.models.canslim_config import CANSLIMScoreThresholds, CANSLIMWeights
from src.domain.models.canslim_score import CANSLIMCriteria, CANSLIMScore, ScoreGrade
from src.domain.models.canslim_stock import CANSLIMStock
from src.domain.models.market_benchmark import MarketBenchmark
from src.domain.models.market_indicators import (
    MarketIndicators,
    MovingAverageIndicator,
    PutCallRatioIndicator,
    RsiIndicator,
    SignalType,
    VixIndicator,
)
from src.domain.models.market_snapshot import (
    MarketCondition,
    MarketSnapshot,
    Signal,
)
from src.domain.models.market_status import MarketStatus
from src.domain.models.paper_trade import PaperTrade
from src.domain.models.performance_metrics import PerformanceMetrics
from src.domain.models.price_snapshot import PriceSnapshot
from src.domain.models.quote import HistoricalPrice, Quote
from src.domain.models.screening_criteria import ScreeningCriteria
from src.domain.models.stock_identity import StockIdentity
from src.domain.models.stock_metrics import StockMetrics
from src.domain.models.trade import Trade, TradeStatus, TradeType
from src.domain.models.watchlist_item import WatchlistItem

__all__ = [
    # === 新設計（Phase 1） ===
    "CANSLIMStock",
    "ScreeningCriteria",
    # === 新設計（Phase 3） ===
    "Trade",
    "TradeType",
    "TradeStatus",
    "MarketSnapshot",
    "MarketCondition",
    "Signal",
    "WatchlistItem",
    # === 旧設計（Phase 4 で削除予定） ===
    # 銘柄関連（Entity / Value Object）
    "StockIdentity",
    "PriceSnapshot",
    "StockMetrics",
    # 価格関連
    "Quote",
    "HistoricalPrice",
    # マーケット関連
    "MarketBenchmark",
    "MarketStatus",
    "MarketIndicators",
    "VixIndicator",
    "RsiIndicator",
    "MovingAverageIndicator",
    "PutCallRatioIndicator",
    "SignalType",
    # CAN-SLIM関連
    "CANSLIMWeights",
    "CANSLIMScoreThresholds",
    "CANSLIMScore",
    "CANSLIMCriteria",
    "ScoreGrade",
    # パフォーマンス
    "PerformanceMetrics",
    # ウォッチリスト・ペーパートレード
    "PaperTrade",
]
