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

#### ゲートウェイ設計方針

| ゲートウェイ | 責務 | 実装するインターフェース |
|------------|------|------------------------|
| `YFinanceGateway` | 株価・財務データ取得（統合版） | `FinancialDataGateway` |
| `YFinanceMarketDataGateway` | マーケット指標取得（VIX, RSI等） | `MarketDataRepository` |

> **Note**: 当初 `YFinanceGateway`（汎用）と `YFinancePriceGateway`（スクリーナー用）が
> 別々に存在したが、機能重複を解消するため `YFinanceGateway` に統合。
> `FinancialDataGateway` インターフェースを実装し、非同期メソッドで統一。

```python
# infrastructure/gateways/yfinance_gateway.py
import yfinance as yf
from datetime import datetime
from application.interfaces.financial_data_gateway import (
    FinancialDataGateway,
    FinancialMetrics,
    HistoricalBar,
    QuoteData,
)

class YFinanceGateway(FinancialDataGateway):
    """
    yfinance を使用した財務データゲートウェイ（統合版）

    FinancialDataGateway インターフェースを実装し、
    株価・財務データを一元的に取得する。
    """

    SP500_SYMBOL = "SPY"

    async def get_quote(self, symbol: str) -> QuoteData | None:
        """現在の株価データを取得"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if not info or info.get("regularMarketPrice") is None:
                return None

            price = info.get("regularMarketPrice", 0)
            previous_close = info.get("previousClose", price)
            change = price - previous_close

            return QuoteData(
                symbol=symbol.upper(),
                price=price,
                change=round(change, 2),
                change_percent=round((change / previous_close * 100), 2),
                volume=info.get("regularMarketVolume", 0),
                avg_volume=info.get("averageVolume", 0),
                market_cap=info.get("marketCap"),
                pe_ratio=info.get("trailingPE"),
                week_52_high=info.get("fiftyTwoWeekHigh", 0),
                week_52_low=info.get("fiftyTwoWeekLow", 0),
                timestamp=datetime.now(),
            )
        except Exception:
            return None

    async def get_quotes(self, symbols: list[str]) -> dict[str, QuoteData]:
        """複数銘柄の株価データを一括取得"""
        result = {}
        for symbol in symbols:
            quote = await self.get_quote(symbol)
            if quote:
                result[symbol] = quote
        return result

    async def get_price_history(
        self, symbol: str, period: str = "1y", interval: str = "1d"
    ) -> list[HistoricalBar]:
        """株価履歴を取得"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            if hist.empty:
                return []

            return [
                HistoricalBar(
                    date=date.to_pydatetime(),
                    open=round(row["Open"], 4),
                    high=round(row["High"], 4),
                    low=round(row["Low"], 4),
                    close=round(row["Close"], 4),
                    volume=int(row["Volume"]),
                )
                for date, row in hist.iterrows()
            ]
        except Exception:
            return []

    async def get_financial_metrics(self, symbol: str) -> FinancialMetrics | None:
        """財務指標を取得（EPS成長率を自動計算）"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if not info:
                return None

            return FinancialMetrics(
                symbol=symbol.upper(),
                eps_ttm=info.get("trailingEps"),
                eps_growth_quarterly=self._calc_eps_growth_quarterly(ticker),
                eps_growth_annual=self._calc_eps_growth_annual(ticker),
                revenue_growth=self._to_percent(info.get("revenueGrowth")),
                profit_margin=self._to_percent(info.get("profitMargins")),
                roe=self._to_percent(info.get("returnOnEquity")),
                debt_to_equity=info.get("debtToEquity"),
                institutional_ownership=self._to_percent(
                    info.get("heldPercentInstitutions")
                ),
            )
        except Exception:
            return None

    async def get_sp500_history(
        self, period: str = "1y", interval: str = "1d"
    ) -> list[HistoricalBar]:
        """S&P500の履歴を取得（RS Rating計算用）"""
        return await self.get_price_history(self.SP500_SYMBOL, period, interval)

    # === Private Methods ===

    def _calc_eps_growth_quarterly(self, ticker) -> float | None:
        """四半期EPS成長率を計算"""
        try:
            q = ticker.quarterly_earnings
            if q is None or len(q) < 2:
                return None
            current = q.iloc[0]["Reported EPS"]
            previous = q.iloc[-1]["Reported EPS"] if len(q) >= 4 else q.iloc[1]["Reported EPS"]
            if previous == 0:
                return None
            return round(((current - previous) / abs(previous)) * 100, 2)
        except Exception:
            return None

    def _calc_eps_growth_annual(self, ticker) -> float | None:
        """年間EPS成長率を計算"""
        try:
            a = ticker.earnings
            if a is None or len(a) < 2:
                return None
            current = a.iloc[-1]["Earnings"]
            previous = a.iloc[-2]["Earnings"]
            if previous == 0:
                return None
            return round(((current - previous) / abs(previous)) * 100, 2)
        except Exception:
            return None

    @staticmethod
    def _to_percent(value: float | None) -> float | None:
        return round(value * 100, 2) if value else None
```

```python
# infrastructure/gateways/yfinance_market_data_gateway.py
import yfinance as yf
from domain.repositories.market_data_repository import MarketDataRepository

class YFinanceMarketDataGateway(MarketDataRepository):
    """yfinanceによる市場指標取得（VIX, S&P500 RSI等）"""

    def get_vix(self) -> float:
        ticker = yf.Ticker("^VIX")
        return ticker.info.get("regularMarketPrice", 0)

    def get_sp500_price(self) -> float:
        ticker = yf.Ticker("^GSPC")
        return ticker.info.get("regularMarketPrice", 0)

    def get_sp500_rsi(self, period: int = 14) -> float:
        # RSI計算ロジック
        ...

    def get_sp500_ma200(self) -> float:
        # 200日移動平均計算
        ...

    def get_put_call_ratio(self) -> float:
        # Put/Call Ratio取得
        ...
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
