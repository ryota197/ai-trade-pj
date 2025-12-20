# Gateway責務分離 リファクタリング計画

## ステータス: 検討中

作成日: 2024-12-20

---

## 背景

Phase 3実装時に `YFinanceGateway` と `YFinancePriceGateway` を統合したが、
統合後のクラスが多重責務になっている問題が発生。

---

## 現状の問題点

### 1. YFinanceGatewayの責務過多

| 責務 | メソッド | 問題 |
|------|---------|------|
| 価格データ取得 | `get_quote()`, `get_quotes()` | ○ 本来の責務 |
| 履歴データ取得 | `get_price_history()`, `get_sp500_history()` | ○ 価格と関連 |
| 財務指標取得 | `get_financial_metrics()` | △ 別責務の可能性 |
| EPS成長率計算 | `_calculate_eps_growth_*()` | ✗ ドメインロジック |
| レガシー対応 | `get_quote_sync()`, `get_history_sync()` | △ 技術的負債 |

### 2. ドメインロジックの混入

EPS成長率の計算ロジックがInfrastructure層に存在している。
これはビジネスルールであり、Domain層に属すべき。

```python
# 現状（問題あり）
# infrastructure/gateways/yfinance_gateway.py
def _calculate_eps_growth_quarterly(self, ticker) -> float | None:
    # ビジネスロジックがInfrastructure層に...
```

### 3. インターフェースの肥大化

`FinancialDataGateway`インターフェースが複数の責務を持っている：
- 株価取得（Price）
- 履歴取得（History）
- 財務指標取得（Fundamentals）

---

## 責務分離案

### レイヤー別の責務

```
┌─────────────────────────────────────────────────────────────┐
│  Infrastructure層（外部API呼び出しのみ）                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  YFinanceGateway                                            │
│  └─ 責務: yfinance APIから生データを取得                     │
│     ├─ get_quote()         → 株価の生データ                  │
│     ├─ get_price_history() → 履歴の生データ                  │
│     └─ get_raw_financials()→ 財務の生データ                  │
│                                                             │
│  YFinanceMarketDataGateway                                  │
│  └─ 責務: マーケット指標取得（VIX, RSI等）                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Domain層（ビジネスロジック）                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EPSGrowthCalculator（新規）                                 │
│  └─ 責務: EPS成長率の計算ロジック                            │
│     ├─ calculate_quarterly_growth()                         │
│     └─ calculate_annual_growth()                            │
│                                                             │
│  RSRatingCalculator（既存）                                  │
│  └─ 責務: RS Rating計算                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Application層（オーケストレーション）                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  GetFinancialMetricsUseCase（新規）                          │
│  └─ 責務: Gateway + Calculator を組み合わせて                │
│           FinancialMetrics DTOを構築                        │
│                                                             │
│  ScreenCANSLIMStocksUseCase（既存）                          │
│  └─ 責務: 各種Calculatorを使ってスクリーニング               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 具体的な変更内容

### 1. Domain層に追加

```
domain/services/
├── eps_growth_calculator.py  # 新規
├── rs_rating_calculator.py   # 既存
└── market_analyzer.py        # 既存
```

```python
# domain/services/eps_growth_calculator.py
@dataclass(frozen=True)
class EPSData:
    """EPS生データ"""
    quarterly_eps: list[float]
    annual_eps: list[float]

class EPSGrowthCalculator:
    """EPS成長率計算サービス"""

    @staticmethod
    def calculate_quarterly_growth(eps_data: EPSData) -> float | None:
        """四半期EPS成長率を計算"""
        ...

    @staticmethod
    def calculate_annual_growth(eps_data: EPSData) -> float | None:
        """年間EPS成長率を計算"""
        ...
