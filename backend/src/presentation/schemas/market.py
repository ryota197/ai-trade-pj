"""マーケット関連スキーマ"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MarketIndicatorsResponse(BaseModel):
    """マーケット指標レスポンス"""

    vix: float = Field(..., description="VIX指数")
    vix_signal: Literal["bullish", "neutral", "bearish"] = Field(
        ..., description="VIXシグナル"
    )

    sp500_price: float = Field(..., description="S&P500現在価格")
    sp500_rsi: float = Field(..., ge=0, le=100, description="S&P500 RSI")
    sp500_rsi_signal: Literal["bullish", "neutral", "bearish"] = Field(
        ..., description="RSIシグナル"
    )
    sp500_ma200: float = Field(..., description="S&P500 200日移動平均")
    sp500_above_ma200: bool = Field(..., description="200MAを上回っているか")

    put_call_ratio: float = Field(..., description="Put/Call Ratio")
    put_call_signal: Literal["bullish", "neutral", "bearish"] = Field(
        ..., description="Put/Call Ratioシグナル"
    )

    retrieved_at: datetime = Field(..., description="データ取得日時")

    model_config = {
        "json_schema_extra": {
            "example": {
                "vix": 15.2,
                "vix_signal": "bullish",
                "sp500_price": 5200.50,
                "sp500_rsi": 62.5,
                "sp500_rsi_signal": "bullish",
                "sp500_ma200": 4850.00,
                "sp500_above_ma200": True,
                "put_call_ratio": 0.85,
                "put_call_signal": "neutral",
                "retrieved_at": "2024-01-15T10:30:00Z",
            }
        }
    }


class MarketStatusResponse(BaseModel):
    """マーケット状態レスポンス"""

    condition: Literal["risk_on", "risk_off", "neutral"] = Field(
        ..., description="マーケット状態"
    )
    condition_label: str = Field(..., description="マーケット状態ラベル")
    confidence: float = Field(..., ge=0, le=1, description="確信度")
    score: int = Field(..., ge=-5, le=5, description="総合スコア")
    recommendation: str = Field(..., description="推奨アクション")

    indicators: MarketIndicatorsResponse = Field(..., description="各種指標")
    analyzed_at: datetime = Field(..., description="分析日時")

    model_config = {
        "json_schema_extra": {
            "example": {
                "condition": "risk_on",
                "condition_label": "Risk On",
                "confidence": 0.75,
                "score": 3,
                "recommendation": "市場環境は良好。個別株のエントリー検討可。",
                "indicators": {
                    "vix": 15.2,
                    "vix_signal": "bullish",
                    "sp500_price": 5200.50,
                    "sp500_rsi": 62.5,
                    "sp500_rsi_signal": "bullish",
                    "sp500_ma200": 4850.00,
                    "sp500_above_ma200": True,
                    "put_call_ratio": 0.85,
                    "put_call_signal": "neutral",
                    "retrieved_at": "2024-01-15T10:30:00Z",
                },
                "analyzed_at": "2024-01-15T10:30:00Z",
            }
        }
    }
