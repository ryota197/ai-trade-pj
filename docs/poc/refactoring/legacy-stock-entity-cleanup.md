# レガシー Stock/StockSummary エンティティの整理

> **採用方針: 案A（完全削除）**
>
> 決定日: 2024-12-30

## 概要

`domain/entities/` と `domain/value_objects/` フォルダを削除し、`domain/models/` に統一するリファクタリング作業において、存在しない `Stock` / `StockSummary` クラスへの参照が発見された。

このドキュメントでは、レガシーコードの整理方針を定義する。

---

## 背景

### 現在のドメイン層構造

```
domain/
├── models/           # Entity + Value Object（正）
├── constants/        # 定数クラス（正）
├── repositories/     # リポジトリIF
├── services/         # ドメインサービス
├── entities/         # [非推奨] 後方互換用re-export → 削除予定
└── value_objects/    # [非推奨] 後方互換用re-export → 削除予定
```

### 発見された問題

`from src.domain.entities.stock import Stock, StockSummary` という参照が12ファイルに存在するが、`Stock` / `StockSummary` クラスは**どこにも定義されていない**。

これはDBスキーマの正規化（Phase 3）時に古いエンティティが削除されたが、参照元のコードが更新されなかったため。

---

## 現状分析

### テーブル構造

| テーブル | 構造 | 用途 | 関連ドメインモデル | 今後 |
|---------|------|------|-------------------|------|
| `stocks` | 正規化（新） | 銘柄マスター | `StockIdentity` | 継続使用 |
| `stock_prices` | 正規化（新） | 価格スナップショット | `PriceSnapshot` | 継続使用 |
| `stock_metrics` | 正規化（新） | 計算指標 | `StockMetrics` | 継続使用 |
| `screener_results` | 非正規化（旧） | スクリーニング結果キャッシュ | `Stock` (存在しない) | **削除** |

### ファイル分類

#### 正規化構造用（新・継続使用）

| レイヤー | ファイル | 状態 |
|---------|---------|------|
| Domain | `models/stock_identity.py` | ✅ |
| Domain | `models/price_snapshot.py` | ✅ |
| Domain | `models/stock_metrics.py` | ✅ |
| Domain | `repositories/stock_identity_repository.py` | ✅ |
| Domain | `repositories/price_snapshot_repository.py` | ✅ |
| Domain | `repositories/stock_metrics_repository.py` | ✅ |
| Domain | `repositories/stock_query_repository.py` | ✅ |
| Infra | `postgres_stock_identity_repository.py` | ✅ |
| Infra | `postgres_price_snapshot_repository.py` | ✅ |
| Infra | `postgres_stock_metrics_repository.py` | ✅ |
| Infra | `postgres_stock_query_repository.py` | ✅ |

#### 非正規化構造用（旧・削除対象）

| レイヤー | ファイル | 状態 | 対応 |
|---------|---------|------|------|
| Domain | `repositories/stock_repository.py` | ❌ | 削除 |
| Infra | `repositories/postgres_stock_repository.py` | ❌ | 削除 |
| Infra | `repositories/postgres_screener_repository.py` | ❌ | 削除 |
| Infra | `mappers/stock_mapper.py` | ❌ | 削除 |
| Infra | `mappers/stock_model_mapper.py` | ❌ | 削除 |
| Infra | `database/models/screener_result_model.py` | ❌ | 削除 |

#### 参照元（修正対象）

| ファイル | 参照内容 | 対応 |
|---------|---------|------|
| `use_cases/screener/screen_canslim_stocks.py` | `StockRepository` | `StockQueryRepository` に変更 |
| `use_cases/screener/get_stock_detail.py` | `StockRepository` | `StockQueryRepository` に変更 |
| `use_cases/admin/refresh_screener_data.py` | `StockRepository`, `Stock` | 削除または大幅修正 |
| `presentation/dependencies.py` | `PostgresStockRepository`, `PostgresScreenerRepository` | 修正 |

---

## 採用方針: 案A（完全削除）

`screener_results` テーブルと関連コードを全て削除し、正規化テーブル（`stocks`, `stock_prices`, `stock_metrics`）のみを使用する。

### 選定理由

1. 正規化テーブル用のリポジトリ（`StockQueryRepository` 等）が既に存在する
2. 重複した構造を残すと将来的な混乱の原因になる
3. Phase 3で正規化を実施した意図を尊重する
4. コードベースがクリーンになり保守性が向上する

### リスクと対策

| リスク | 対策 |
|-------|------|
| スクリーニング機能が壊れる | `StockQueryRepository` の十分なテスト |
| パフォーマンス劣化 | JOIN クエリの最適化、インデックス確認 |
| データ不整合 | 移行前後でのデータ検証 |

---

## 実装ステップ

### Phase 1: 事前準備

