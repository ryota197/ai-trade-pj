# Backend コーディング規約

## 概要

Python 3.11 + FastAPI + SQLAlchemy を使用したバックエンド開発のコーディング規約。
**クリーンアーキテクチャ**に基づいた設計を採用する。

---

## プロジェクト構成

### ディレクトリ構成

詳細なディレクトリ構成は [directory-structure.md](../architectures/directory-structure.md) を参照。
アーキテクチャの詳細は [service-components.md](../architectures/service-components.md) を参照。

```
src/
├── main.py                  # エントリーポイント
├── config.py                # 設定管理
│
├── domain/                  # ドメイン層（最内層）
│   ├── entities/            # エンティティ
│   ├── value_objects/       # 値オブジェクト
│   ├── services/            # ドメインサービス
│   └── repositories/        # リポジトリインターフェース（抽象）
│
├── application/             # アプリケーション層（ユースケース）
│   ├── use_cases/           # ユースケース
│   ├── dto/                 # Data Transfer Objects
│   └── interfaces/          # 外部サービスのインターフェース
│
├── infrastructure/          # インフラストラクチャ層
│   ├── database/            # DB接続、SQLAlchemyモデル
│   ├── repositories/        # リポジトリ実装
│   └── gateways/            # 外部API連携（ゲートウェイ実装）
│
└── presentation/            # プレゼンテーション層
    ├── api/                 # FastAPIルーター
    ├── schemas/             # Pydanticスキーマ
    └── dependencies.py      # 依存性注入設定
```

### レイヤー間の依存関係

```
presentation → application → domain ← infrastructure
                  ↓                      ↓
          (uses interfaces)    (implements interfaces)
```

- **Domain**: 何にも依存しない（最内層）
- **Application**: Domainのみに依存、外部サービスはインターフェース経由
- **Infrastructure**: Domain/Applicationのインターフェースを実装
- **Presentation**: Applicationのユースケースに依存

### ファイル命名規則

| 種別 | 命名規則 | 例 |
|-----|---------|-----|
| モジュール | snake_case | `market_service.py` |
| クラス | PascalCase | `MarketService` |
| 関数・変数 | snake_case | `get_market_status` |
| 定数 | UPPER_SNAKE_CASE | `DEFAULT_RS_RATING` |

---

## Python 基本規約

### 型ヒント（必須）

```python
# Good: 型ヒントを付ける
def calculate_rs_rating(symbol: str, period_days: int = 252) -> float:
    ...

# Good: 複雑な型
from typing import Optional, List
from datetime import datetime

def get_stocks(
    symbols: List[str],
    start_date: Optional[datetime] = None
) -> List[Stock]:
    ...

# Bad: 型ヒントなし
def calculate_rs_rating(symbol, period_days=252):  # 禁止
    ...
```

### インポート順序

```python
# 1. 標準ライブラリ
import os
from datetime import datetime
from typing import Optional, List

# 2. サードパーティ
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import yfinance as yf

# 3. ローカルモジュール
from src.services.market_service import MarketService
from src.schemas.market import MarketStatusResponse
```

### 文字列フォーマット

```python
# Good: f-string
symbol = "AAPL"
message = f"Stock {symbol} not found"

# Bad: format() や % 演算子
message = "Stock {} not found".format(symbol)  # 避ける
message = "Stock %s not found" % symbol  # 避ける
```

---

## FastAPI

### ルーター定義

```python
# routers/market.py
from fastapi import APIRouter, Depends
from src.services.market_service import MarketService
from src.schemas.market import MarketStatusResponse
from src.schemas.common import ApiResponse

router = APIRouter(prefix="/market", tags=["market"])

@router.get("/status", response_model=ApiResponse[MarketStatusResponse])
async def get_market_status(
    service: MarketService = Depends(get_market_service)
) -> ApiResponse[MarketStatusResponse]:
    """
    マーケット全体の現在の状態を取得

    - **status**: risk_on / risk_off / neutral
    - **confidence**: 判定の確信度 (0-1)
    - **indicators**: 各指標の値
    """
    data = await service.get_status()
    return ApiResponse(success=True, data=data)
```

### 依存性注入（クリーンアーキテクチャ）

