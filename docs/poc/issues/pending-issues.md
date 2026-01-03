# 積み残しIssue一覧

実装状況調査で発見された積み残し項目。GitHubにissueを作成する際のテンプレートとして使用。

---

## Issue #1: PortfolioページにHeaderコンポーネントを追加

**Labels**: `enhancement`, `frontend`, `priority:high`

### 概要

PortfolioページにHeaderコンポーネントがなく、ナビゲーション体験が他のページと不整合になっている。

### 現状

| ページ | Header |
|--------|--------|
| `/` (ホーム) | ✅ あり |
| `/screener` | ✅ あり |
| `/stock/*` | ✅ あり |
| `/portfolio` | ❌ なし |

### 影響

- ホームに戻るリンクがない
- ナビゲーション体験の不整合

### 対策

`frontend/src/app/portfolio/page.tsx` にHeaderコンポーネントを追加

```tsx
import { Header } from "@/components/layout/Header";

export default function PortfolioPage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />  {/* 追加 */}
      <div className="container mx-auto px-4 py-8">
        {/* 既存のコンテンツ */}
      </div>
    </div>
  );
}
```

### 関連ドキュメント

- `docs/poc/plan/implementation-status.md` PENDING-004
- `docs/poc/architecture-review.md` ISSUE-010

### 工数

小（10分程度）

---

## Issue #2: 個別銘柄ページでCAN-SLIMスコアを表示

**Labels**: `bug`, `frontend`, `priority:high`

### 概要

個別銘柄詳細ページ（`/stock/[symbol]`）でCAN-SLIMスコアが表示されない。

### 現状

```tsx
// frontend/src/app/stock/[symbol]/page.tsx (122行目)
<CANSLIMScoreCard score={null} isLoading={isLoading} />
```

常に `score={null}` を渡しているため、「スコアデータがありません」と表示される。

### 原因

`useStockData` hookは以下のデータのみ取得している：
- `quote` - 株価クォート（`/api/data/quote/{symbol}`）
- `priceHistory` - 価格履歴（`/api/data/history/{symbol}`）
- `financials` - 財務指標（`/api/data/financials/{symbol}`）

CAN-SLIMスコアは `/api/screener/stock/{symbol}` から取得する必要があるが、呼び出していない。

### 対策

#### 案1: useStockData を拡張

```tsx
// frontend/src/hooks/useStockData.ts
export function useStockData(symbol: string, period: string = "1y") {
  // 既存のstate...
  const [stockDetail, setStockDetail] = useState<StockDetail | null>(null);

  const fetchData = useCallback(async () => {
    const [quoteRes, historyRes, financialsRes, detailRes] = await Promise.all([
      fetch(`/api/data/quote/${symbol}`),
      fetch(`/api/data/history/${symbol}?period=${period}&interval=1d`),
      fetch(`/api/data/financials/${symbol}`).catch(() => null),
      fetch(`/api/screener/stock/${symbol}`).catch(() => null),  // 追加
    ]);
    // ...
  }, [symbol, period]);

  return {
    quote,
    priceHistory,
    financials,
    stockDetail,  // CAN-SLIMスコアを含む
    // ...
  };
}
```

#### 案2: 専用hook を作成

```tsx
// frontend/src/hooks/useStockDetail.ts
export function useStockDetail(symbol: string) {
  // /api/screener/stock/{symbol} を呼び出してStockDetailを取得
}
```

### 関連ドキュメント

- `docs/poc/plan/implementation-status.md` PENDING-002
- `docs/poc/plan/phase3-screener.md` 3.6節

### 工数

中（1時間程度）

---

## Issue #3: 管理者向けデータ更新機能の実装

**Labels**: `enhancement`, `backend`, `frontend`, `priority:medium`

### 概要

スクリーニングデータを手動で更新するための管理者向けAPI・UIを実装する。

### 背景

スクリーニングデータの計算（yfinance API呼び出し、RS Rating計算、CAN-SLIMスコア計算）はコストが高いため、ユーザーリクエスト毎ではなく、事前にバッチ処理で計算しDBにキャッシュする設計。

PoC段階では、管理者が手動でデータ更新をトリガーできるAPIを提供する。

### 実装内容

#### Backend API

| メソッド | エンドポイント | 説明 | 優先度 |
|---------|---------------|------|--------|
| POST | `/api/admin/screener/refresh` | 更新開始 | P1 |
| GET | `/api/admin/screener/refresh/{job_id}/status` | 進捗確認 | P2 |
| DELETE | `/api/admin/screener/refresh/{job_id}` | キャンセル | P3 |

#### Frontend