| # | タスク | 状態 |
|---|--------|------|
| 1-1 | `StockQueryRepository` の機能確認 | [x] |
| 1-2 | スクリーニング機能に必要な機能が揃っているか検証 | [x] |
| 1-3 | DDD依存関係の問題調査（横展開） | [x] |
| 1-4 | `StockData` を削除し `StockAggregate` 型エイリアスに変更 | [x] |
| 1-5 | `RefreshJob` を `domain/models/` に移動 | [ ] |
| 1-6 | `ScreenerFilter`, `ScreenerResult` を削除（Use Case で直接処理） | [ ] |
| 1-7 | `StockQueryRepository.screen()` のIF変更（プリミティブパラメータ化） | [ ] |
| 1-8 | `postgres_stock_query_repository.py` の `screen()` に不足フィルター追加 | [ ] |

#### Phase 1 分析結果

**メソッド比較:**

| メソッド | StockQueryRepository（新） | StockRepository（旧） | 状態 |
|---------|--------------------------|---------------------|------|
| `get_stock(symbol)` | ✅ | ✅ | OK |
| `get_stocks(symbols)` | ✅ | ✅ | OK |
| `screen(filter_, limit, offset)` | ✅ | ✅ | 一部フィルター未実装 |
| `get_all_for_canslim()` | ✅ | ✅ | OK |

**ScreenerFilter 比較:**

| フィールド | 新 | 旧 | screen()実装 | 対応 |
|-----------|---|---|-------------|------|
| `min_rs_rating` | ✅ | ✅ | ✅ | OK |
| `min_eps_growth_quarterly` | ✅ | ✅ | ✅ | OK |
| `min_eps_growth_annual` | ✅ | ✅ | ✅ | OK |
| `max_distance_from_52w_high` | ✅ | ✅ | ❌ | **実装追加** |
| `min_volume_ratio` | ✅ | ✅ | ❌ | **実装追加** |
| `min_canslim_score` | ✅ | ✅ | ✅ | OK |
| `min_market_cap` | ❌ | ✅ | - | **フィールド追加** |
| `max_market_cap` | ❌ | ✅ | - | **フィールド追加** |
| `symbols` | ❌ | ✅ | - | **フィールド追加** |

**結果データ構造の違い:**

| 項目 | StockQueryRepository（新） | StockRepository（旧） |
|-----|--------------------------|---------------------|
| 戻り値型 | `ScreenerResult.stocks: list[StockData]` | `ScreenerResult.stocks: list[StockSummary]` |
| データ構造 | `StockData(identity, price, metrics)` | `StockSummary(symbol, name, price, ...)` |

**必要な修正（タスク 1-3）:**

1. `ScreenerFilter` に3フィールド追加:
   - `min_market_cap: float | None = None`
   - `max_market_cap: float | None = None`
   - `symbols: list[str] | None = None`

2. `postgres_stock_query_repository.py` の `screen()` に5フィルター実装追加:
   - `min_market_cap` フィルター（stock_prices.market_cap）
   - `max_market_cap` フィルター（stock_prices.market_cap）
   - `symbols` フィルター
   - `max_distance_from_52w_high` フィルター（計算が必要）
   - `min_volume_ratio` フィルター（volume / avg_volume_50d）

3. Use Case 側で `StockData` → DTO 変換を修正（Phase 2 で対応）

#### DDD依存関係の問題（横展開調査結果）

Domain層にUIの関心事（フィルター条件・結果形式）が存在している。DDDの原則に従い、Application層へ移動する。

**問題のあるファイル:**

| ファイル | クラス | 問題 | 対応 |
|---------|-------|------|------|
| `stock_query_repository.py` | `ScreenerFilter` | UIのフィルター条件 | Application層へ移動 |
| `stock_query_repository.py` | `ScreenerResult` | UIへの結果形式 | Application層へ移動 |
| `stock_query_repository.py` | `StockData` | 既存モデルの単なる入れ物 | **削除済** → `StockAggregate` 型エイリアス |
| `refresh_job_repository.py` | `RefreshJob` | エンティティがリポジトリIFファイルに定義 | `domain/models/` へ移動 |

**問題のないファイル（参考）:**

| ファイル | 設計 | 評価 |
|---------|------|------|
| `trade_repository.py` | フィルター条件をプリミティブパラメータで受け取る | ✅ 良い |
| `watchlist_repository.py` | 同上 | ✅ 良い |
| `benchmark_repository.py` | ドメインモデルのみ使用 | ✅ 良い |
| `market_snapshot_repository.py` | ドメインモデルのみ使用 | ✅ 良い |
| `stock_metrics_repository.py` | ドメインモデルのみ使用 | ✅ 良い |

**修正方針:**

1. **`ScreenerFilter` → `application/dto/screener_dto.py`**
   - 既存の `ScreenerFilterInput` と統合
   - Repository IFはプリミティブパラメータを受け取るように変更

2. **`ScreenerResult` → `application/dto/screener_dto.py`**
   - 既存の `ScreenerResultOutput` と統合

