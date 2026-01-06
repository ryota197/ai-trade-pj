# Jobs層 実装ガイド

## 概要

Jobs層はバックグラウンドジョブの実行を担当する層。
長時間実行される処理、段階的計算、複数ジョブのオーケストレーションを行う。
Domain層のみに依存し、外部サービスはインターフェース経由で利用する。

---

## Application層との違い

| 観点 | Application (UseCase) | Jobs |
|------|----------------------|------|
| 実行方式 | 同期（リクエスト/レスポンス） | 非同期（バックグラウンド） |
| 実行時間 | 短時間（秒単位） | 長時間可（分〜時間） |
| 呼び出し元 | Controller | UseCase or スケジューラ |
| 進捗管理 | 不要 | 必要（DBで進捗追跡） |
| エラー影響 | リクエスト失敗 | 他銘柄の処理は継続 |

---

## ディレクトリ構造

```
backend/src/jobs/
├── lib/                          # 共通基盤
│   ├── base.py                   # Job 基底クラス
│   ├── state.py                  # ジョブ実行状態（進捗管理）
│   └── errors.py                 # ジョブ固有エラー
│
├── executions/                   # 個別ジョブ実装（単一責務）
│   ├── collect_stock_data.py     # Job 1: データ収集
│   ├── calculate_rs_rating.py    # Job 2: RS Rating 計算
│   └── calculate_canslim.py      # Job 3: CAN-SLIM スコア計算
│
└── flows/                        # 複数ジョブのオーケストレーション
    └── refresh_screener.py       # データ更新フロー
```

---

## 構成要素

| 要素 | 責務 | 配置場所 |
|------|------|----------|
| Job 基底クラス | 共通インターフェース定義 | `jobs/lib/base.py` |
| Execution | 単一責務のジョブ実装 | `jobs/executions/` |
| Flow | 複数ジョブのオーケストレーション | `jobs/flows/` |
| JobExecution | ジョブ実行状態（進捗管理） | `jobs/lib/state.py` |

---

## ジョブ一覧

| Job | 名前 | 責務 | 依存サービス |
|-----|------|------|-------------|
| Job 1 | `CollectStockDataJob` | 外部APIからデータ収集 | FinancialDataGateway, CANSLIMStockRepository |
| Job 2 | `CalculateRSRatingJob` | RS Rating パーセンタイル計算 | CANSLIMStockRepository, RSCalculator |
| Job 3 | `CalculateCANSLIMJob` | CAN-SLIM スコア計算 | CANSLIMStockRepository, CANSLIMScoreCalculator |

### ジョブ間の依存関係

```
Job 1: CollectStockData
  │  更新: price, volume, eps_growth, relative_strength, ...
  ▼
Job 2: CalculateRSRating
  │  更新: rs_rating (1-99)
  │  前提: 全銘柄の relative_strength が設定済み
  ▼
Job 3: CalculateCANSLIM
  │  更新: canslim_score, score_c/a/n/s/l/i/m
  │  前提: rs_rating が設定済み
  ▼
完了
```

---

## RefreshScreenerFlow

### PoC実装での制約

PoC実装では **S&P 500 固定** でデータ更新を行う。

```python
# jobs/flows/refresh_screener.py
DEFAULT_SOURCE = "sp500"

class RefreshScreenerFlow:
    async def run(self) -> FlowResult:
        """S&P 500銘柄のスクリーニングデータを更新"""
        symbols = await self.symbol_provider.get_symbols(DEFAULT_SOURCE)
        # Job 1 → Job 2 → Job 3 を順次実行
```

パラメータによるソース切り替えは行わない（将来の拡張時に再設計）。

---

## 進捗管理

### テーブル構成

| テーブル | 責務 |
|---------|------|
| `flow_executions` | フロー全体の状態管理 |
| `job_executions` | 各ジョブの状態管理 |

### ステータス

| ステータス | 説明 |
|-----------|------|
| `pending` | 待機中 |
| `running` | 実行中 |
| `completed` | 完了 |
| `failed` | 失敗 |
| `cancelled` | キャンセル |
| `skipped` | スキップ（ジョブのみ） |

---

## エラーハンドリング

### 原則

1. **銘柄単位で独立**: 1銘柄の失敗が他銘柄に影響しない
2. **エラー記録**: 失敗した銘柄とエラー内容をリストに記録
3. **処理継続**: 失敗してもスキップして次の銘柄へ
4. **ジョブ結果にエラー一覧を含める**

---

## 呼び出し方法

Controller からバックグラウンド実行:

```python
# presentation/api/admin_controller.py
@router.post("/screener/refresh")
async def start_refresh(
    background_tasks: BackgroundTasks,
    flow: RefreshScreenerFlow = Depends(get_refresh_screener_flow),
):
    background_tasks.add_task(flow.run)
    return ApiResponse(success=True, data={"status": "started"})
```

---

## 設計原則

1. **Domain層のみに依存**: Infrastructure層の実装に依存しない
2. **インターフェース経由**: 外部サービスは抽象インターフェースで定義
3. **単一責任**: 1ジョブ = 1責務
4. **段階的実行**: Job 1 → Job 2 → Job 3 の順に依存
5. **独立性**: 各銘柄の処理が他銘柄に影響しない

---

## 関連ドキュメント

- `docs/poc/plan/refresh-screener-usecase.md` - ジョブ設計詳細
- `docs/poc/architectures/layers/overview.md` - レイヤー設計概要
