# Infrastructure層 実装ガイド

## 概要

Infrastructure層は外部サービス、データベース、APIとの実際の連携を担当する。
Domain/Application層のインターフェースを実装する。

---

## 構成要素

| 要素 | 責務 | 配置場所 |
|------|------|----------|
| Repository Impl | リポジトリインターフェースの実装 | `infrastructure/repositories/` |
| Gateway Impl | ゲートウェイインターフェースの実装 | `infrastructure/gateways/` |
| Database | DB接続、SQLAlchemyモデル | `infrastructure/database/` |

---

## コード例

### Repository Implementations（リポジトリ実装）

```python
# infrastructure/repositories/postgres_stock_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from domain.entities.stock import Stock
from domain.repositories.stock_repository import StockRepository
from infrastructure.database.models import StockModel

class PostgresStockRepository(StockRepository):
    """PostgreSQLによる銘柄リポジトリ実装"""

    def __init__(self, session: Session):
        self._session = session

    async def get_by_symbol(self, symbol: str) -> Stock | None:
        stmt = select(StockModel).where(StockModel.symbol == symbol)
        model = self._session.scalars(stmt).first()

        if not model:
            return None

        return self._to_entity(model)

    async def get_all(self, symbols: list[str]) -> list[Stock]:
        stmt = select(StockModel).where(StockModel.symbol.in_(symbols))
        models = self._session.scalars(stmt).all()
        return [self._to_entity(m) for m in models]

    async def save(self, stock: Stock) -> None:
        model = StockModel(
            symbol=stock.symbol,
            name=stock.name,
            price=stock.price,
            volume=stock.volume,
            market_cap=stock.market_cap
        )
        self._session.merge(model)
        self._session.commit()

    def _to_entity(self, model: StockModel) -> Stock:
        return Stock(
            symbol=model.symbol,
            name=model.name,
            price=float(model.price),
            volume=model.volume,
            market_cap=model.market_cap
        )
```

### Gateway Implementations（ゲートウェイ実装）

```python
# infrastructure/gateways/yfinance_market_data_gateway.py
import yfinance as yf
from datetime import date
from domain.repositories.market_data_repository import MarketDataRepository

class YFinanceMarketDataGateway(MarketDataRepository):
    """yfinanceによる市場データ取得実装"""

    async def get_vix(self) -> float:
        ticker = yf.Ticker("^VIX")
        return ticker.info.get("regularMarketPrice", 0)

    async def get_sp500_price(self) -> float:
        ticker = yf.Ticker("^GSPC")
        return ticker.info.get("regularMarketPrice", 0)

    async def get_price_history(
        self, symbol: str, start_date: date, end_date: date
    ) -> list[dict]:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        return df.reset_index().to_dict(orient="records")
```

```python
# infrastructure/gateways/fmp_financial_gateway.py
import httpx
from application.interfaces.financial_data_gateway import (
    FinancialDataGateway, FinancialData
)

class FMPFinancialGateway(FinancialDataGateway):
    """Financial Modeling Prep APIによる財務データ取得実装"""

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key
        self._base_url = "https://financialmodelingprep.com/api/v3"

    async def get_financials(self, symbol: str) -> FinancialData:
        async with httpx.AsyncClient() as client:
            # API呼び出し実装
            response = await client.get(
                f"{self._base_url}/income-statement/{symbol}",
                params={"apikey": self._api_key}
            )
            data = response.json()
            # ... データ変換

        return FinancialData(
            eps_growth_q=30.0,
            eps_growth_y=25.0,
            volume_ratio=1.8,
            rs_rating=85.0,
            institutional_holding=0.65
        )
```

### Database（データベース）

```python
# infrastructure/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from src.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

```python
# infrastructure/database/models/market_snapshot_model.py
from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database.base import Base

class MarketSnapshotModel(Base):
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

---

## 設計原則

1. **インターフェースを実装**: Domain/Application層で定義されたインターフェースを実装
2. **外部依存はここに集約**: yfinance、SQLAlchemy、httpx等の外部ライブラリ依存
3. **Entity変換**: ORMモデルとDomainエンティティの相互変換を担当
4. **テストは統合テスト**: 実際のDB/APIとの接続をテスト
