# ジョブ進捗追跡の設計方針

## 概要

RefreshScreenerFlow の実行中に、各ジョブ（Job 1〜3）の進捗をリアルタイムで追跡できるようにするかの設計検討。

## 現状の課題

現在の実装では、`RefreshScreenerFlow.run()` が完了するまで進捗が分からない。

```python
# 現在の実装
async def run(self, input_) -> FlowResult:
    # Job 1 実行（進捗不明）
    collect_result = await self.collect_job.execute(...)

    # Job 2 実行（進捗不明）
    rs_result = await self.rs_rating_job.execute(...)

    # Job 3 実行（進捗不明）
    canslim_result = await self.canslim_job.execute(...)

    return FlowResult(...)  # ← ここで初めて結果が分かる
```

### 影響

- フロントエンドで進捗バーを表示できない
- 長時間実行時にユーザーが不安になる
- 失敗時にどのジョブで失敗したか即座に分からない

---

## 選択肢

### 案1: job_executions テーブルにステップごとに更新

各ジョブの完了時に `job_executions` テーブルを更新する。

#### 実装イメージ

```python
class RefreshScreenerFlow:
    def __init__(
        self,
        collect_job: CollectStockDataJob,
        rs_rating_job: CalculateRSRatingJob,
        canslim_job: CalculateCANSLIMJob,
        symbol_provider: SymbolProvider,
        job_repository: RefreshJobRepository,  # 追加
    ): ...

    async def run(self, input_) -> FlowResult:
        # ジョブ開始を記録
        job_id = self._job_repo.create(
            status="running",
            current_step="collect_stock_data",
            total_steps=3,
        )

        # Job 1
        collect_result = await self.collect_job.execute(...)
        self._job_repo.update_progress(
            job_id,
            current_step="calculate_rs_rating",
            completed_steps=1,
            step_results={"job1": collect_result},
        )

        # Job 2
        rs_result = await self.rs_rating_job.execute(...)
        self._job_repo.update_progress(
            job_id,
            current_step="calculate_canslim",
            completed_steps=2,
            step_results={"job2": rs_result},
        )

        # Job 3
        canslim_result = await self.canslim_job.execute(...)
        self._job_repo.update_progress(
            job_id,
            status="completed",
            completed_steps=3,
            step_results={"job3": canslim_result},
        )

        return FlowResult(job_id=job_id, ...)
```

#### メリット

| メリット | 説明 |
|---------|------|
| 永続化 | サーバー再起動でも進捗情報が消えない |
| 既存API活用 | GET /status エンドポイントがそのまま使える |
| 履歴保存 | 後で分析・デバッグに活用可能 |
| フロントエンド実装がシンプル | ポーリングで進捗取得可能 |

#### デメリット

| デメリット | 説明 | 深刻度 |
|-----------|------|--------|
| DB書き込み増加 | ステップ毎にUPDATE（4回程度） | 低 |
| Repository依存 | FlowにInfrastructure層の依存が追加 | 中 |
| トランザクション管理 | 進捗更新とデータ更新の整合性 | 高 |
| 失敗時の考慮 | ロールバック範囲の決定が必要 | 高 |

#### トランザクション管理の詳細

```python
# 選択肢A: 全体で1トランザクション
# - メリット: 整合性が保証される
# - デメリット: 途中経過が外部から見えない

# 選択肢B: 都度コミット（推奨）
# - メリット: 進捗がリアルタイムで見える
# - デメリット: Job 2失敗時、Job 1の結果は残る
```

#### 失敗時の振る舞い

| シナリオ | 対応案 |
|---------|--------|
| Job 1成功 → Job 2失敗 | Job 1のデータは残す（再実行時にスキップ可能） |
| Job 2成功 → Job 3失敗 | rs_ratingは更新済み、canslim_scoreは未計算 |
| サーバークラッシュ | status="running"のまま残る（ゾンビ検出が必要） |

---

### 案2: Redis/メモリキャッシュで進捗管理

一時的な進捗情報をインメモリまたはRedisで管理する。

#### 実装イメージ（インメモリ）

```python
class JobProgressStore:
    """シングルトンの進捗ストア"""
    _instance: "JobProgressStore | None" = None
    _progress: dict[str, dict] = {}

    @classmethod
    def get_instance(cls) -> "JobProgressStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def update(self, job_id: str, step: str, data: dict) -> None:
        self._progress[job_id] = {
            "current_step": step,
            "updated_at": datetime.now(),
            **data,
        }

    def get(self, job_id: str) -> dict | None:
        return self._progress.get(job_id)

    def delete(self, job_id: str) -> None:
        self._progress.pop(job_id, None)
```

