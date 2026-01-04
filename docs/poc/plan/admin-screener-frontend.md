# 管理画面フロントエンド実装方針

## 概要

スクリーニングデータ更新の管理画面（`/admin/screener`）のフロントエンド実装方針。
バックエンドの Flow ベース進捗追跡 API に対応する UI を実装する。

---

## 現状分析

### バックエンド API（実装済み）

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| POST | `/admin/screener/refresh` | 更新開始 → `flow_id` 返却 |
| GET | `/admin/screener/refresh/{flow_id}/status` | フロー進捗取得 |
| GET | `/admin/screener/refresh/latest` | 最新フロー一覧取得 |
| DELETE | `/admin/screener/refresh/{flow_id}` | キャンセル（501 未実装） |

### バックエンド レスポンス形式

```typescript
// POST /admin/screener/refresh
interface RefreshJobResponse {
  flow_id: string;    // "pending" (バックグラウンド開始のため)
  status: string;     // "started"
  message: string;
}

// GET /admin/screener/refresh/{flow_id}/status
interface FlowStatusResponse {
  flow_id: string;
  flow_name: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  total_jobs: number;
  completed_jobs: number;
  current_job: string | null;
  started_at: string | null;
  completed_at: string | null;
  jobs: JobExecutionSchema[];
}

interface JobExecutionSchema {
  job_name: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}
```

### フロントエンド現状（要更新）

| ファイル | 現状 | 課題 |
|---------|------|------|
| `useAdminRefresh.ts` | `job_id` 使用、進捗なし | `flow_id` 対応、ポーリング追加 |
| `RefreshPanel.tsx` | 開始ボタンのみ | プログレスバー、ジョブリスト追加 |
| `route.ts` (API) | 旧レスポンス型 | 新 `flow_id` 形式に対応 |
| `[jobId]/route.ts` | 旧ステータス型 | 新 `FlowStatusResponse` 形式に対応 |

---

## 実装方針

### 1. ディレクトリ構成

```
frontend/src/
├── app/
│   ├── api/admin/screener/refresh/
│   │   ├── route.ts                    # POST: 更新開始
│   │   ├── latest/route.ts             # GET: 最新フロー一覧（新規）
│   │   └── [flowId]/
│   │       └── route.ts                # GET: フロー状態取得
│   │
│   └── admin/screener/
│       ├── page.tsx                    # ページ（既存）
│       ├── _components/
│       │   ├── RefreshPanel.tsx        # 更新パネル（拡張）
│       │   ├── FlowProgress.tsx        # フロー進捗表示（新規）
│       │   ├── JobStepList.tsx         # ジョブリスト（新規）
│       │   └── FlowHistory.tsx         # フロー履歴（新規）
│       └── _hooks/
│           ├── useAdminRefresh.ts      # 更新開始（修正）
│           └── useFlowHistory.ts       # 履歴取得（新規）
│
└── types/
    └── admin.ts                        # 管理画面型定義（新規）
```

---

### 2. 型定義（`types/admin.ts`）

```typescript
// ジョブステータス
export type JobStatus = "pending" | "running" | "completed" | "failed" | "skipped";

// フローステータス
export type FlowStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

// ジョブ実行情報
export interface JobExecution {
  job_name: string;
  status: JobStatus;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

// フローステータスレスポンス
export interface FlowStatusResponse {
  flow_id: string;
  flow_name: string;
  status: FlowStatus;
  total_jobs: number;
  completed_jobs: number;
  current_job: string | null;
  started_at: string | null;
  completed_at: string | null;
  jobs: JobExecution[];
}

// 更新開始レスポンス
export interface RefreshResponse {
  flow_id: string;
  status: string;
  message: string;
}

// シンボルソース
export type SymbolSource = "sp500" | "nasdaq100";
```

---

### 3. API Routes 修正

#### 3.1 `route.ts` (POST 更新開始)

```typescript
// 変更点: レスポンス型を RefreshResponse に変更
interface RefreshResponse {
  flow_id: string;  // job_id → flow_id
  status: string;
  message: string;
}
```

#### 3.2 `latest/route.ts` (GET 最新フロー一覧) - 新規