```python
# presentation/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from infrastructure.database.connection import get_db
from infrastructure.repositories.postgres_stock_repository import PostgresStockRepository
from infrastructure.gateways.yfinance_market_data_gateway import YFinanceMarketDataGateway
from domain.services.market_analyzer import MarketAnalyzer
from application.use_cases.get_market_status import GetMarketStatusUseCase

def get_market_status_use_case(
    db: Session = Depends(get_db)
) -> GetMarketStatusUseCase:
    """GetMarketStatusUseCaseの依存性を解決"""
    # Infrastructure層の実装をユースケースに注入
    market_data_repo = YFinanceMarketDataGateway()
    market_analyzer = MarketAnalyzer()

    return GetMarketStatusUseCase(
        market_data_repo=market_data_repo,
        market_analyzer=market_analyzer
    )

# infrastructure/database/connection.py
from sqlalchemy.orm import Session
from typing import Generator

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### エラーハンドリング

```python
from fastapi import HTTPException

# カスタム例外
class StockNotFoundError(Exception):
    def __init__(self, symbol: str):
        self.symbol = symbol
        super().__init__(f"Stock {symbol} not found")

# ルーターでの使用
@router.get("/quote/{symbol}")
async def get_quote(symbol: str) -> ApiResponse[QuoteResponse]:
    try:
        data = await service.get_quote(symbol)
        return ApiResponse(success=True, data=data)
    except StockNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ExternalApiError as e:
        raise HTTPException(status_code=502, detail="External API error")
```

---

## Pydantic (スキーマ)

### リクエスト/レスポンススキーマ

```python
# schemas/market.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

class MarketIndicators(BaseModel):
    vix: float = Field(..., description="VIX指数")
    vix_signal: Literal["bullish", "neutral", "bearish"]
    put_call_ratio: float
    sp500_rsi: float = Field(..., ge=0, le=100)
    sp500_above_200ma: bool

class MarketStatusResponse(BaseModel):
    status: Literal["risk_on", "risk_off", "neutral"]
    confidence: float = Field(..., ge=0, le=1)
    indicators: MarketIndicators
    recommendation: str
    updated_at: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "risk_on",
                "confidence": 0.75,
                "indicators": {
                    "vix": 15.2,
                    "vix_signal": "bullish",
                    "put_call_ratio": 0.82,
                    "sp500_rsi": 62.5,
                    "sp500_above_200ma": True
                },
                "recommendation": "市場環境は良好",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }
    }
```

### 共通レスポンス

```python
# schemas/common.py
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

---

## SQLAlchemy (モデル)

### モデル定義（2.0スタイル）

```python
# models/market.py
from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base

class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    vix: Mapped[float] = mapped_column(Numeric(10, 2))
    put_call_ratio: Mapped[float] = mapped_column(Numeric(10, 4))
    sp500_rsi: Mapped[float] = mapped_column(Numeric(10, 2))
    sp500_above_200ma: Mapped[bool] = mapped_column(Boolean)

    market_status: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 2))

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
```

### クエリ（2.0スタイル）

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

# Good: 2.0 スタイル
def get_latest_snapshot(db: Session) -> MarketSnapshot | None:
    stmt = select(MarketSnapshot).order_by(
        MarketSnapshot.recorded_at.desc()
    ).limit(1)
    return db.scalars(stmt).first()

# Bad: 1.x スタイル（使わない）
# db.query(MarketSnapshot).order_by(...).first()
```

---

## 型定義の配置ルール

### 原則

**ビジネス概念を表す型はDomain層に配置する。**

各層で定義すべき型を明確に区別し、適切な場所に配置する。

### 配置ガイドライン

| 型の種類 | 配置場所 | 例 |
|---------|---------|-----|
| ビジネスエンティティ | `domain/entities/` | `Quote`, `Stock`, `Order` |
| 値オブジェクト | `domain/value_objects/` | `Price`, `Symbol`, `Period` |
| ユースケース出力 | `application/dto/` | `GetMarketStatusOutput` |
| APIレスポンス | `presentation/schemas/` | `QuoteResponse` (Pydantic) |
| 外部API固有の型 | `infrastructure/gateways/` | （基本的に作らない） |

### ✅ 正しい例

```python
# domain/entities/quote.py
@dataclass(frozen=True)
class Quote:
    """株価エンティティ（ドメイン層）"""
    symbol: str
    price: float
    change: float
    ...

# infrastructure/gateways/yfinance_gateway.py
from src.domain.entities.quote import Quote