#### 実装イメージ（Redis）

```python
class RedisJobProgressStore:
    def __init__(self, redis_client: Redis):
        self._redis = redis_client
        self._ttl = 3600  # 1時間で自動削除

    def update(self, job_id: str, step: str, data: dict) -> None:
        key = f"job_progress:{job_id}"
        self._redis.hset(key, mapping={"current_step": step, **data})
        self._redis.expire(key, self._ttl)

    def get(self, job_id: str) -> dict | None:
        key = f"job_progress:{job_id}"
        return self._redis.hgetall(key) or None
```

#### メリット

| メリット | 説明 |
|---------|------|
| 高速 | DBアクセスなし |
| DBへの負荷なし | 本番DBに影響しない |
| リアルタイム更新 | 頻繁な更新に適している |
| 一時情報に適切 | 完了後は不要な情報 |

#### デメリット

| デメリット | 説明 | 深刻度 |
|-----------|------|--------|
| 新たな依存 | Redis使用時は追加インフラが必要 | 中〜高 |
| 揮発性 | サーバー再起動で消える | 中 |
| マルチプロセス問題 | インメモリはプロセス間で共有不可 | 高 |
| 履歴なし | 後で分析できない | 低 |

---

### 案3: 現状維持（シンプル）

進捗追跡機能は実装せず、完了を待つ。

#### メリット

| メリット | 説明 |
|---------|------|
| 実装コストゼロ | 変更不要 |
| 複雑性なし | コードがシンプルなまま |
| テスト容易 | モックが不要 |

#### デメリット

| デメリット | 説明 | 深刻度 |
|-----------|------|--------|
| UX低下 | 進捗が見えない | 中 |
| デバッグ困難 | 失敗箇所の特定が難しい | 中 |
| スケール問題 | 大量データ時に問題 | 低（現時点） |

---

## 比較表

| 観点 | 案1: DB | 案2: Cache | 案3: 現状維持 |
|------|---------|------------|--------------|
| 実装コスト | 中 | 中〜高 | なし |
| 永続性 | あり | なし | - |
| リアルタイム性 | 中 | 高 | なし |
| インフラ追加 | 不要 | Redis時は必要 | 不要 |
| 履歴保存 | あり | なし | なし |
| 複雑性 | 中 | 中 | 低 |
| マルチプロセス対応 | あり | Redis時のみ | - |

---

## 推奨（参考）

| フェーズ | 推奨案 | 理由 |
|---------|--------|------|
| Phase 1（現在） | 案3 | シンプルに保つ。500銘柄は数分で完了 |
| Phase 2以降 | 案1 | 永続化・履歴が必要になる場合 |
| リアルタイム重視 | 案2 | WebSocket等と組み合わせる場合 |

---

## 決定事項

- **採用案:** 案1（job_executions テーブルにステップごとに更新）
- **理由:**
  - 永続化により進捗情報が失われない
  - 既存の GET /status エンドポイントを活用可能
  - 履歴として残り、後で分析・デバッグに活用可能
- **トランザクション方針:** 都度コミット（進捗がリアルタイムで見える）
- **失敗時の振る舞い:** Job N 失敗時、Job 1〜N-1 のデータは残す
- **再実行方針:** 新規 Flow として全体再実行（下記参照）
- **実装優先度:** 未定

### 主キー設計

- **job_executions の主キー:** `(flow_id, job_name)` 複合主キー
- **理由:** 同一 Flow 内で同じ Job は1つのみ存在（自然キー）
- **サロゲートキー (job_id) は不要**

### 再実行方針

失敗した Flow の再実行は、**新規 Flow として全体を再実行** する。

```
Flow A (failed)          Flow B (retry)
├── Job 1: completed     ├── Job 1: completed (高速 - データは既存)
├── Job 2: failed        ├── Job 2: completed
└── Job 3: skipped       └── Job 3: completed
```

**理由:**

1. **実装がシンプル:** 同一 Flow 内リトライは UPDATE/DELETE ロジックが複雑化
2. **履歴が残る:** 失敗した Flow A と成功した Flow B が別レコードとして残る
3. **冪等性:** Job 1（データ収集）は既存データがあれば高速にスキップ可能
4. **複合主キーと相性が良い:** 新規 flow_id なので衝突しない

---

## 実装方針

### データベース設計

Flow（親）と Job（子）の親子関係でテーブルを分離する。

```
┌─────────────────────────────────────────────────────────┐
│ flow_executions (親)                                    │
│ - RefreshScreenerFlow 全体の実行を管理                   │
│ - 1フロー = 1レコード                                    │
└─────────────────────────────────────────────────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────────────────────────────────────────┐
│ job_executions (子)                                     │
│ - 各Job (Job1, Job2, Job3) の実行を管理                 │
│ - 1フロー内の各ステップ = 1レコード                      │
└─────────────────────────────────────────────────────────┘
```

