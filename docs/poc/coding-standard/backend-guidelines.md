# Backend コーディング規約

## 概要

Python 3.11 + FastAPI + SQLAlchemy を使用したバックエンド開発のコーディング規約。
**シンプルな3層アーキテクチャ**を採用する。

---

## プロジェクト構成

### ディレクトリ構成

アーキテクチャの詳細は [service-components.md](../architectures/service-components.md) を参照。

```
src/
├── main.py                  # エントリーポイント
├── config.py                # 設定管理
│
├── domain/                  # ドメイン層（最内層）
│   ├── models/              # ビジネスモデル
│   ├── services/            # ドメインサービス
│   └── repositories/        # リポジトリインターフェース（抽象）
│
├── infrastructure/          # インフラストラクチャ層
│   ├── database/            # DB接続設定
│   ├── repositories/        # リポジトリ実装
│   └── gateways/            # 外部API連携（インターフェース＋実装）
│
├── presentation/            # プレゼンテーション層
│   ├── api/                 # FastAPIコントローラー
│   ├── schemas/             # Pydanticスキーマ
│   └── dependencies.py      # 依存性注入設定
│
└── jobs/                    # バッチ処理層
    ├── flows/               # フロー（複数Jobのオーケストレーション）
    ├── executions/          # 個別Job実行
    └── lib/                 # Job共通ライブラリ
```

### レイヤー間の依存関係

```
presentation ──┬──> infrastructure ──> domain
               │
jobs ──────────┘
```

- **Domain**: 何にも依存しない（最内層）
- **Infrastructure**: Domainのインターフェースを実装
- **Presentation**: Domain, Infrastructureに依存（Repository/Gateway直接呼び出し）
- **Jobs**: Domain, Infrastructureに依存

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

### 依存性注入

```python
# presentation/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from src.infrastructure.database.connection import get_db
from src.jobs.flows.refresh_screener import RefreshScreenerFlow

def get_refresh_screener_flow(
    db: Session = Depends(get_db),
) -> RefreshScreenerFlow:
    """RefreshScreenerFlowの依存性を解決"""
    # Repository/Gatewayを注入してFlowを構築
    ...

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

**Note**: コントローラーではRepositoryを直接インスタンス化して使用する。
依存性注入はJobs層のFlowなど、複雑な構築が必要な場合のみ使用する。

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
| ビジネスモデル | `domain/models/` | `CANSLIMStock`, `Trade`, `MarketSnapshot` |
| APIスキーマ | `presentation/schemas/` | `QuoteResponse` (Pydantic) |
| Gatewayデータ型 | `infrastructure/gateways/` | `QuoteData`, `HistoricalBar` |

### ✅ 正しい例

```python
# domain/models/canslim_stock.py
@dataclass(frozen=True)
class CANSLIMStock:
    """CAN-SLIM銘柄（ドメイン層）"""
    symbol: str
    price: Decimal
    canslim_score: int
    ...

# infrastructure/gateways/financial_data_gateway.py
@dataclass(frozen=True)
class QuoteData:
    """外部APIから取得した株価データ（Gateway層）"""
    symbol: str
    price: float
    ...

# presentation/api/screener_controller.py
from src.domain.models.canslim_stock import CANSLIMStock

def _stock_to_response(stock: CANSLIMStock) -> StockSummarySchema:
    """ドメイン → レスポンススキーマ変換"""
    return StockSummarySchema(
        symbol=stock.symbol,
        price=float(stock.price),
        ...
    )
```

### ❌ 避けるべき例

```python
# presentation/api/screener_controller.py

# Bad: コントローラー内にビジネスロジックを定義
def calculate_canslim_score(stock_data):  # ← Domain層に置くべき
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

## 3層アーキテクチャのコード例

### Domain層 - モデル

```python
# domain/models/market_snapshot.py
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal

class MarketCondition(Enum):
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    NEUTRAL = "neutral"

@dataclass
class MarketSnapshot:
    """マーケットスナップショット（純粋なドメインロジック）"""
    vix: Decimal
    sp500_price: Decimal
    sp500_rsi: Decimal
    condition: MarketCondition
    score: int

    def is_favorable_for_entry(self) -> bool:
        """エントリーに適した環境か"""
        return self.condition == MarketCondition.RISK_ON and self.score >= 2
```

### Domain層 - リポジトリインターフェース

```python
# domain/repositories/market_snapshot_repository.py
from abc import ABC, abstractmethod
from domain.models.market_snapshot import MarketSnapshot

class MarketSnapshotRepository(ABC):
    """市場スナップショットリポジトリのインターフェース（抽象）"""

    @abstractmethod
    def find_latest(self) -> MarketSnapshot | None:
        pass

    @abstractmethod
    def save(self, snapshot: MarketSnapshot) -> None:
        pass
```

### Infrastructure層 - リポジトリ実装

```python
# infrastructure/repositories/postgres_market_snapshot_repository.py
from sqlalchemy.orm import Session
from domain.repositories.market_snapshot_repository import MarketSnapshotRepository
from domain.models.market_snapshot import MarketSnapshot

class PostgresMarketSnapshotRepository(MarketSnapshotRepository):
    """PostgreSQLによるMarketSnapshotリポジトリ実装"""

    def __init__(self, db: Session):
        self._db = db

    def find_latest(self) -> MarketSnapshot | None:
        # SQLAlchemyクエリ実行
        ...

    def save(self, snapshot: MarketSnapshot) -> None:
        # 永続化処理
        ...
```

### Presentation層 - コントローラー

```python
# presentation/api/market_controller.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.infrastructure.database.connection import get_db
from src.infrastructure.repositories.postgres_market_snapshot_repository import (
    PostgresMarketSnapshotRepository,
)
from src.presentation.schemas.market import MarketStatusResponse
from src.presentation.schemas.common import ApiResponse

router = APIRouter(prefix="/market", tags=["market"])


def _snapshot_to_response(snapshot: MarketSnapshot) -> MarketStatusResponse:
    """Domain Model → Schema変換"""
    return MarketStatusResponse(
        condition=snapshot.condition.value,
        score=snapshot.score,
        ...
    )


@router.get("/status", response_model=ApiResponse[MarketStatusResponse])
def get_market_status(
    db: Session = Depends(get_db),
) -> ApiResponse[MarketStatusResponse]:
    """マーケット状態を取得"""
    repo = PostgresMarketSnapshotRepository(db)
    snapshot = repo.find_latest()

    if snapshot is None:
        raise HTTPException(status_code=404, detail="Market data not available")

    return ApiResponse(success=True, data=_snapshot_to_response(snapshot))
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