class YFinanceGateway:
    def get_quote(self, symbol: str) -> Quote:  # ドメイン型を返す
        ...
        return Quote(symbol=symbol, price=price, ...)

# presentation/api/data_controller.py
from src.domain.entities.quote import Quote

def _quote_to_response(quote: Quote) -> QuoteResponse:
    """ドメイン → レスポンススキーマ変換"""
    return QuoteResponse(
        symbol=quote.symbol,
        price=quote.price,
        ...
    )
```

### ❌ 避けるべき例

```python
# infrastructure/gateways/yfinance_gateway.py

# Bad: ゲートウェイ内にドメイン概念の型を定義
@dataclass
class QuoteData:  # ← これはDomain層に置くべき
    symbol: str
    price: float
    ...

class YFinanceGateway:
    def get_quote(self, symbol: str) -> QuoteData:
        ...
```

### 判断基準

型を定義する際は以下を考慮する:

1. **この型はビジネス概念を表しているか？**
   - Yes → `domain/entities/` または `domain/value_objects/`
   - No → 用途に応じた層

2. **この型は複数のゲートウェイ/リポジトリで再利用されるか？**
   - Yes → 間違いなくDomain層
   - No → それでもビジネス概念ならDomain層

3. **外部APIのレスポンス構造をそのまま表す型か？**
   - Yes → 作らない（直接ドメイン型に変換）
   - 複雑な場合のみInfrastructure層に内部型を作成

### frozen=True の推奨

ドメインエンティティには `frozen=True` を使用し、不変オブジェクトとして扱う。

```python
@dataclass(frozen=True)  # 推奨: イミュータブル
class Quote:
    symbol: str
    price: float
```

これにより:
- 予期しない変更を防止
- ハッシュ可能になる（dictのキーやsetに使える）
- スレッドセーフになる

### Domain → Presentation の変換関数

Presentation層では、ドメインエンティティをレスポンススキーマに変換する関数を定義する。

```python
# presentation/api/data_controller.py

def _quote_to_response(quote: Quote) -> QuoteResponse:
    """ドメインエンティティをレスポンススキーマに変換"""
    return QuoteResponse(
        symbol=quote.symbol,
        price=quote.price,
        ...
    )
```

#### なぜ変換が必要か

1. **依存方向の制御**
   - `Quote`（Domain）: 何にも依存しない純粋なビジネスロジック
   - `QuoteResponse`（Presentation）: Pydantic、バリデーション、OpenAPI生成などAPI固有の関心事

2. **変更の影響範囲を限定**

   | 変更内容 | Quote | QuoteResponse | Gateway | Controller |
   |---------|-------|---------------|---------|------------|
   | APIレスポンス形式変更 | 不変 | 変更 | 不変 | 変換関数のみ |
   | ビジネスロジック追加 | 変更 | 不変 | 不変 | 不変 |
   | 外部API変更 | 不変 | 不変 | 変更 | 不変 |

3. **API専用のフィールド追加が容易**

   ```python
   # 表示用フォーマットなど、API専用の加工
   def _quote_to_response(quote: Quote) -> QuoteResponse:
       return QuoteResponse(
           ...
           formatted_price=f"${quote.price:.2f}",  # API専用
       )
   ```

#### 命名規則

- プライベート関数として `_` プレフィックスを付ける
- `_{entity}_to_{response}` の形式で命名

---

## クリーンアーキテクチャのコード例

### Domain層 - エンティティ

```python
# domain/entities/market_status.py
from dataclasses import dataclass
from enum import Enum

class MarketCondition(Enum):
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    NEUTRAL = "neutral"

@dataclass
class MarketStatus:
    """マーケット状態エンティティ（純粋なドメインロジック）"""
    condition: MarketCondition
    confidence: float
    vix: float
    sp500_rsi: float

    def is_favorable_for_entry(self) -> bool:
        """エントリーに適した環境か"""
        return self.condition == MarketCondition.RISK_ON and self.confidence >= 0.6
```

### Domain層 - リポジトリインターフェース

```python
# domain/repositories/market_data_repository.py
from abc import ABC, abstractmethod

class MarketDataRepository(ABC):
    """市場データリポジトリのインターフェース（抽象）"""

    @abstractmethod
    async def get_vix(self) -> float:
        pass

    @abstractmethod
    async def get_sp500_price(self) -> float:
        pass