#### テーブル定義

```sql
-- フロー実行（親）
CREATE TABLE flow_executions (
    flow_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_name VARCHAR(50) NOT NULL,  -- 'refresh_screener'
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- 進捗サマリ
    total_jobs INT NOT NULL DEFAULT 3,
    completed_jobs INT NOT NULL DEFAULT 0,
    current_job VARCHAR(50),  -- 現在実行中のJob名

    -- タイミング
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 制約
    CONSTRAINT valid_flow_status CHECK (
        status IN ('pending', 'running', 'completed', 'failed', 'cancelled')
    )
);

-- ジョブ実行（子）
CREATE TABLE job_executions (
    flow_id UUID NOT NULL REFERENCES flow_executions(flow_id) ON DELETE CASCADE,
    job_name VARCHAR(50) NOT NULL,  -- 'collect_stock_data', 'calculate_rs_rating', 'calculate_canslim'
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- タイミング
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- 結果
    result JSONB,
    error_message TEXT,

    -- 制約
    PRIMARY KEY (flow_id, job_name),
    CONSTRAINT valid_job_status CHECK (
        status IN ('pending', 'running', 'completed', 'failed', 'skipped')
    )
);

-- インデックス
CREATE INDEX idx_flow_executions_status ON flow_executions(status, created_at DESC);
```

### 1. ディレクトリ構成

```
src/jobs/
├── lib/                             # フロー・ジョブ実行管理
│   ├── __init__.py
│   ├── models.py                    # FlowExecution, JobExecution [実装済み]
│   └── repositories.py              # リポジトリインターフェース [実装済み]
├── flows/
│   └── refresh_screener.py
└── executions/
    ├── base.py                      # Job 基底クラス [実装済み]
    ├── collect_stock_data.py
    ├── calculate_rs_rating.py
    └── calculate_canslim.py

src/infrastructure/
├── database/
│   ├── init.sql                     # テーブル定義 [実装済み]
│   ├── migrations/
│   │   └── 20260104_add_flow_executions.sql  # [実装済み]
│   └── models/
│       ├── flow_execution_model.py  # SQLAlchemy ORM（未実装）
│       └── job_execution_model.py   # SQLAlchemy ORM（未実装）
└── repositories/
    ├── postgres_flow_execution_repository.py   # 未実装
    └── postgres_job_execution_repository.py    # 未実装
```

### 2. エンティティ定義

`src/jobs/lib/models.py`:

```python
@dataclass
class FlowExecution:
    """フロー実行（親）"""
    flow_id: str
    flow_name: str  # 'refresh_screener'
    status: str  # pending, running, completed, failed, cancelled
    total_jobs: int = 3
    completed_jobs: int = 0
    current_job: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class JobExecution:
    """ジョブ実行（子）"""
    flow_id: str  # 複合主キー (1/2)
    job_name: str  # 複合主キー (2/2): 'collect_stock_data', 'calculate_rs_rating', 'calculate_canslim'
    status: str  # pending, running, completed, failed, skipped
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict | None = None
    error_message: str | None = None
```

### 3. リポジトリインターフェース

`src/jobs/lib/repositories.py`:

```python
class FlowExecutionRepository(ABC):
    """フロー実行リポジトリ"""

    @abstractmethod
    def create(self, flow: FlowExecution) -> FlowExecution:
        """フローを作成"""
        pass

    @abstractmethod
    def get_by_id(self, flow_id: str) -> FlowExecution | None:
        """フローIDで取得"""
        pass

    @abstractmethod
    def update(self, flow: FlowExecution) -> FlowExecution:
        """フローを更新"""
        pass

    @abstractmethod
    def get_latest(self, limit: int = 10) -> list[FlowExecution]:
        """最新のフローを取得"""
        pass


class JobExecutionRepository(ABC):
    """ジョブ実行リポジトリ"""

    @abstractmethod
    def create(self, job: JobExecution) -> JobExecution:
        """ジョブを作成"""
        pass

    @abstractmethod
    def get(self, flow_id: str, job_name: str) -> JobExecution | None:
        """複合主キーでジョブを取得"""
        pass

    @abstractmethod
    def get_by_flow_id(self, flow_id: str) -> list[JobExecution]:
        """フローIDで全ジョブを取得"""
        pass

    @abstractmethod
    def update(self, job: JobExecution) -> JobExecution:
        """ジョブを更新（flow_id, job_name で識別）"""
        pass
```

### 4. RefreshScreenerFlow の修正

