"""Domain Services"""

from src.domain.services.canslim_scorer import CANSLIMScorer, CANSLIMScoreResult
from src.domain.services.canslim_score_calculator import (
    CANSLIMInput,
    CANSLIMScoreCalculator,
)
from src.domain.services.eps_growth_calculator import (
    EPSData,
    EPSGrowthCalculator,
    EPSGrowthResult,
)
from src.domain.services.market_analyzer import MarketAnalyzer
from src.domain.services.rs_calculator import PriceBar, RSCalculator
from src.domain.services.rs_rating_calculator import RSRatingCalculator
from src.domain.services.screening_service import ScreeningService

__all__ = [
    # === 新設計（Phase 2） ===
    "CANSLIMScorer",
    "CANSLIMScoreResult",
    "RSCalculator",
    "RSRatingCalculator",
    "ScreeningService",
    "PriceBar",
    # === 旧設計（Phase 4 で削除予定） ===
    "CANSLIMInput",
    "CANSLIMScoreCalculator",
    "EPSData",
    "EPSGrowthCalculator",
    "EPSGrowthResult",
    "MarketAnalyzer",
]
