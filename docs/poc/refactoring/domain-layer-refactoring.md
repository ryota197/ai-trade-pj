# ドメイン層リファクタリング方針

## 概要

新しいDB設計（`canslim_stocks` 統合テーブル）に合わせて、ドメイン層を再構成する。

**参照ドキュメント:**
- 新設計: `docs/poc/domain/` 配下
- 現行設計: `docs/poc/architectures/layers/domain-layer.md`
- DB設計: `docs/poc/domain/03-database-design.md`

---

## 現行 vs 新設計 比較

### Models（集約・エンティティ・値オブジェクト）

| 現行ファイル | 現行クラス | 新設計 | アクション |
|-------------|-----------|--------|----------|
| stock_identity.py | StockIdentity | CANSLIMStock に統合 | 削除 |
| price_snapshot.py | PriceSnapshot | PriceSnapshot (VO) | 維持（内部VO化） |
| stock_metrics.py | StockMetrics | StockRating (VO) | 置換 |
| market_benchmark.py | MarketBenchmark | - | 削除 |
| market_status.py | MarketStatus | MarketSnapshot | リネーム・簡略化 |
| watchlist_item.py | WatchlistItem | WatchlistItem | 維持 |
| paper_trade.py | PaperTrade | Trade | リネーム |
| canslim_score.py | CANSLIMScore | CANSLIMScore (VO) | 維持 |
| canslim_config.py | CANSLIMWeights 等 | ScreeningCriteria | 置換 |
| quote.py | Quote, HistoricalPrice | - | 削除（API直接使用） |
| - | - | CANSLIMStock | 新規作成 |
| - | - | RSRating (VO) | 新規作成 |
| - | - | StockRating (VO) | 新規作成 |

### Repositories

| 現行ファイル | 新設計 | アクション |
|-------------|--------|----------|
| stock_identity_repository.py | CANSLIMStockRepository に統合 | 削除 |
| price_snapshot_repository.py | CANSLIMStockRepository に統合 | 削除 |
| stock_metrics_repository.py | CANSLIMStockRepository に統合 | 削除 |
| benchmark_repository.py | - | 削除 |
| stock_query_repository.py | CANSLIMStockRepository に統合 | 削除 |
| market_snapshot_repository.py | MarketSnapshotRepository | 維持 |
| watchlist_repository.py | WatchlistRepository | 維持 |
| trade_repository.py | TradeRepository | 維持（リネーム対応） |
| - | CANSLIMStockRepository | 新規作成 |

### Domain Services

| 現行ファイル | 新設計 | アクション |
|-------------|--------|----------|
| relative_strength_calculator.py | RelativeStrengthCalculator | 維持（シグネチャ変更） |
| canslim_score_calculator.py | CANSLIMScorer | リネーム |
| eps_growth_calculator.py | - | 削除（API で取得） |
| performance_calculator.py | - | 削除または統合 |
| market_analyzer.py | MarketAnalyzer | 維持 |
| - | RSRatingCalculator | 新規作成 |
| - | ScreeningService | 新規作成 |

---

## 新ディレクトリ構造

```
backend/src/domain/
├── models/
│   ├── __init__.py
│   ├── canslim_stock.py          # 新規: CANSLIMStock 集約ルート
│   ├── price_snapshot.py         # 維持: PriceSnapshot VO
│   ├── stock_rating.py           # 新規: StockRating, RSRating VO
│   ├── canslim_score.py          # 維持: CANSLIMScore VO
│   ├── screening_criteria.py     # 新規: ScreeningCriteria VO
│   ├── market_snapshot.py        # リネーム: MarketSnapshot
│   ├── watchlist_item.py         # 維持
│   └── trade.py                  # リネーム: Trade (旧 PaperTrade)
│
├── constants/
│   ├── __init__.py
│   └── trading_days.py           # 維持
│
├── repositories/
│   ├── __init__.py
│   ├── canslim_stock_repository.py   # 新規
│   ├── market_snapshot_repository.py # 維持
│   ├── watchlist_repository.py       # 維持
│   └── trade_repository.py           # 維持
│
├── services/
│   ├── __init__.py
│   ├── relative_strength_calculator.py  # 維持
│   ├── rs_rating_calculator.py          # 新規
│   ├── canslim_scorer.py                # リネーム
│   ├── market_analyzer.py               # 維持
│   └── screening_service.py             # 新規
│
└── __init__.py
```

---

## 削除対象ファイル

```
backend/src/domain/
├── models/
│   ├── stock_identity.py         # → CANSLIMStock に統合
│   ├── stock_metrics.py          # → StockRating に置換
│   ├── market_benchmark.py       # テーブル削除に伴い削除
│   ├── quote.py                  # API 直接使用に変更
│   ├── market_indicators.py      # MarketSnapshot に統合
│   ├── performance_metrics.py    # 削除または統合
│   └── canslim_config.py         # ScreeningCriteria に置換
│
├── repositories/
│   ├── stock_identity_repository.py   # 統合
│   ├── price_snapshot_repository.py   # 統合
│   ├── stock_metrics_repository.py    # 統合
│   ├── benchmark_repository.py        # 削除
│   ├── stock_query_repository.py      # 統合
│   ├── stock_repository.py            # 統合
│   ├── market_data_repository.py      # 削除
│   └── refresh_job_repository.py      # Infrastructure 層へ移動
│
├── services/
│   ├── eps_growth_calculator.py       # 削除
│   └── performance_calculator.py      # 削除または統合
│
├── entities/                          # 後方互換用 → 削除
│   └── __init__.py
│
└── value_objects/                     # 後方互換用 → 削除
    └── __init__.py
```