```

### Application層 - ユースケース

```python
# application/use_cases/get_market_status.py
from dataclasses import dataclass
from datetime import datetime
from domain.entities.market_status import MarketStatus
from domain.services.market_analyzer import MarketAnalyzer
from domain.repositories.market_data_repository import MarketDataRepository

@dataclass
class GetMarketStatusOutput:
    status: MarketStatus
    recommendation: str
    updated_at: datetime

class GetMarketStatusUseCase:
    """マーケット状態取得ユースケース"""

    def __init__(
        self,
        market_data_repo: MarketDataRepository,  # インターフェースに依存
        market_analyzer: MarketAnalyzer
    ):
        self._market_data_repo = market_data_repo
        self._market_analyzer = market_analyzer

    async def execute(self) -> GetMarketStatusOutput:
        vix = await self._market_data_repo.get_vix()
        # ... ドメインサービスで分析
        return GetMarketStatusOutput(...)
```

### Infrastructure層 - ゲートウェイ実装

```python
# infrastructure/gateways/yfinance_market_data_gateway.py
import yfinance as yf
from domain.repositories.market_data_repository import MarketDataRepository

class YFinanceMarketDataGateway(MarketDataRepository):
    """yfinanceによる市場データ取得実装"""

    async def get_vix(self) -> float:
        ticker = yf.Ticker("^VIX")
        return ticker.info.get("regularMarketPrice", 0)

    async def get_sp500_price(self) -> float:
        ticker = yf.Ticker("^GSPC")
        return ticker.info.get("regularMarketPrice", 0)
```

### Presentation層 - コントローラー

```python
# presentation/api/market_controller.py
from fastapi import APIRouter, Depends
from presentation.schemas.market import MarketStatusResponse
from application.use_cases.get_market_status import GetMarketStatusUseCase
from presentation.dependencies import get_market_status_use_case

router = APIRouter(prefix="/market", tags=["market"])

@router.get("/status")
async def get_market_status(
    use_case: GetMarketStatusUseCase = Depends(get_market_status_use_case)
):
    """マーケット状態を取得"""
    output = await use_case.execute()
    return MarketStatusResponse.from_domain(output)
```

---

## 外部API連携

### クライアントクラス

```python
# external/yfinance_client.py
import yfinance as yf
from typing import Optional
from datetime import datetime, timedelta

class YFinanceClient:
    """yfinance APIのラッパー"""

    def get_quote(self, symbol: str) -> dict:
        """リアルタイム株価を取得"""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "symbol": symbol,
            "price": info.get("regularMarketPrice"),
            "change": info.get("regularMarketChange"),
            "volume": info.get("regularMarketVolume"),
        }

    def get_history(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d"
    ) -> list[dict]:
        """過去株価を取得"""
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        return df.reset_index().to_dict(orient="records")
```

### エラーハンドリング

```python
class ExternalApiError(Exception):
    """外部API呼び出しエラー"""
    pass

class YFinanceClient:
    def get_quote(self, symbol: str) -> dict:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if not info:
                raise StockNotFoundError(symbol)
            return {...}
        except Exception as e:
            raise ExternalApiError(f"yfinance error: {e}")
```

---

## 設定管理

```python
# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://trader:localdev@localhost:5432/trading"

    # External APIs
    fmp_api_key: str | None = None

    # App
    debug: bool = True
    log_level: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## ログ

```python
import logging
from src.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# 使用例
logger.info(f"Fetching quote for {symbol}")
logger.error(f"Failed to fetch data: {e}")
```

---

## テスト

### pytest の使用

```python
# tests/test_market_service.py
import pytest
from unittest.mock import Mock, patch
from src.services.market_service import MarketService

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def market_service(mock_db):
    return MarketService(mock_db)

class TestMarketService:
    async def test_get_status_returns_risk_on_when_vix_low(
        self, market_service
    ):
        with patch.object(
            market_service.yf_client, 'get_quote'
        ) as mock_quote:
            mock_quote.return_value = {"price": 15.0}

            result = await market_service.get_status()

            assert result.status == "risk_on"
```

### テスト実行

```bash
# 全テスト実行
pytest

# カバレッジ付き
pytest --cov=src

# 特定のテスト
pytest tests/test_market_service.py -v
```
