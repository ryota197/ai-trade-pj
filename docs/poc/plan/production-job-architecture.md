# 本番運用時のジョブアーキテクチャ

## 概要

PoC段階では FastAPI `BackgroundTasks` を使用しているが、本番運用時には Redis キューを使用したワーカーアーキテクチャへ移行する。

---

## 現在の実装（PoC）

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PoC アーキテクチャ                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [Frontend]                      [Backend - 単一プロセス]                │
│                                                                         │
│  POST /refresh ──────────────→  1. ジョブ作成 (DB保存)                   │
│       ←─────────────────────    2. job_id 即座に返却                    │
│                                  3. BackgroundTasks.add_task()          │
│                                       │                                 │
│                                       ▼                                 │
│                                  ┌──────────────┐                       │
│                                  │ 同一プロセス内 │                       │
│                                  │ で非同期実行   │                       │
│                                  │              │                       │
│  GET /status ────────────────→  │ 進捗をDBに保存 │                       │
│       ←─────────────────────    └──────────────┘                       │
│  (2秒ごとにポーリング)                                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 特徴

- キューイング: **なし**
- ワーカー: 同一プロセス内
- 状態管理: PostgreSQL のみ

### 制限事項

| 制限 | 影響 |
|------|------|
| サーバー再起動でタスク消失 | 実行中のジョブが失われる |
| 単一プロセス | スケールアウト不可 |
| リトライ機構なし | 失敗時の自動再実行ができない |

---

## 本番運用時の推奨構成

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      本番推奨アーキテクチャ                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [Frontend]         [API Server]         [Redis]        [Worker]        │
│                                                                         │
│  POST /refresh ───→ ジョブ作成 ─────────→ キューに投入 ───→ 処理実行     │
│       ←─────────── job_id返却                              │            │
│                                                             ▼            │
│                                          ┌─────────────────────────┐    │
│                                          │ Celery / ARQ Worker     │    │
│  GET /status ─────→ Redis/DBから取得 ←── │ - 進捗をRedis/DBに保存   │    │
│       ←───────────                       │ - リトライ自動実行       │    │
│                                          │ - 複数ワーカーでスケール │    │
│                                          └─────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 特徴

- キューイング: **Redis**
- ワーカー: 別プロセス（複数可）
- 状態管理: Redis + PostgreSQL

---

## 技術選定

### 推奨: ARQ

| 項目 | ARQ | Celery |
|------|-----|--------|
| 軽量さ | ◎ 軽量 | △ 重い |
| async対応 | ◎ ネイティブ | △ 要設定 |
| 学習コスト | ◎ 低い | △ 高い |
| 機能 | ○ 必要十分 | ◎ 豊富 |
| エコシステム | △ 小さい | ◎ 大きい |

小〜中規模のプロジェクトでは ARQ を推奨。

### ARQ 実装イメージ

```python
# backend/src/infrastructure/workers/arq_worker.py
from arq import create_pool
from arq.connections import RedisSettings

async def collect_stock_data(ctx, job_id: str, symbols: list[str]):
    """Job 1: データ収集"""
    use_case = ctx["collect_use_case"]
    await use_case.execute(job_id, symbols)

async def recalculate_rs_rating(ctx):
    """Job 2: RS Rating 再計算"""
    use_case = ctx["recalc_rs_use_case"]
    await use_case.execute()

async def recalculate_canslim_score(ctx):
    """Job 3: CAN-SLIM スコア再計算"""
    use_case = ctx["recalc_score_use_case"]
    await use_case.execute()

class WorkerSettings:
    functions = [
        collect_stock_data,
        recalculate_rs_rating,
        recalculate_canslim_score,
    ]
    redis_settings = RedisSettings(host="redis", port=6379)
    max_jobs = 10
    job_timeout = 3600  # 1時間
```

### ジョブ投入

```python
# backend/src/presentation/api/admin_controller.py
from arq import create_pool

@router.post("/screener/refresh")
async def start_refresh(request: RefreshRequest):
    # ジョブをDBに作成
    job = await use_case.create_job(input_)

    # ARQ キューに投入
    redis = await create_pool(RedisSettings())
    await redis.enqueue_job(
        "collect_stock_data",
        job.job_id,
        symbols,
    )

    return job
```

---

## インフラ構成

### Docker Compose

```yaml
version: "3.8"

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  worker:
    build: ./backend
    command: arq src.infrastructure.workers.arq_worker.WorkerSettings
    depends_on:
      - db
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  db:
    image: postgres:16
    # ...
```

### 本番環境

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │  API Server │    │  API Server │    │  API Server │  ← Auto Scaling │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                 │
│         │                  │                  │                         │
│         └──────────────────┼──────────────────┘                         │
│                            │                                            │
│                            ▼                                            │
│                   ┌─────────────────┐                                   │
│                   │  Redis Cluster  │                                   │
│                   └────────┬────────┘                                   │
│                            │                                            │
│         ┌──────────────────┼──────────────────┐                         │
│         │                  │                  │                         │
│         ▼                  ▼                  ▼                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │   Worker    │    │   Worker    │    │   Worker    │  ← Auto Scaling │
│  └─────────────┘    └─────────────┘    └─────────────┘                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 移行手順

### Phase 1: Redis 導入

1. Docker Compose に Redis 追加
2. Redis 接続設定を追加

### Phase 2: ARQ Worker 実装

1. `arq` パッケージをインストール
2. Worker 関数を実装
3. ジョブ投入ロジックを変更

### Phase 3: 既存コード修正

1. `BackgroundTasks` の使用箇所を ARQ に置換
2. ジョブ状態の取得を Redis 対応に

### Phase 4: テスト・デプロイ

1. ローカルで動作確認
2. ステージング環境でテスト
3. 本番デプロイ

---

## 関連 Issue

- Issue #9: 本番運用時のBackgroundTasks制限対応
- Issue #8: 管理者機能の認証実装

---

## 参考

- [ARQ 公式ドキュメント](https://arq-docs.helpmanual.io/)
- [Celery 公式ドキュメント](https://docs.celeryq.dev/)
