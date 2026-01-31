# ダッシュボード改善設計書

## 概要

現状のダッシュボードは開発者向け情報（API Status, Database, Current Phase）が中心で、ユーザーにとって有用な情報が不足している。本設計では以下を実現する：

1. **マーケットデータ更新機能**: 管理画面からマーケット指標を更新可能に
2. **ダッシュボード刷新**: 投資判断に有用な情報を表示

---

## 1. マーケットデータ更新機能

### 1.1 アーキテクチャ

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Admin UI      │────▶│  Backend API    │────▶│   yfinance      │
│ /admin (タブ)   │     │ /admin/market   │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ market_snapshots│
                        │     (DB)        │
                        └─────────────────┘
```

### 1.2 バックエンド

#### 1.2.1 新規ジョブ: CollectMarketDataJob

**ファイル**: `backend/src/jobs/executions/collect_market_data.py`

```python
@dataclass
class CollectMarketInput:
    """マーケットデータ収集入力（現状は空）"""
    pass


@dataclass
class CollectMarketOutput:
    """マーケットデータ収集出力"""
    vix: float
    sp500_price: float
    sp500_rsi: float
    sp500_ma200: float
    put_call_ratio: float
    condition: str      # risk_on / neutral / risk_off
    score: int          # -5 ~ +5


class CollectMarketDataJob(Job[CollectMarketInput, CollectMarketOutput]):
    """
    マーケットデータ収集ジョブ

    責務:
        - yfinanceからマーケット指標を取得
        - MarketAnalyzerでスコア・状態を計算
        - market_snapshotsテーブルに保存
    """

    name = "collect_market_data"

    def __init__(
        self,
        market_query: MarketSnapshotQuery,
        gateway: YFinanceMarketDataGateway | None = None,
        analyzer: MarketAnalyzer | None = None,
    ) -> None:
        self._query = market_query
        self._gateway = gateway or YFinanceMarketDataGateway()
        self._analyzer = analyzer or MarketAnalyzer()

    async def execute(self, input_: CollectMarketInput | None = None) -> CollectMarketOutput:
        # 1. yfinanceからデータ取得
        vix = self._gateway.get_vix()
        sp500_price = self._gateway.get_sp500_price()
        sp500_rsi = self._gateway.get_sp500_rsi()
        sp500_ma200 = self._gateway.get_sp500_ma200()
        put_call_ratio = self._gateway.get_put_call_ratio()

        # 2. スコア計算
        result = self._analyzer.analyze(
            vix=vix,
            sp500_price=sp500_price,
            sp500_rsi=sp500_rsi,
            sp500_ma200=sp500_ma200,
            put_call_ratio=put_call_ratio,
        )

        # 3. DBに保存
        snapshot = MarketSnapshot(
            recorded_at=datetime.now(timezone.utc),
            vix=Decimal(str(vix)),
            sp500_price=Decimal(str(sp500_price)),
            sp500_rsi=Decimal(str(sp500_rsi)),
            sp500_ma200=Decimal(str(sp500_ma200)),
            put_call_ratio=Decimal(str(put_call_ratio)),
            condition=result.condition.value,
            score=result.score,
        )
        self._query.save(snapshot)

        return CollectMarketOutput(
            vix=vix,
            sp500_price=sp500_price,
            sp500_rsi=sp500_rsi,
            sp500_ma200=sp500_ma200,
            put_call_ratio=put_call_ratio,
            condition=result.condition.value,
            score=result.score,
        )
```

#### 1.2.2 新規フロー: RefreshMarketFlow

**ファイル**: `backend/src/jobs/flows/refresh_market.py`

```python
class RefreshMarketFlow:
    """
    マーケットデータ更新フロー

    実行順序:
      1. collect_market_data - yfinanceからマーケット指標を収集

    進捗追跡:
      - flow_executions / job_executions テーブルで管理
    """

    FLOW_NAME = "refresh_market"

    def __init__(
        self,
        collect_job: CollectMarketDataJob,
        flow_query: FlowExecutionQuery,
        job_query: JobExecutionQuery,
    ) -> None:
        self.collect_job = collect_job
        self._flow_query = flow_query
        self._job_query = job_query

    async def run(self) -> FlowResult:
        flow = FlowExecution(
            flow_id=str(uuid4()),
            flow_name=self.FLOW_NAME,
            total_jobs=1,
        )
        flow.start(first_job="collect_market_data")
        self._flow_query.create(flow)

        job = JobExecution(flow_id=flow.flow_id, job_name="collect_market_data")
        self._job_query.create(job)

        try:
            await self._execute_job(job, flow)
            flow.complete()
            self._flow_query.update(flow)

        except Exception:
            flow.fail()
            self._flow_query.update(flow)
            raise

        return FlowResult(
            flow_id=flow.flow_id,
            success=True,
            started_at=flow.started_at,
            completed_at=flow.completed_at,
            duration_seconds=flow.duration_seconds or 0,
        )

    async def _execute_job(self, job: JobExecution, flow: FlowExecution) -> None:
        job.start()
        self._job_query.update(job)

        try:
            result = await self.collect_job.execute(None)
            job.complete(result=asdict(result))
            self._job_query.update(job)
            flow.advance(next_job=None)
            self._flow_query.update(flow)

        except Exception as e:
            job.result = None
            job.fail(error_message=str(e))
            self._job_query.update(job)
            raise