```typescript
// GET /api/admin/screener/refresh/latest
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const limit = searchParams.get("limit") || "10";

  const result = await backendGet<ApiResponse<FlowStatusResponse[]>>(
    `/admin/screener/refresh/latest?limit=${limit}`,
    { next: { revalidate: 0 } }
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}
```

#### 3.3 `[flowId]/route.ts` (GET フロー状態)

```typescript
// 変更点:
// - パス: [jobId] → [flowId]
// - レスポンス型を FlowStatusResponse に変更
// - DELETE は 501 を返すよう修正
```

---

### 4. カスタムフック

#### 4.1 `useAdminRefresh.ts` (修正)

```typescript
interface UseAdminRefreshReturn {
  isLoading: boolean;
  error: string | null;
  lastFlowId: string | null;  // job_id → flow_id
  startRefresh: (source: SymbolSource) => Promise<string | null>;
}
```

**主な変更:**
- `lastJobId` → `lastFlowId`
- 戻り値として `flow_id` を返す

#### 4.2 `useFlowHistory.ts` (新規)

```typescript
interface UseFlowHistoryReturn {
  flows: FlowStatusResponse[];
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useFlowHistory(limit?: number): UseFlowHistoryReturn {
  // GET /api/admin/screener/refresh/latest を呼び出し
  // 初期ロード + 手動リフレッシュ
}
```

---

### 5. コンポーネント

#### 5.1 `RefreshPanel.tsx` (拡張)

**追加機能:**
- 直近フローの状態表示（リロードで更新）

```tsx
export function RefreshPanel() {
  const [selectedSource, setSelectedSource] = useState<SymbolSource>("nasdaq100");
  const { isLoading, error, startRefresh } = useAdminRefresh();
  const { flows, refresh: refreshHistory } = useFlowHistory(1);
  const latestFlow = flows[0] ?? null;

  const handleStart = async () => {
    await startRefresh(selectedSource);
    refreshHistory(); // 履歴を再取得
  };

  return (
    <Card>
      {/* ソース選択 */}
      {/* 開始ボタン */}

      {/* 最新フローの進捗表示 */}
      {latestFlow && <FlowProgress status={latestFlow} />}

      {/* エラー表示 */}
    </Card>
  );
}
```

#### 5.2 `FlowProgress.tsx` (新規)

**表示内容:**
- フロー全体の進捗バー（completed_jobs / total_jobs）
- 現在実行中のジョブ名
- 経過時間
- ジョブステップリスト

```tsx
interface FlowProgressProps {
  status: FlowStatusResponse;
}

export function FlowProgress({ status }: FlowProgressProps) {
  const progress = (status.completed_jobs / status.total_jobs) * 100;

  return (
    <div className="space-y-4">
      {/* ステータスヘッダー */}
      <div className="flex items-center justify-between">
        <StatusBadge status={status.status} />
        <span className="text-sm text-muted-foreground">
          {status.completed_jobs} / {status.total_jobs} ジョブ完了
        </span>
      </div>

      {/* プログレスバー */}
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full bg-primary transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* 現在のジョブ */}
      {status.current_job && (
        <p className="text-sm">
          実行中: <span className="font-mono">{status.current_job}</span>
        </p>
      )}

      {/* ジョブリスト */}
      <JobStepList jobs={status.jobs} />
    </div>
  );
}
```

#### 5.3 `JobStepList.tsx` (新規)

**表示内容:**
- 各ジョブのステータスアイコン
- ジョブ名
- 実行時間（完了した場合）
- エラーメッセージ（失敗した場合）

```tsx
interface JobStepListProps {
  jobs: JobExecution[];
}

export function JobStepList({ jobs }: JobStepListProps) {
  return (
    <div className="space-y-2">
      {jobs.map((job) => (
        <div key={job.job_name} className="flex items-center gap-3">
          <JobStatusIcon status={job.status} />
          <div className="flex-1">
            <span className="font-mono text-sm">{formatJobName(job.job_name)}</span>
            {job.error_message && (
              <p className="text-xs text-destructive">{job.error_message}</p>
            )}
          </div>
          {job.completed_at && job.started_at && (
            <span className="text-xs text-muted-foreground">
              {formatDuration(job.started_at, job.completed_at)}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

// ジョブ名の日本語表示
function formatJobName(name: string): string {
  const names: Record<string, string> = {
    collect_stock_data: "データ収集",
    calculate_rs_rating: "RS Rating 計算",
    calculate_canslim: "CAN-SLIM スコア計算",
  };
  return names[name] || name;
}
```