```python
class RefreshScreenerFlow:
    def __init__(
        self,
        collect_job: CollectStockDataJob,
        rs_rating_job: CalculateRSRatingJob,
        canslim_job: CalculateCANSLIMJob,
        symbol_provider: SymbolProvider,
        flow_repository: FlowExecutionRepository,
        job_repository: JobExecutionRepository,
    ) -> None:
        self.collect_job = collect_job
        self.rs_rating_job = rs_rating_job
        self.canslim_job = canslim_job
        self.symbol_provider = symbol_provider
        self._flow_repo = flow_repository
        self._job_repo = job_repository

    async def run(self, input_: RefreshScreenerInput) -> FlowResult:
        # フロー開始を記録
        flow = FlowExecution(
            flow_id=str(uuid4()),
            flow_name="refresh_screener",
            status="running",
            started_at=datetime.now(timezone.utc),
            current_job="collect_stock_data",
        )
        self._flow_repo.create(flow)

        # 各ジョブのレコードを事前作成
        jobs = self._create_job_records(flow.flow_id)

        try:
            # Job 1: データ収集
            jobs[0].status = "running"
            jobs[0].started_at = datetime.now(timezone.utc)
            self._job_repo.update(jobs[0])

            collect_result = await self.collect_job.execute(...)

            jobs[0].status = "completed"
            jobs[0].completed_at = datetime.now(timezone.utc)
            jobs[0].result = asdict(collect_result)
            self._job_repo.update(jobs[0])

            flow.completed_jobs = 1
            flow.current_job = "calculate_rs_rating"
            self._flow_repo.update(flow)

            # Job 2, 3 も同様...

            # フロー完了
            flow.status = "completed"
            flow.completed_at = datetime.now(timezone.utc)
            flow.current_job = None
            self._flow_repo.update(flow)

        except Exception as e:
            # 失敗を記録
            flow.status = "failed"
            self._flow_repo.update(flow)
            raise

        return FlowResult(flow_id=flow.flow_id, ...)

    def _create_job_records(self, flow_id: str) -> list[JobExecution]:
        """ジョブレコードを事前作成"""
        job_names = [
            "collect_stock_data",
            "calculate_rs_rating",
            "calculate_canslim",
        ]
        jobs = []
        for job_name in job_names:
            job = JobExecution(
                flow_id=flow_id,
                job_name=job_name,
                status="pending",
            )
            self._job_repo.create(job)
            jobs.append(job)
        return jobs
```

### 5. dependencies.py の修正

```python
def get_refresh_screener_flow(
    db: Session = Depends(get_db),
) -> RefreshScreenerFlow:
    stock_repo = PostgresCANSLIMStockRepository(db)
    flow_repo = PostgresFlowExecutionRepository(db)
    job_repo = PostgresJobExecutionRepository(db)
    financial_gateway = YFinanceGateway()
    symbol_provider = StaticSymbolProvider()

    collect_job = CollectStockDataJob(...)
    rs_rating_job = CalculateRSRatingJob(...)
    canslim_job = CalculateCANSLIMJob(...)

    return RefreshScreenerFlow(
        collect_job=collect_job,
        rs_rating_job=rs_rating_job,
        canslim_job=canslim_job,
        symbol_provider=symbol_provider,
        flow_repository=flow_repo,
        job_repository=job_repo,
    )
```

### 6. 既存テーブルの扱い

| テーブル | 対応 |
|---------|------|
| `refresh_jobs` | 削除（flow_executions に置き換え） |
| `job_executions`（既存） | スキーマ変更して再利用 |

### 7. 実装順序

1. [x] データベースマイグレーション（flow_executions作成、job_executions変更）
   - `init.sql` 更新済み
   - `migrations/20260104_add_flow_executions.sql` 作成済み
2. [x] `src/jobs/lib/models.py` 作成
   - FlowStatus, JobStatus, FlowExecution, JobExecution
3. [x] `src/jobs/lib/repositories.py` 作成
   - FlowExecutionRepository, JobExecutionRepository インターフェース
4. [x] `src/jobs/lib/__init__.py` 更新（エクスポート追加）
5. [ ] `src/infrastructure/database/models/flow_execution_model.py` 作成
6. [ ] `src/infrastructure/database/models/job_execution_model.py` 作成
7. [ ] `src/infrastructure/repositories/postgres_flow_execution_repository.py` 作成
8. [ ] `src/infrastructure/repositories/postgres_job_execution_repository.py` 作成
9. [ ] RefreshScreenerFlow の修正
10. [ ] dependencies.py の修正
11. [ ] admin_controller の修正（GET /status レスポンス変更）
12. [ ] 単体テスト
13. [ ] 結合テスト
