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
