"""株価データスキーマ"""

from datetime import datetime

from pydantic import BaseModel, Field


class QuoteResponse(BaseModel):
    """株価レスポンス"""

    symbol: str = Field(..., description="ティッカーシンボル")
    price: float = Field(..., description="現在価格")
    change: float = Field(..., description="変動額")
    change_percent: float = Field(..., description="変動率（%）")
    volume: int = Field(..., description="出来高")
    market_cap: float | None = Field(None, description="時価総額")
    pe_ratio: float | None = Field(None, description="PER")
    week_52_high: float | None = Field(None, description="52週高値")
    week_52_low: float | None = Field(None, description="52週安値")
    timestamp: datetime = Field(..., description="取得日時")


class HistoryItem(BaseModel):
    """過去データ1件"""

    date: datetime = Field(..., description="日付")
    open: float = Field(..., description="始値")
    high: float = Field(..., description="高値")
    low: float = Field(..., description="安値")
    close: float = Field(..., description="終値")
    volume: int = Field(..., description="出来高")


class HistoryResponse(BaseModel):
    """過去データレスポンス"""

    symbol: str = Field(..., description="ティッカーシンボル")
    period: str = Field(..., description="期間")
    interval: str = Field(..., description="間隔")
    data: list[HistoryItem] = Field(..., description="過去データ")


class FinancialsResponse(BaseModel):
    """財務指標レスポンス"""

    symbol: str = Field(..., description="ティッカーシンボル")
    eps_ttm: float | None = Field(None, description="EPS（TTM）")
    eps_growth_quarterly: float | None = Field(
        None, description="四半期EPS成長率（%）"
    )
    eps_growth_annual: float | None = Field(None, description="年間EPS成長率（%）")
    revenue_growth: float | None = Field(None, description="売上成長率（%）")
    profit_margin: float | None = Field(None, description="利益率（%）")
    roe: float | None = Field(None, description="ROE（%）")
    debt_to_equity: float | None = Field(None, description="負債資本倍率")
    institutional_ownership: float | None = Field(
        None, description="機関投資家保有率（%）"
    )
    retrieved_at: datetime = Field(..., description="取得日時")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "AAPL",
                "eps_ttm": 6.13,
                "eps_growth_quarterly": 32.5,
                "eps_growth_annual": 25.8,
                "revenue_growth": 12.3,
                "profit_margin": 25.6,
                "roe": 147.5,
                "debt_to_equity": 205.8,
                "institutional_ownership": 60.5,
                "retrieved_at": "2024-01-15T10:30:00Z",
            }
        }
    }
