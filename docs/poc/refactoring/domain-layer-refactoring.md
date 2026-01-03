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
| price_snapshot.py | PriceSnapshot | CANSLIMStock に統合 | 削除 |
| stock_metrics.py | StockMetrics | CANSLIMStock に統合 | 削除 |
| market_benchmark.py | MarketBenchmark | - | 削除 |
| market_status.py | MarketStatus | MarketSnapshot | リネーム・簡略化 |
| watchlist_item.py | WatchlistItem | WatchlistItem | 維持 |
| paper_trade.py | PaperTrade | Trade | リネーム |
| canslim_score.py | CANSLIMScore | - | 削除（フラット化） |
| canslim_config.py | CANSLIMWeights 等 | ScreeningCriteria | 置換 |
| quote.py | Quote, HistoricalPrice | - | 削除（API直接使用） |
| - | - | CANSLIMStock | 新規作成（フラット構造） |

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
| rs_calculator.py | RSCalculator | リネーム・シグネチャ変更 |
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
│   ├── canslim_stock.py          # 新規: CANSLIMStock 集約ルート（フラット構造）
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
│   ├── rs_calculator.py                 # リネーム: RSCalculator
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

1. `models/canslim_stock.py` 新規作成（フラット構造）
2. `models/screening_criteria.py` 新規作成
3. `repositories/canslim_stock_repository.py` 新規作成

### Phase 2: ドメインサービス更新

1. `services/rs_rating_calculator.py` 新規作成
2. `services/canslim_scorer.py` リネーム・更新
3. `services/screening_service.py` 新規作成
4. `services/rs_calculator.py` リネーム・シグネチャ更新

### Phase 3: 既存モデルのリネーム・更新

1. `models/paper_trade.py` → `models/trade.py`
2. `models/market_status.py` → `models/market_snapshot.py`
3. リポジトリのリネーム対応

### Phase 4: 旧ファイル削除・クリーンアップ

1. 統合済みモデル削除
2. 統合済みリポジトリ削除
3. 後方互換ディレクトリ削除
4. ドメインサービスのクリーンアップ
   - `rs_calculator.py`: 旧メソッド削除（`calculate_relative_strength`, `calculate_from_prices`, `calculate_percentile_rank`, `_estimate_rs_rating`）
   - `canslim_score_calculator.py`: 削除（`canslim_scorer.py` に移行済み）

### Phase 5: Infrastructure 層・Application 層更新

1. リポジトリ実装の更新
2. ユースケースの更新
3. API エンドポイントの更新

---

## CANSLIMStock 集約設計

### 設計方針

- **フラット構造**: PriceSnapshot, StockRating などの値オブジェクトを使わず、フラットにフィールドを持つ
- **NULL許容不変条件**: 段階的計算に対応するため、計算途中のフィールドは NULL を許容
- **計算フェーズ**: Job 1 → Job 2 → Job 3 の順に段階的に計算・更新

### 計算フェーズと更新順序

```
Job 1: 価格データ取得
  → price, change_percent, volume, avg_volume_50d, market_cap,
    week_52_high, week_52_low, eps_growth_quarterly, eps_growth_annual,
    institutional_ownership, relative_strength

Job 2: RS Rating 計算（全銘柄の relative_strength が必要）
  → rs_rating

Job 3: CAN-SLIM スコア計算（rs_rating が必要）
  → canslim_score, score_c, score_a, score_n, score_s, score_l, score_i, score_m
```

### コード例