---

## 実装順序

### Phase 1: 新モデル作成（破壊的変更なし）

1. `models/canslim_stock.py` 新規作成
2. `models/stock_rating.py` 新規作成（RSRating, StockRating）
3. `models/screening_criteria.py` 新規作成
4. `repositories/canslim_stock_repository.py` 新規作成

### Phase 2: ドメインサービス更新

1. `services/rs_rating_calculator.py` 新規作成
2. `services/canslim_scorer.py` リネーム・更新
3. `services/screening_service.py` 新規作成
4. `services/relative_strength_calculator.py` シグネチャ更新

### Phase 3: 既存モデルのリネーム・更新

1. `models/paper_trade.py` → `models/trade.py`
2. `models/market_status.py` → `models/market_snapshot.py`
3. リポジトリのリネーム対応

### Phase 4: 旧ファイル削除

1. 統合済みモデル削除
2. 統合済みリポジトリ削除
3. 後方互換ディレクトリ削除

### Phase 5: Infrastructure 層・Application 層更新

1. リポジトリ実装の更新
2. ユースケースの更新
3. API エンドポイントの更新

---

## CANSLIMStock 集約設計

```python
# models/canslim_stock.py

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .price_snapshot import PriceSnapshot
from .stock_rating import StockRating
from .screening_criteria import ScreeningCriteria


@dataclass
class CANSLIMStock:
    """CAN-SLIM分析銘柄（集約ルート）"""

    # 識別子
    symbol: str
    date: date

    # 銘柄情報
    name: str
    industry: str

    # 価格スナップショット
    price_snapshot: PriceSnapshot

    # 評価
    rating: StockRating | None

    # メタデータ
    updated_at: datetime

    def meets_filter(self, criteria: ScreeningCriteria) -> bool:
        """スクリーニング条件を満たすか判定"""
        if self.rating is None:
            return False
        if self.rating.rs_rating is None:
            return False
        if self.rating.rs_rating.value < criteria.min_rs_rating:
            return False
        if self.rating.canslim_score is None:
            return False
        if self.rating.canslim_score.total < criteria.min_canslim_score:
            return False
        return True

    def distance_from_52week_high(self) -> Decimal:
        """52週高値からの乖離率（%）"""
        if self.price_snapshot.week_52_high == 0:
            return Decimal("0")
        return (
            (self.price_snapshot.week_52_high - self.price_snapshot.price)
            / self.price_snapshot.week_52_high
            * 100
        )

    def volume_ratio(self) -> Decimal:
        """出来高倍率（当日 / 50日平均）"""
        if self.price_snapshot.avg_volume_50d == 0:
            return Decimal("0")
        return Decimal(self.price_snapshot.volume) / Decimal(self.price_snapshot.avg_volume_50d)
```

---

## CANSLIMStockRepository インターフェース

```python
# repositories/canslim_stock_repository.py

from abc import ABC, abstractmethod
from datetime import date

from ..models.canslim_stock import CANSLIMStock
from ..models.screening_criteria import ScreeningCriteria


class CANSLIMStockRepository(ABC):
    """CAN-SLIM銘柄リポジトリ"""

    @abstractmethod
    def find_by_symbol_and_date(
        self, symbol: str, target_date: date
    ) -> CANSLIMStock | None:
        """シンボルと日付で取得"""
        pass

    @abstractmethod
    def find_all_by_date(self, target_date: date) -> list[CANSLIMStock]:
        """指定日の全銘柄を取得"""
        pass

    @abstractmethod
    def find_by_criteria(
        self,
        target_date: date,
        criteria: ScreeningCriteria,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CANSLIMStock]:
        """条件でスクリーニング"""
        pass

    @abstractmethod
    def save(self, stock: CANSLIMStock) -> None:
        """保存（UPSERT）"""
        pass

    @abstractmethod
    def save_all(self, stocks: list[CANSLIMStock]) -> None:
        """一括保存"""
        pass

    @abstractmethod
    def get_all_symbols(self) -> list[str]:
        """全シンボル一覧を取得"""
        pass
```

---

## 注意事項

### 破壊的変更への対応

- Application 層・Infrastructure 層のコードも同時に更新が必要
- テストコードも更新対象
- 段階的に移行し、各 Phase 完了後に動作確認

### 後方互換性

- Phase 4 まで旧モデルを残し、新旧並行運用も可能
- ただし POC のため、一括移行を推奨

### テーブル名との整合性

- テーブル: `canslim_stocks`
- モデル: `CANSLIMStock`
- リポジトリ: `CANSLIMStockRepository`

---

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2025-01-01 | 初版作成 |