#### 5.4 `FlowHistory.tsx` (新規)

**表示内容:**
- 過去のフロー実行履歴
- 各フローのステータス、開始時刻、所要時間

```tsx
export function FlowHistory() {
  const { flows, isLoading, refresh } = useFlowHistory(5);

  return (
    <Card>
      <CardHeader>
        <CardTitle>実行履歴</CardTitle>
      </CardHeader>
      <CardContent>
        {flows.map((flow) => (
          <div key={flow.flow_id} className="py-3 border-b last:border-0">
            <div className="flex items-center justify-between">
              <StatusBadge status={flow.status} />
              <span className="text-sm text-muted-foreground">
                {formatDateTime(flow.started_at)}
              </span>
            </div>
            <p className="text-sm mt-1">
              {flow.completed_jobs}/{flow.total_jobs} ジョブ
              {flow.completed_at && flow.started_at && (
                <span className="text-muted-foreground ml-2">
                  ({formatDuration(flow.started_at, flow.completed_at)})
                </span>
              )}
            </p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
```

---

### 6. ページ構成 (`page.tsx`)

```tsx
export default function AdminScreenerPage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="mx-auto max-w-4xl px-4 py-8">
        {/* ページヘッダー */}
        <div className="mb-8">...</div>

        {/* 更新パネル（進捗表示含む） */}
        <RefreshPanel />

        {/* 実行履歴 */}
        <div className="mt-8">
          <FlowHistory />
        </div>

        {/* 注意事項 */}
        <div className="mt-8 p-4 bg-muted/50 rounded-lg">...</div>
      </main>
    </div>
  );
}
```

---

## 実装順序

| # | タスク | 優先度 | 依存 |
|---|--------|--------|------|
| 1 | `types/admin.ts` 型定義作成 | P1 | - |
| 2 | API Routes 修正（flow_id 対応） | P1 | 1 |
| 3 | `latest/route.ts` 新規作成 | P1 | 1 |
| 4 | `useAdminRefresh.ts` 修正 | P1 | 1,2 |
| 5 | `useFlowHistory.ts` 新規作成 | P1 | 1,3 |
| 6 | `JobStepList.tsx` 新規作成 | P1 | 1 |
| 7 | `FlowProgress.tsx` 新規作成 | P1 | 1,6 |
| 8 | `RefreshPanel.tsx` 拡張 | P1 | 4,5,7 |
| 9 | `FlowHistory.tsx` 新規作成 | P2 | 5 |
| 10 | `page.tsx` 更新 | P2 | 8,9 |

---

## UI デザイン

### ステータスバッジ

| ステータス | 色 | アイコン |
|-----------|-----|---------|
| pending | グレー | Clock |
| running | 青（アニメーション） | Loader2 |
| completed | 緑 | CheckCircle |
| failed | 赤 | XCircle |
| cancelled | オレンジ | Ban |

### プログレスバー

```
[████████████░░░░░░░░] 60%
           ↑
        primary色
```

### ジョブリスト

```
✓ データ収集           12.3s
● RS Rating 計算       実行中...
○ CAN-SLIM スコア計算  待機中
```

---

## 技術的考慮事項

### 進捗確認方式

- **手動リロード**: ページリロードで最新状態を取得
- **開始直後の再取得**: `startRefresh()` 完了後に `refreshHistory()` を呼び出し

### キャッシュ

- フロー状態: `revalidate: 0`（常に最新）

### エラー表示

- API エラー: インライン表示
- ジョブエラー: ジョブリスト内に表示

---

## 将来拡張

- **自動ポーリング**: 実行中フローの自動進捗更新
- **WebSocket/SSE**: リアルタイム更新
- **詳細ログ**: 各ジョブの詳細ログ表示
- **リトライ機能**: 失敗したフローの再実行
- **スケジュール設定**: 定期実行の設定 UI