```python
# models/canslim_stock.py

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from .screening_criteria import ScreeningCriteria


@dataclass
class CANSLIMStock:
    """CAN-SLIM分析銘柄（集約ルート・フラット構造）"""

    # === 識別子（必須） ===
    symbol: str
    date: date

    # === 銘柄情報 ===
    name: str | None = None
    industry: str | None = None

    # === 価格データ（Job 1 で更新） ===
    price: Decimal | None = None
    change_percent: Decimal | None = None
    volume: int | None = None
    avg_volume_50d: int | None = None
    market_cap: int | None = None
    week_52_high: Decimal | None = None
    week_52_low: Decimal | None = None

    # === 財務データ（Job 1 で更新） ===
    eps_growth_quarterly: Decimal | None = None
    eps_growth_annual: Decimal | None = None
    institutional_ownership: Decimal | None = None

    # === 相対強度（Job 1 で更新） ===
    relative_strength: Decimal | None = None

    # === RS Rating（Job 2 で更新、全銘柄のrelative_strengthが必要） ===
    rs_rating: int | None = None

    # === CAN-SLIM スコア（Job 3 で更新） ===
    canslim_score: int | None = None
    score_c: int | None = None
    score_a: int | None = None
    score_n: int | None = None
    score_s: int | None = None
    score_l: int | None = None
    score_i: int | None = None
    score_m: int | None = None

    # === メタデータ ===
    updated_at: datetime | None = None

    # === 不変条件（Invariants） ===
    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("symbol is required")
        if self.rs_rating is not None and not (1 <= self.rs_rating <= 99):
            raise ValueError("rs_rating must be between 1 and 99")
        if self.canslim_score is not None and not (0 <= self.canslim_score <= 100):
            raise ValueError("canslim_score must be between 0 and 100")

    # === ドメインロジック ===
    def meets_filter(self, criteria: ScreeningCriteria) -> bool:
        """スクリーニング条件を満たすか判定"""
        if self.rs_rating is None:
            return False
        if self.rs_rating < criteria.min_rs_rating:
            return False
        if self.canslim_score is None:
            return False
        if self.canslim_score < criteria.min_canslim_score:
            return False
        return True

    def distance_from_52week_high(self) -> Decimal | None:
        """52週高値からの乖離率（%）"""
        if self.week_52_high is None or self.price is None:
            return None
        if self.week_52_high == 0:
            return Decimal("0")
        return (self.week_52_high - self.price) / self.week_52_high * 100

    def volume_ratio(self) -> Decimal | None:
        """出来高倍率（当日 / 50日平均）"""
        if self.volume is None or self.avg_volume_50d is None:
            return None
        if self.avg_volume_50d == 0:
            return Decimal("0")
        return Decimal(self.volume) / Decimal(self.avg_volume_50d)

    def is_leader(self) -> bool:
        """主導株か（RS Rating 80以上）"""
        return self.rs_rating is not None and self.rs_rating >= 80

    def is_calculation_complete(self) -> bool:
        """全計算フェーズが完了しているか"""
        return (
            self.relative_strength is not None
            and self.rs_rating is not None
            and self.canslim_score is not None
        )
```

---

## CANSLIMStockRepository インターフェース

### 設計方針

- **段階的更新対応**: Job 1 → Job 2 → Job 3 の各フェーズで部分更新が可能
- **一括操作優先**: パフォーマンスのため、一括取得・一括更新メソッドを提供
- **UPSERT**: 存在すれば更新、なければ挿入

```python
# repositories/canslim_stock_repository.py

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from ..models.canslim_stock import CANSLIMStock
from ..models.screening_criteria import ScreeningCriteria


class CANSLIMStockRepository(ABC):
    """CAN-SLIM銘柄リポジトリ"""

    # === 取得系 ===

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
        """条件でスクリーニング（計算完了銘柄のみ）"""
        pass

    @abstractmethod
    def find_all_with_relative_strength(
        self, target_date: date
    ) -> list[CANSLIMStock]:
        """relative_strength が計算済みの全銘柄を取得（Job 2 用）"""
        pass

    @abstractmethod
    def get_all_symbols(self) -> list[str]:
        """全シンボル一覧を取得"""
        pass

    # === 保存系（全フィールド） ===

    @abstractmethod
    def save(self, stock: CANSLIMStock) -> None:
        """保存（UPSERT）"""
        pass

    @abstractmethod
    def save_all(self, stocks: list[CANSLIMStock]) -> None:
        """一括保存"""
        pass

    # === 部分更新系（段階的計算用） ===

    @abstractmethod
    def update_rs_ratings(
        self,
        target_date: date,
        rs_ratings: dict[str, int],  # {symbol: rs_rating}
    ) -> None:
        """RS Rating を一括更新（Job 2 用）"""
        pass

    @abstractmethod
    def update_canslim_scores(
        self,
        target_date: date,
        scores: dict[str, dict],  # {symbol: {canslim_score, score_c, ...}}
    ) -> None:
        """CAN-SLIM スコアを一括更新（Job 3 用）"""
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
| 2025-01-02 | フラット構造に変更（StockRating 削除）、段階的計算とNULL許容不変条件を追加 |
| 2025-01-03 | Phase 4 にドメインサービスのクリーンアップを追加 |