3. **`StockData` → 削除、`StockAggregate` 型エイリアスに変更** ✅ 完了
   - 既存ドメインモデルの単なる入れ物は不要
   - `StockAggregate: TypeAlias = tuple[StockIdentity, PriceSnapshot | None, StockMetrics | None]`

4. **`RefreshJob` → `domain/models/refresh_job.py`**
   - エンティティとして適切な場所に配置

**修正後の構造:**

```
application/
└── dto/
    └── screener_dto.py
        ├── ScreenerFilterInput   # UI入力（既存）
        ├── ScreenerResultOutput  # UI出力（既存）
        └── StockSummaryOutput    # 一覧用サマリー（既存）

domain/
├── models/
│   └── refresh_job.py           # NEW: ジョブエンティティ
│
└── repositories/
    └── stock_query_repository.py
        ├── StockAggregate        # 型エイリアス（tuple）
        └── StockQueryRepository  # IFのみ
```

### Phase 2: Use Case の修正

| # | タスク | 状態 |
|---|--------|------|
| 2-1 | `screen_canslim_stocks.py` を `StockQueryRepository` を使うように修正 | [ ] |
| 2-2 | `get_stock_detail.py` を `StockQueryRepository` を使うように修正 | [ ] |
| 2-3 | `refresh_screener_data.py` の処理を確認・削除判断 | [ ] |

### Phase 3: 不要ファイルの削除

| # | タスク | ファイル | 状態 |
|---|--------|---------|------|
| 3-1 | Domain リポジトリIF削除 | `domain/repositories/stock_repository.py` | [ ] |
| 3-2 | Infra リポジトリ削除 | `infrastructure/repositories/postgres_stock_repository.py` | [ ] |
| 3-3 | Infra リポジトリ削除 | `infrastructure/repositories/postgres_screener_repository.py` | [ ] |
| 3-4 | マッパー削除 | `infrastructure/mappers/stock_mapper.py` | [ ] |
| 3-5 | マッパー削除 | `infrastructure/mappers/stock_model_mapper.py` | [ ] |

### Phase 4: 依存性の修正

| # | タスク | ファイル | 状態 |
|---|--------|---------|------|
| 4-1 | 依存性注入修正 | `presentation/dependencies.py` | [ ] |
| 4-2 | リポジトリ__init__修正 | `infrastructure/repositories/__init__.py` | [ ] |
| 4-3 | マッパー__init__修正 | `infrastructure/mappers/__init__.py` | [ ] |

### Phase 5: テーブル・モデル削除

| # | タスク | 状態 |
|---|--------|------|
| 5-1 | `screener_results` テーブル削除マイグレーション作成 | [ ] |
| 5-2 | `database/models/screener_result_model.py` 削除 | [ ] |

### Phase 6: クリーンアップ

| # | タスク | 状態 |
|---|--------|------|
| 6-1 | `domain/entities/` フォルダ削除 | [ ] |
| 6-2 | `domain/value_objects/` フォルダ削除 | [ ] |
| 6-3 | `domain-layer.md` ドキュメント更新 | [ ] |

---

## 影響を受けるAPI

| エンドポイント | 影響 | 対応方針 |
|---------------|------|---------|
| `GET /api/screener/stocks` | スクリーニング結果の取得元が変更 | `StockQueryRepository.screen()` を使用 |
| `GET /api/screener/stocks/{symbol}` | 詳細取得の取得元が変更 | `StockQueryRepository.get_stock()` を使用 |
| `POST /api/admin/refresh` | データ更新処理の変更 | Job フローを使用（既存の正規化フロー） |

---

## 目標とする最終構造

```
domain/
├── models/           # Entity + Value Object
│   ├── stock_identity.py
│   ├── price_snapshot.py
│   ├── stock_metrics.py
│   ├── market_benchmark.py
│   ├── market_status.py
│   ├── market_indicators.py
│   ├── quote.py
│   ├── watchlist_item.py
│   ├── paper_trade.py
│   ├── canslim_config.py
│   ├── canslim_score.py
│   └── performance_metrics.py
│
├── constants/        # 定数クラス
│   ├── trading_days.py
│   └── canslim_defaults.py
│
├── repositories/     # リポジトリIF
│   ├── stock_identity_repository.py
│   ├── price_snapshot_repository.py
│   ├── stock_metrics_repository.py
│   ├── stock_query_repository.py    # スクリーニング用
│   ├── benchmark_repository.py
│   └── ...
│
└── services/         # ドメインサービス
    ├── relative_strength_calculator.py
    ├── canslim_score_calculator.py
    └── ...
```

※ `entities/` と `value_objects/` フォルダは削除

---

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2024-12-30 | 初版作成、案A採用決定 |
| 2024-12-30 | Phase 1 分析結果追記（StockQueryRepository 機能比較） |
| 2024-12-30 | DDD依存関係の問題調査結果追記、タスク追加（1-4〜1-8） |
| 2024-12-30 | `StockData` を削除し `StockAggregate` 型エイリアスに変更（タスク1-4完了） |
