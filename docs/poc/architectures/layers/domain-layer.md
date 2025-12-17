# Domain層 実装ガイド

## 概要

Domain層はクリーンアーキテクチャの最内層であり、ビジネスルールとドメインロジックを定義する。
フレームワークや外部ライブラリに依存しない純粋なPythonコードで構成される。

---

## 構成要素

| 要素 | 責務 | 配置場所 |
|------|------|----------|
| Entity | ビジネスエンティティ、識別子を持つ | `domain/entities/` |
| Value Object | 不変の値オブジェクト | `domain/value_objects/` |
| Domain Service | 複数エンティティにまたがるロジック | `domain/services/` |
| Repository Interface | データアクセスの抽象インターフェース | `domain/repositories/` |

---

## コード例

### Entities（エンティティ）

```python
# domain/entities/stock.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Stock:
    """銘柄エンティティ"""
    symbol: str
    name: str
    price: float
    volume: int
    market_cap: int

    def is_large_cap(self) -> bool:
        """大型株かどうか"""
        return self.market_cap >= 10_000_000_000  # $10B以上
```

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
    """マーケット状態エンティティ"""
    condition: MarketCondition
    confidence: float
    vix: float
    sp500_rsi: float
    sp500_above_200ma: bool

    def is_favorable_for_entry(self) -> bool:
        """エントリーに適した環境か"""
        return self.condition == MarketCondition.RISK_ON and self.confidence >= 0.6
```

### Value Objects（値オブジェクト）

```python
# domain/value_objects/canslim_score.py
from dataclasses import dataclass

@dataclass(frozen=True)
class CANSLIMScore:
    """CAN-SLIMスコア値オブジェクト"""
    eps_growth_q: float      # C: Current Quarterly Earnings
    eps_growth_y: float      # A: Annual Earnings Growth
    is_near_high: bool       # N: New High
    volume_ratio: float      # S: Supply and Demand
    rs_rating: float         # L: Leader
    institutional_holding: float  # I: Institutional

    def passes_canslim(self) -> bool:
        """CAN-SLIM条件を満たすか"""
        return (
            self.eps_growth_q >= 25 and
            self.eps_growth_y >= 25 and
            self.is_near_high and
            self.volume_ratio >= 1.5 and
            self.rs_rating >= 80
        )

    @property
    def total_score(self) -> int:
        """総合スコア（0-100）"""
        score = 0
        if self.eps_growth_q >= 25: score += 20
        if self.eps_growth_y >= 25: score += 20
        if self.is_near_high: score += 15
        if self.volume_ratio >= 1.5: score += 15
        if self.rs_rating >= 80: score += 20
        if self.institutional_holding >= 0: score += 10
        return score
```

### Domain Services（ドメインサービス）

```python
# domain/services/market_analyzer.py
from domain.entities.market_status import MarketStatus, MarketCondition

class MarketAnalyzer:
    """マーケット分析ドメインサービス"""

    def determine_condition(
        self,
        vix: float,
        sp500_rsi: float,
        sp500_above_200ma: bool,
        put_call_ratio: float
    ) -> tuple[MarketCondition, float]:
        """
        複数指標からマーケット状態を判定

        Returns:
            (condition, confidence)
        """
        score = 0

        # VIX判定
        if vix < 20:
            score += 2
        elif vix > 30:
            score -= 2

        # RSI判定
        if sp500_rsi < 30:
            score += 2  # 売られすぎ = 買いチャンス
        elif 30 <= sp500_rsi <= 70:
            score += 1
        else:
            score -= 1

        # 200MA判定
        if sp500_above_200ma:
            score += 1
        else:
            score -= 1

        # Put/Call Ratio判定
        if put_call_ratio > 1.0:
            score += 1  # 恐怖 = 逆張りチャンス
        elif put_call_ratio < 0.7:
            score -= 1

        # 判定
        if score >= 3:
            return MarketCondition.RISK_ON, min(score / 5, 1.0)
        elif score <= -2:
            return MarketCondition.RISK_OFF, min(abs(score) / 5, 1.0)
        else:
            return MarketCondition.NEUTRAL, 0.5
```

### Repository Interfaces（リポジトリインターフェース）

```python
# domain/repositories/stock_repository.py
from abc import ABC, abstractmethod
from domain.entities.stock import Stock

class StockRepository(ABC):
    """銘柄リポジトリのインターフェース"""

    @abstractmethod
    async def get_by_symbol(self, symbol: str) -> Stock | None:
        pass

    @abstractmethod
    async def get_all(self, symbols: list[str]) -> list[Stock]:
        pass

    @abstractmethod
    async def save(self, stock: Stock) -> None:
        pass
```

```python
# domain/repositories/market_data_repository.py
from abc import ABC, abstractmethod
from datetime import date

class MarketDataRepository(ABC):
    """市場データリポジトリのインターフェース"""

    @abstractmethod
    async def get_vix(self) -> float:
        pass

    @abstractmethod
    async def get_sp500_price(self) -> float:
        pass

    @abstractmethod
    async def get_price_history(
        self, symbol: str, start_date: date, end_date: date
    ) -> list[dict]:
        pass
```

---

## 設計原則

1. **外部依存なし**: フレームワーク、DB、APIに依存しない
2. **純粋なロジック**: ビジネスルールのみを表現
3. **テスタビリティ**: モックなしで単体テスト可能
4. **不変性優先**: Value Objectは`frozen=True`で不変に