- `/admin/screener` ページ作成
- 更新開始ボタン
- プログレスバーコンポーネント
- リアルタイム進捗表示（ポーリング）
- エラー一覧表示

### 詳細設計

`docs/poc/plan/phase3-admin-refresh.md` を参照

### 関連ドキュメント

- `docs/poc/plan/implementation-status.md` PENDING-003
- `docs/poc/plan/phase3-admin-refresh.md`

### 工数

大（1日程度）

---

## Issue #4: Marketスナップショットバッチ処理の実装

**Labels**: `enhancement`, `backend`, `priority:low`

### 概要

Market状態を定期的にDBに保存するバッチ処理を実装する。

### 背景

現在のAPIはリアルタイムでyfinanceからデータを取得し、DBには保存しない。
履歴分析やトレンド把握のため、将来的にバッチジョブでスナップショットを保存する。

### 現状

- `market_snapshots` テーブル: ✅ 定義済み（`init.sql`）
- `MarketSnapshotModel`: ✅ 定義済み
- `PostgresMarketRepository.save()`: ✅ 実装済み
- 定期実行の仕組み: ❌ 未実装

### 実装内容

1. バッチジョブの実装
   - APScheduler または cron を使用
   - 1時間ごとに実行

2. 実行ロジック
   ```python
   # 疑似コード
   async def save_market_snapshot():
       use_case = GetMarketStatusUseCase(...)
       status = await use_case.execute()
       repository = PostgresMarketRepository(...)
       await repository.save(status)
   ```

3. 履歴取得API（オプション）
   - `GET /api/market/history` - 過去のスナップショット一覧

### 関連ドキュメント

- `docs/poc/plan/implementation-status.md` PENDING-001
- `docs/poc/plan/phase2-market.md`「将来対応（バックログ）」

### 工数

中（半日程度）

---

## GitHub Issue 作成コマンド

`gh` CLIが利用可能な場合、以下のコマンドでissueを作成できる：

```bash
# Issue #1
gh issue create \
  --title "PortfolioページにHeaderコンポーネントを追加" \
  --label "enhancement,frontend,priority:high" \
  --body-file docs/poc/issues/issue-1-body.md

# Issue #2
gh issue create \
  --title "個別銘柄ページでCAN-SLIMスコアを表示" \
  --label "bug,frontend,priority:high" \
  --body-file docs/poc/issues/issue-2-body.md

# Issue #3
gh issue create \
  --title "管理者向けデータ更新機能の実装" \
  --label "enhancement,backend,frontend,priority:medium" \
  --body-file docs/poc/issues/issue-3-body.md

# Issue #4
gh issue create \
  --title "Marketスナップショットバッチ処理の実装" \
  --label "enhancement,backend,priority:low" \
  --body-file docs/poc/issues/issue-4-body.md
```

---

## Issue #5: 管理者機能の認証実装

**Labels**: `enhancement`, `backend`, `security`, `priority:medium`

### 概要

管理者機能へのアクセス制御のため、認証機能を実装する。

### 背景

現在のPoC実装ではローカル環境専用のため認証機能がない。
デプロイ時には管理者APIエンドポイントへの不正アクセスを防ぐ必要がある。

### 対象エンドポイント

| エンドポイント | 説明 |
|---------------|------|
| `POST /api/admin/screener/refresh` | スクリーニングデータ更新開始 |
| `GET /api/admin/screener/refresh/{job_id}/status` | 進捗確認 |
| `DELETE /api/admin/screener/refresh/{job_id}` | キャンセル |
| `/admin/*` | 管理者UIページ |

### 実装案

1. **API Key認証**: 環境変数でキーを設定、Headerで送信
2. **Basic認証**: admin:password形式
3. **OAuth/JWT**: 将来のマルチユーザー対応時

### 関連ドキュメント

- `docs/poc/plan/plan-overview.md` - PoC対象外として記載
- `docs/poc/issues/issue-3-body.md` - 管理者機能

### 工数

中（半日〜1日程度）

---

## 優先度

| Issue | タイトル | 優先度 | 工数 | 状態 |
|-------|---------|--------|------|------|
| #1 | PortfolioページにHeader追加 | 高 | 小 | ✅ 完了 |
| #2 | CAN-SLIMスコア表示 | 高 | 中 | ✅ 完了 |
| #3 | 管理者向けデータ更新機能 | 中 | 大 | 🔴 未対応 |
| #4 | Marketスナップショットバッチ | 低 | 中 | 🔴 未対応 |
| #5 | 管理者機能の認証実装 | 中 | 中 | 🔴 未対応（デプロイ時） |
