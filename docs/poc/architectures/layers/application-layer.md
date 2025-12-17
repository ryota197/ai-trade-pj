# Application層 実装ガイド

## 概要

Application層はユースケースを実装する層。
Domain層のみに依存し、外部サービスはインターフェース経由で利用する。

---

## 構成要素

| 要素 | 責務 | 配置場所 |
|------|------|----------|
| Use Case | アプリケーション固有のビジネスロジック | `application/use_cases/` |
| DTO | 入出力データの定義 | `application/dto/` |
| Gateway Interface | 外部サービスの抽象インターフェース | `application/interfaces/` |

---

## コード例

### Use Cases（ユースケース）

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
        market_data_repo: MarketDataRepository,
        market_analyzer: MarketAnalyzer
    ):
        self._market_data_repo = market_data_repo
        self._market_analyzer = market_analyzer

    async def execute(self) -> GetMarketStatusOutput:
        # 市場データ取得
        vix = await self._market_data_repo.get_vix()
        sp500_price = await self._market_data_repo.get_sp500_price()
        # ... 他の指標も取得

        # ドメインサービスで分析
        condition, confidence = self._market_analyzer.determine_condition(
            vix=vix,
            sp500_rsi=65.0,  # 実際は計算
            sp500_above_200ma=True,
            put_call_ratio=0.85
        )

        status = MarketStatus(
            condition=condition,
            confidence=confidence,
            vix=vix,
            sp500_rsi=65.0,
            sp500_above_200ma=True
        )

        recommendation = self._generate_recommendation(status)

        return GetMarketStatusOutput(
            status=status,
            recommendation=recommendation,
            updated_at=datetime.utcnow()
        )

    def _generate_recommendation(self, status: MarketStatus) -> str:
        if status.is_favorable_for_entry():
            return "市場環境は良好。個別株のエントリー検討可。"
        elif status.condition.value == "risk_off":
            return "市場環境は悪化。新規エントリーは控える。"
        else:
            return "市場環境は中立。慎重に判断。"
```

```python
# application/use_cases/screen_canslim_stocks.py
from dataclasses import dataclass
from domain.entities.stock import Stock
from domain.value_objects.canslim_score import CANSLIMScore
from domain.repositories.stock_repository import StockRepository
from application.interfaces.financial_data_gateway import FinancialDataGateway

@dataclass
class ScreeningResult:
    stock: Stock
    canslim_score: CANSLIMScore

@dataclass
class ScreenCANSLIMInput:
    min_eps_growth: float = 25.0
    min_rs_rating: float = 80.0
    limit: int = 50

class ScreenCANSLIMStocksUseCase:
    """CAN-SLIMスクリーニングユースケース"""

    def __init__(
        self,
        stock_repo: StockRepository,
        financial_gateway: FinancialDataGateway
    ):
        self._stock_repo = stock_repo
        self._financial_gateway = financial_gateway

    async def execute(self, input: ScreenCANSLIMInput) -> list[ScreeningResult]:
        # 銘柄リスト取得
        symbols = await self._get_universe()
        results = []

        for symbol in symbols:
            # 財務データ取得
            financials = await self._financial_gateway.get_financials(symbol)
            stock = await self._stock_repo.get_by_symbol(symbol)

            if not stock:
                continue

            # CAN-SLIMスコア計算
            score = CANSLIMScore(
                eps_growth_q=financials.eps_growth_q,
                eps_growth_y=financials.eps_growth_y,
                is_near_high=self._is_near_52w_high(stock),
                volume_ratio=financials.volume_ratio,
                rs_rating=financials.rs_rating,
                institutional_holding=financials.institutional_holding
            )

            # フィルター適用
            if (score.eps_growth_q >= input.min_eps_growth and
                score.rs_rating >= input.min_rs_rating):
                results.append(ScreeningResult(stock=stock, canslim_score=score))

        # スコア順にソート
        results.sort(key=lambda r: r.canslim_score.total_score, reverse=True)
        return results[:input.limit]
```

### Interfaces（ゲートウェイインターフェース）

```python
# application/interfaces/financial_data_gateway.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class FinancialData:
    eps_growth_q: float
    eps_growth_y: float
    volume_ratio: float
    rs_rating: float
    institutional_holding: float

class FinancialDataGateway(ABC):
    """財務データ取得ゲートウェイのインターフェース"""

    @abstractmethod
    async def get_financials(self, symbol: str) -> FinancialData:
        pass
```

---

## 設計原則

1. **Domain層のみに依存**: Infrastructure層の実装に依存しない
2. **インターフェース経由**: 外部サービスは抽象インターフェースで定義
3. **単一責任**: 1ユースケース = 1クラス
4. **テスタビリティ**: リポジトリ/ゲートウェイをモック化してテスト可能