```

### 2. Infrastructure層の変更

```python
# infrastructure/gateways/yfinance_gateway.py
class YFinanceGateway(FinancialDataGateway):
    """yfinance APIからデータを取得（生データのみ）"""

    async def get_quote(self, symbol: str) -> QuoteData | None:
        # 株価取得（変更なし）
        ...

    async def get_price_history(self, symbol: str, ...) -> list[HistoricalBar]:
        # 履歴取得（変更なし）
        ...

    async def get_raw_financials(self, symbol: str) -> RawFinancialData | None:
        """財務生データを取得（EPS計算はしない）"""
        ticker = yf.Ticker(symbol)
        return RawFinancialData(
            quarterly_eps=[...],  # 生データのみ
            annual_eps=[...],
            ...
        )
```

### 3. Application層の変更

```python
# application/use_cases/screener/get_financial_metrics.py
class GetFinancialMetricsUseCase:
    """財務指標取得ユースケース"""

    def __init__(
        self,
        gateway: FinancialDataGateway,
        eps_calculator: EPSGrowthCalculator,
    ):
        self._gateway = gateway
        self._eps_calculator = eps_calculator

    async def execute(self, symbol: str) -> FinancialMetrics:
        # 1. 生データ取得（Infrastructure）
        raw = await self._gateway.get_raw_financials(symbol)

        # 2. EPS成長率計算（Domain）
        eps_growth_q = self._eps_calculator.calculate_quarterly_growth(raw)
        eps_growth_a = self._eps_calculator.calculate_annual_growth(raw)

        # 3. DTOに変換して返却
        return FinancialMetrics(
            eps_growth_quarterly=eps_growth_q,
            eps_growth_annual=eps_growth_a,
            ...
        )
```

---

## インターフェース分離案（オプション）

現在の `FinancialDataGateway` を分割する場合：

```python
# 現在（肥大化）
class FinancialDataGateway(ABC):
    async def get_quote(self, symbol: str) -> QuoteData | None: ...
    async def get_quotes(self, symbols: list[str]) -> dict[str, QuoteData]: ...
    async def get_price_history(self, ...) -> list[HistoricalBar]: ...
    async def get_financial_metrics(self, symbol: str) -> FinancialMetrics | None: ...
    async def get_sp500_history(self, ...) -> list[HistoricalBar]: ...

# 分割後（ISP準拠）
class PriceDataGateway(ABC):
    """株価データ取得"""
    async def get_quote(self, symbol: str) -> QuoteData | None: ...
    async def get_quotes(self, symbols: list[str]) -> dict[str, QuoteData]: ...

class PriceHistoryGateway(ABC):
    """株価履歴取得"""
    async def get_price_history(self, ...) -> list[HistoricalBar]: ...
    async def get_sp500_history(self, ...) -> list[HistoricalBar]: ...

class FinancialDataGateway(ABC):
    """財務生データ取得"""
    async def get_raw_financials(self, symbol: str) -> RawFinancialData | None: ...
```

---

## 優先度と実施タイミング

| 優先度 | アクション | 理由 | 実施時期 |
|--------|-----------|------|----------|
| **高** | EPSGrowthCalculator作成 | SRP違反の解消 | Phase 3完了後 |
| **中** | YFinanceGatewayからEPS計算削除 | 上記に依存 | 同上 |
| **中** | GetFinancialMetricsUseCase作成 | オーケストレーション | 同上 |
| **低** | インターフェース分離 | 現状でも動作する | Phase 4以降 |
| **低** | レガシーメソッド削除 | 利用箇所確認後 | 適宜 |

---

## 判断基準

### リファクタリング実施の条件

1. Phase 3の基本機能が動作確認済み
2. テストが整備されている
3. 他の開発に影響しないタイミング

### リファクタリング見送りの条件

1. 現状で機能要件を満たしている
2. パフォーマンス問題がない
3. コードの理解が困難でない

---

## 関連ドキュメント

- [infrastructure-layer.md](./layers/infrastructure-layer.md)
- [directory-structure.md](./directory-structure.md)
- [Phase 3: Screener Module](../plan/phase3-screener.md)
