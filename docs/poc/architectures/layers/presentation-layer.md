# Presentation層 実装ガイド

## 概要

Presentation層はHTTPリクエスト/レスポンスの処理、API定義を担当する。
Application層のユースケースを呼び出し、結果をクライアントに返す。

---

## 構成要素

| 要素 | 責務 | 配置場所 |
|------|------|----------|
| Controller | APIルーター、エンドポイント定義 | `presentation/api/` |
| Schema | Pydanticスキーマ（リクエスト/レスポンス） | `presentation/schemas/` |
| Dependencies | 依存性注入設定 | `presentation/dependencies.py` |

---

## コード例

### Controllers（コントローラー/ルーター）

```python
# presentation/api/market_controller.py
from fastapi import APIRouter, Depends
from presentation.schemas.market import MarketStatusResponse
from presentation.schemas.common import ApiResponse
from application.use_cases.get_market_status import GetMarketStatusUseCase
from presentation.dependencies import get_market_status_use_case

router = APIRouter(prefix="/market", tags=["market"])

@router.get("/status", response_model=ApiResponse[MarketStatusResponse])
async def get_market_status(
    use_case: GetMarketStatusUseCase = Depends(get_market_status_use_case)
):
    """マーケット状態を取得"""
    output = await use_case.execute()

    return ApiResponse(
        success=True,
        data=MarketStatusResponse(
            status=output.status.condition.value,
            confidence=output.status.confidence,
            vix=output.status.vix,
            sp500_rsi=output.status.sp500_rsi,
            sp500_above_200ma=output.status.sp500_above_200ma,
            recommendation=output.recommendation,
            updated_at=output.updated_at
        )
    )
```

```python
# presentation/api/screener_controller.py
from fastapi import APIRouter, Depends, Query
from presentation.schemas.screener import ScreenerResponse, StockResult
from presentation.schemas.common import ApiResponse
from application.use_cases.screen_canslim_stocks import (
    ScreenCANSLIMStocksUseCase, ScreenCANSLIMInput
)
from presentation.dependencies import get_screen_canslim_use_case

router = APIRouter(prefix="/screener", tags=["screener"])

@router.get("/canslim", response_model=ApiResponse[ScreenerResponse])
async def screen_canslim_stocks(
    min_eps_growth: float = Query(25.0, ge=0),
    min_rs_rating: float = Query(80.0, ge=0, le=100),
    limit: int = Query(50, ge=1, le=100),
    use_case: ScreenCANSLIMStocksUseCase = Depends(get_screen_canslim_use_case)
):
    """CAN-SLIM条件を満たす銘柄を取得"""
    input_dto = ScreenCANSLIMInput(
        min_eps_growth=min_eps_growth,
        min_rs_rating=min_rs_rating,
        limit=limit
    )
    results = await use_case.execute(input_dto)

    return ApiResponse(
        success=True,
        data=ScreenerResponse(
            count=len(results),
            stocks=[StockResult.from_domain(r) for r in results]
        )
    )
```

### Schemas（Pydanticスキーマ）

```python
# presentation/schemas/common.py
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: str
    message: str

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
```

```python
# presentation/schemas/market.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

class MarketStatusResponse(BaseModel):
    status: Literal["risk_on", "risk_off", "neutral"]
    confidence: float = Field(..., ge=0, le=1)
    vix: float
    sp500_rsi: float = Field(..., ge=0, le=100)
    sp500_above_200ma: bool
    recommendation: str
    updated_at: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "risk_on",
                "confidence": 0.75,
                "vix": 15.2,
                "sp500_rsi": 62.5,
                "sp500_above_200ma": True,
                "recommendation": "市場環境は良好",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }
    }
```

### Dependency Injection（依存性注入）

```python
# presentation/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from infrastructure.database.connection import get_db
from infrastructure.repositories.postgres_stock_repository import PostgresStockRepository
from infrastructure.gateways.yfinance_market_data_gateway import YFinanceMarketDataGateway
from infrastructure.gateways.fmp_financial_gateway import FMPFinancialGateway
from domain.services.market_analyzer import MarketAnalyzer
from application.use_cases.get_market_status import GetMarketStatusUseCase
from application.use_cases.screen_canslim_stocks import ScreenCANSLIMStocksUseCase

def get_market_status_use_case(
    db: Session = Depends(get_db)
) -> GetMarketStatusUseCase:
    """GetMarketStatusUseCaseの依存性を解決"""
    market_data_repo = YFinanceMarketDataGateway()
    market_analyzer = MarketAnalyzer()

    return GetMarketStatusUseCase(
        market_data_repo=market_data_repo,
        market_analyzer=market_analyzer
    )

def get_screen_canslim_use_case(
    db: Session = Depends(get_db)
) -> ScreenCANSLIMStocksUseCase:
    """ScreenCANSLIMStocksUseCaseの依存性を解決"""
    stock_repo = PostgresStockRepository(db)
    financial_gateway = FMPFinancialGateway()

    return ScreenCANSLIMStocksUseCase(
        stock_repo=stock_repo,
        financial_gateway=financial_gateway
    )
```

---

## 設計原則

1. **Application層に依存**: ユースケースを呼び出すのみ
2. **薄いコントローラー**: ビジネスロジックを持たない
3. **依存性注入**: Infrastructure層の実装をユースケースに注入
4. **スキーマ変換**: Domain EntityとAPIレスポンスの変換を担当