```

#### 1.2.3 新規コントローラー: AdminMarketController

**ファイル**: `backend/src/presentation/controllers/admin_market_controller.py`

```python
router = APIRouter(prefix="/admin/market", tags=["admin-market"])


@router.post("/refresh", response_model=ApiResponse[RefreshResponse])
async def start_market_refresh(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ApiResponse[RefreshResponse]:
    """マーケットデータ更新を開始"""
    flow = _create_refresh_market_flow(db)
    flow_id = str(uuid4())

    background_tasks.add_task(_run_flow, flow, flow_id)

    return ApiResponse(
        success=True,
        data=RefreshResponse(flow_id=flow_id, message="Market refresh started"),
    )


@router.get("/refresh/latest", response_model=ApiResponse[list[FlowStatusResponse]])
def get_latest_market_flows(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> ApiResponse[list[FlowStatusResponse]]:
    """最新のマーケット更新フローを取得"""
    query = FlowExecutionQuery(db)
    flows = query.find_by_name("refresh_market", limit=limit)
    # ... 変換処理
```

#### 1.2.4 MarketSnapshotQuery 拡張

**ファイル**: `backend/src/queries/market_snapshot.py`

```python
class MarketSnapshotQuery:
    # 既存メソッド...

    def save(self, snapshot: MarketSnapshot) -> MarketSnapshot:
        """スナップショットを保存"""
        self._session.add(snapshot)
        self._session.commit()
        self._session.refresh(snapshot)
        return snapshot
```

### 1.3 フロントエンド

#### 1.3.1 管理画面のタブ化

**現状**:
```
/admin/screener  - スクリーナー管理のみ
```

**変更後**:
```
/admin           - タブ式統合管理画面
├── タブ: スクリーナー（既存機能）
└── タブ: マーケット（新規）
```

#### 1.3.2 ディレクトリ構成

```
frontend/src/app/admin/
├── page.tsx                      # タブ式メインページ（新規）
├── layout.tsx                    # 共通レイアウト
├── _components/
│   ├── AdminTabs.tsx             # タブ切り替えUI（新規）
│   ├── ScreenerTab.tsx           # スクリーナータブ（既存移植）
│   └── MarketTab.tsx             # マーケットタブ（新規）
├── _hooks/
│   ├── useAdminRefresh.ts        # 既存
│   ├── useFlowHistory.ts         # 既存
│   └── useMarketRefresh.ts       # 新規
└── screener/
    └── page.tsx                  # 削除 or リダイレクト
```

#### 1.3.3 新規コンポーネント: AdminTabs

```tsx
// frontend/src/app/admin/_components/AdminTabs.tsx

"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScreenerTab } from "./ScreenerTab";
import { MarketTab } from "./MarketTab";

export function AdminTabs() {
  return (
    <Tabs defaultValue="screener" className="w-full">
      <TabsList className="grid w-full grid-cols-2 max-w-md">
        <TabsTrigger value="screener">スクリーナー</TabsTrigger>
        <TabsTrigger value="market">マーケット</TabsTrigger>
      </TabsList>

      <TabsContent value="screener" className="mt-6">
        <ScreenerTab />
      </TabsContent>

      <TabsContent value="market" className="mt-6">
        <MarketTab />
      </TabsContent>
    </Tabs>
  );
}
```

#### 1.3.4 新規コンポーネント: MarketTab

```tsx
// frontend/src/app/admin/_components/MarketTab.tsx

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useMarketRefresh } from "../_hooks/useMarketRefresh";
import { FlowHistory } from "./FlowHistory";

export function MarketTab() {
  const {
    latestSnapshot,
    isRefreshing,
    startRefresh,
    flowHistory
  } = useMarketRefresh();

  return (
    <div className="space-y-6">
      {/* 現在の状態 */}
      <Card>
        <CardHeader>
          <CardTitle>マーケットデータ更新</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {latestSnapshot ? (
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">最終更新:</span>
                <span className="ml-2 font-medium">
                  {new Date(latestSnapshot.recorded_at).toLocaleString("ja-JP")}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">状態:</span>
                <span className="ml-2 font-medium">
                  {latestSnapshot.condition.toUpperCase()} (スコア: {latestSnapshot.score})
                </span>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              マーケットデータがありません。更新を実行してください。
            </p>
          )}

          <Button
            onClick={startRefresh}
            disabled={isRefreshing}
          >
            {isRefreshing ? "更新中..." : "更新開始"}
          </Button>
        </CardContent>
      </Card>

      {/* 実行履歴 */}
      <FlowHistory
        flows={flowHistory}
        title="実行履歴"
      />
    </div>
  );
}
```

---

## 2. ダッシュボード刷新

### 2.1 現状の問題点

| 要素 | 問題 |
|-----|------|
| API Status | 開発者向け、ユーザーには不要 |
| Database | 開発者向け、ユーザーには不要 |
| Current Phase | 開発フェーズ表示、完全に不要 |
| Module Cards | "coming-soon"表示、既に実装済みで古い |

### 2.2 新しいダッシュボード設計

```
┌─────────────────────────────────────────────────────────────┐
│ Header                                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Market Overview                                             │
│ ┌─────────┬─────────┬─────────┬─────────┬─────────┐        │
│ │ 状態    │ VIX     │ S&P500  │ RSI     │ P/C     │        │
│ │ NEUTRAL │ 18.5    │ 5,234   │ 55.2    │ 0.85    │        │
│ │ スコア:0│         │         │         │         │        │
│ └─────────┴─────────┴─────────┴─────────┴─────────┘        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Top CAN-SLIM Stocks               [スクリーナーを開く →]   │
│ ┌────────┬──────────┬────────┬─────────┬──────────┐        │
│ │ Symbol │ Name     │ Price  │ RS      │ Score    │        │
│ ├────────┼──────────┼────────┼─────────┼──────────┤        │
│ │ NVDA   │ NVIDIA   │ $450   │ 98      │ 95       │        │
│ │ AAPL   │ Apple    │ $189   │ 92      │ 88       │        │
│ │ MSFT   │ Microsoft│ $378   │ 90      │ 85       │        │
│ │ ...    │          │        │         │          │        │
│ └────────┴──────────┴────────┴─────────┴──────────┘        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Quick Actions                                               │
│ ┌─────────────────┐ ┌─────────────────┐ ┌────────────────┐ │
│ │ 📊 スクリーナー │ │ 👁 ウォッチリスト│ │ 💼 ポートフォリオ│ │
│ │ CAN-SLIM条件で  │ │ 注目銘柄を      │ │ ペーパートレード│ │
│ │ 銘柄を検索      │ │ 管理            │ │ を管理          │ │
│ └─────────────────┘ └─────────────────┘ └────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 コンポーネント構成

```
frontend/src/app/
├── page.tsx                          # ダッシュボード（大幅修正）
├── _components/
│   ├── MarketDashboard.tsx           # 既存（維持）
│   ├── MarketStatus.tsx              # 既存（維持）
│   ├── IndicatorCard.tsx             # 既存（維持）
│   ├── TopStocksCard.tsx             # 新規
│   └── QuickActions.tsx              # 新規
└── _hooks/
    ├── useMarketStatus.ts            # 既存（維持）
    └── useTopStocks.ts               # 新規
```

### 2.4 新規コンポーネント: TopStocksCard

```tsx
// frontend/src/app/_components/TopStocksCard.tsx

"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight } from "lucide-react";
import { useTopStocks } from "../_hooks/useTopStocks";

export function TopStocksCard() {
  const { stocks, isLoading, error } = useTopStocks(5);

  if (isLoading) {
    return <Card className="animate-pulse h-64" />;
  }

  if (error || stocks.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          スクリーニングデータがありません
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Top CAN-SLIM Stocks</CardTitle>
        <Link
          href="/screener"
          className="text-sm text-primary hover:underline flex items-center gap-1"
        >
          すべて見る <ArrowRight className="h-4 w-4" />
        </Link>
      </CardHeader>
      <CardContent>
        <table className="w-full">
          <thead>
            <tr className="text-xs text-muted-foreground border-b">
              <th className="text-left py-2">Symbol</th>
              <th className="text-right py-2">Price</th>
              <th className="text-right py-2">Change</th>
              <th className="text-right py-2">RS</th>
              <th className="text-right py-2">Score</th>
            </tr>
          </thead>
          <tbody>
            {stocks.map((stock) => (
              <tr key={stock.symbol} className="border-b last:border-0">
                <td className="py-3">
                  <Link
                    href={`/stock/${stock.symbol}`}
                    className="font-mono font-bold text-primary hover:underline"
                  >
                    {stock.symbol}
                  </Link>
                </td>
                <td className="text-right font-mono">
                  ${stock.price.toFixed(2)}
                </td>
                <td className={`text-right font-mono ${
                  stock.change_percent >= 0 ? "text-green-600" : "text-red-600"
                }`}>
                  {stock.change_percent >= 0 ? "+" : ""}
                  {stock.change_percent.toFixed(2)}%
                </td>
                <td className="text-right">
                  <Badge variant="secondary">{stock.rs_rating}</Badge>
                </td>
                <td className="text-right">
                  <Badge>{stock.canslim_score}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
```

### 2.5 新規コンポーネント: QuickActions

```tsx
// frontend/src/app/_components/QuickActions.tsx

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Search, Eye, Briefcase } from "lucide-react";

const actions = [
  {
    title: "スクリーナー",
    description: "CAN-SLIM条件で銘柄を検索",
    href: "/screener",
    icon: Search,
  },
  {
    title: "ウォッチリスト",
    description: "注目銘柄を管理",
    href: "/portfolio?tab=watchlist",
    icon: Eye,
  },
  {
    title: "ポートフォリオ",
    description: "ペーパートレードを管理",
    href: "/portfolio",
    icon: Briefcase,
  },
];

export function QuickActions() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {actions.map((action) => (
        <Link key={action.href} href={action.href}>
          <Card className="h-full hover:bg-muted/50 transition-colors cursor-pointer">
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="p-2 rounded-lg bg-primary/10">
                  <action.icon className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">{action.title}</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    {action.description}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}
```

### 2.6 修正後の page.tsx

```tsx
// frontend/src/app/page.tsx

import { Header } from "@/components/layout/Header";
import { MarketDashboard } from "./_components/MarketDashboard";
import { TopStocksCard } from "./_components/TopStocksCard";
import { QuickActions } from "./_components/QuickActions";

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-8 space-y-8">
        {/* Market Overview */}
        <section>
          <h2 className="mb-4 text-lg font-semibold">Market Overview</h2>
          <MarketDashboard />
        </section>

        {/* Top Stocks */}
        <section>
          <TopStocksCard />
        </section>

        {/* Quick Actions */}
        <section>
          <h2 className="mb-4 text-lg font-semibold">Quick Actions</h2>
          <QuickActions />
        </section>
      </main>
    </div>
  );
}
```

---

## 3. 実装タスク一覧

### Phase 1: マーケットデータ更新機能

| # | タスク | ファイル |
|---|--------|---------|
| 1-1 | CollectMarketDataJob 作成 | `jobs/executions/collect_market_data.py` |
| 1-2 | RefreshMarketFlow 作成 | `jobs/flows/refresh_market.py` |
| 1-3 | MarketSnapshotQuery.save() 追加 | `queries/market_snapshot.py` |
| 1-4 | AdminMarketController 作成 | `presentation/controllers/admin_market_controller.py` |
| 1-5 | main.py にルーター登録 | `main.py` |
| 1-6 | フロントエンド API Route 作成 | `app/api/admin/market/` |
| 1-7 | 管理画面タブ化 | `app/admin/` |
| 1-8 | MarketTab コンポーネント作成 | `app/admin/_components/MarketTab.tsx` |

### Phase 2: ダッシュボード刷新

| # | タスク | ファイル |
|---|--------|---------|
| 2-1 | TopStocksCard 作成 | `app/_components/TopStocksCard.tsx` |
| 2-2 | useTopStocks フック作成 | `app/_hooks/useTopStocks.ts` |
| 2-3 | QuickActions 作成 | `app/_components/QuickActions.tsx` |
| 2-4 | page.tsx 修正 | `app/page.tsx` |
| 2-5 | 不要コンポーネント削除 | `StatusCard`, `ModuleCard` |

---

## 4. API設計

### 4.1 新規エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/admin/market/refresh` | マーケットデータ更新開始 |
| GET | `/api/admin/market/refresh/latest` | 最新フロー一覧取得 |

### 4.2 レスポンス例

**POST /api/admin/market/refresh**
```json
{
  "success": true,
  "data": {
    "flow_id": "uuid-xxx",
    "message": "Market refresh started"
  }
}
```

**GET /api/admin/market/refresh/latest**
```json
{
  "success": true,
  "data": [
    {
      "flow_id": "uuid-xxx",
      "flow_name": "refresh_market",
      "status": "completed",
      "total_jobs": 1,
      "completed_jobs": 1,
      "started_at": "2026-01-31T10:00:00Z",
      "completed_at": "2026-01-31T10:00:03Z",
      "jobs": [
        {
          "job_name": "collect_market_data",
          "status": "completed",
          "result": {
            "vix": 18.5,
            "sp500_price": 5234.12,
            "condition": "neutral",
            "score": 0
          }
        }
      ]
    }
  ]
}
```

---

## 5. 備考

- Market Overviewはマーケットデータがない場合、エラー表示ではなく「データなし」メッセージを表示
- 管理画面の `/admin/screener` は `/admin` にリダイレクト（後方互換性）
- 将来的にはスケジュール実行（毎朝自動更新）も検討可能
