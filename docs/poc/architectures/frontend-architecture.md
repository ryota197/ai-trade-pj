# フロントエンド アーキテクチャ設計書

## 概要

Next.js 14 (App Router) + TypeScript + TailwindCSS を使用したフロントエンド設計。
BFF (Backend For Frontend) パターンを採用し、バックエンドAPIとの通信を抽象化。

---

## アーキテクチャ全体像

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        フロントエンド構成                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Pages (app/) - ページ単位で構成                 │   │
│  │                                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │ / (Dashboard)│  │  /screener   │  │/stock/[symbol]│           │   │
│  │  │ _components/ │  │ _components/ │  │ _components/  │           │   │
│  │  │ _hooks/      │  │ _hooks/      │  │ _hooks/       │           │   │
│  │  │ page.tsx     │  │ page.tsx     │  │ page.tsx      │           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  │                                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐                             │   │
│  │  │  /portfolio  │  │/admin/screener│                             │   │
│  │  │ _components/ │  │ _components/  │                             │   │
│  │  │ _hooks/      │  │ _hooks/       │                             │   │
│  │  │ page.tsx     │  │ page.tsx      │                             │   │
│  │  └──────────────┘  └──────────────┘                             │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                 │                                      │
│  ┌──────────────────────────────┴──────────────────────────────────┐   │
│  │                    Shared Components (components/)               │   │
│  │             layout/Header.tsx  |  ui/*.tsx                      │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                      │
│  ┌──────────────────────────────┴──────────────────────────────────┐   │
│  │                    BFF Route Handlers (app/api/)                 │   │
│  │   /api/market/*, /api/screener/*, /api/watchlist/*,             │   │
│  │   /api/trades/*, /api/performance, /api/admin/*                 │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                      │
│                                 ▼                                      │
│                        Backend API (FastAPI)                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ディレクトリ構成

```
frontend/src/
├── app/                        # ページ & BFF Route Handlers
│   │
│   ├── _components/            # Dashboard専用コンポーネント
│   │   ├── IndicatorCard.tsx
│   │   ├── MarketDashboard.tsx
│   │   └── MarketStatus.tsx
│   ├── _hooks/                 # Dashboard専用フック
│   │   └── useMarketStatus.ts
│   ├── layout.tsx
│   ├── page.tsx
│   │
│   ├── screener/
│   │   ├── _components/        # Screener専用
│   │   │   ├── FilterPanel.tsx
│   │   │   └── StockTable.tsx
│   │   ├── _hooks/
│   │   │   └── useScreener.ts
│   │   └── page.tsx
│   │
│   ├── stock/[symbol]/
│   │   ├── _components/        # Stock Detail専用
│   │   │   ├── CANSLIMScoreCard.tsx
│   │   │   ├── FundamentalsCard.tsx
│   │   │   └── PriceChart.tsx
│   │   ├── _hooks/
│   │   │   └── useStockData.ts
│   │   └── page.tsx
│   │
│   ├── portfolio/
│   │   ├── _components/        # Portfolio専用
│   │   │   ├── WatchlistTable.tsx
│   │   │   ├── TradeHistory.tsx
│   │   │   ├── TradeForm.tsx
│   │   │   ├── PerformanceSummary.tsx
│   │   │   └── AddToWatchlistButton.tsx
│   │   ├── _hooks/
│   │   │   ├── useWatchlist.ts
│   │   │   ├── useTrades.ts
│   │   │   └── usePerformance.ts
│   │   └── page.tsx
│   │
│   ├── admin/screener/
│   │   ├── _components/        # Admin専用
│   │   │   ├── RefreshPanel.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   └── ErrorList.tsx
│   │   ├── _hooks/
│   │   │   └── useAdminRefresh.ts
│   │   └── page.tsx
│   │
│   └── api/                    # BFF Route Handlers
│
├── components/                 # 共有コンポーネントのみ
│   ├── layout/
│   │   └── Header.tsx
│   └── ui/                     # 汎用UI部品
│       ├── button.tsx
│       ├── card.tsx
│       ├── badge.tsx
│       ├── StatusCard.tsx
│       └── ModuleCard.tsx
│
├── lib/                        # ユーティリティ
└── types/                      # 型定義
```

### ディレクトリ設計の原則

| 原則 | 説明 |
|------|------|
| ページ単位のカプセル化 | 各ページは `_components/`, `_hooks/` で専用コードを持つ |
| 共有は最小限 | `components/` には複数ページで使用するものだけ配置 |
| barrel file 禁止 | `index.ts` は使用しない。直接ファイルをインポート |
| インポート規則 | ページ専用は相対パス、共有は `@/` エイリアス |

### インポート例

```typescript
// ページ専用（相対パス）
import { StockTable } from "./_components/StockTable";
import { useScreener } from "./_hooks/useScreener";

// 共有（エイリアス）
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
```

---

## ページ構成

### 画面遷移図

```
                    ┌─────────────────┐
                    │   Dashboard     │
                    │       /         │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │  Screener   │   │  Portfolio  │   │    Admin    │
    │  /screener  │   │  /portfolio │   │   /admin/*  │
    └──────┬──────┘   └─────────────┘   └─────────────┘
           │
           ▼
    ┌─────────────┐
    │Stock Detail │
    │/stock/[sym] │
    └─────────────┘
```

### 各ページの責務

| ページ | パス | 責務 |
|--------|------|------|
| Dashboard | `/` | マーケット状態概要、モジュールへのナビゲーション |
| Screener | `/screener` | CAN-SLIM条件でのスクリーニング、フィルタリング |
| Stock Detail | `/stock/[symbol]` | 個別銘柄の詳細情報、チャート、CAN-SLIMスコア |
| Portfolio | `/portfolio` | ウォッチリスト、取引履歴、パフォーマンス |
| Admin | `/admin/screener` | スクリーニングデータ更新管理 |

---

## コンポーネント設計

### コンポーネント分類

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       コンポーネント階層                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【Page Components】 (app/*/page.tsx)                                  │
│    └─ ページ単位のコンテナ。データ取得・状態管理を担当                    │
│                                                                         │
│  【Page-Scoped Components】 (app/*/_components/)                       │
│    └─ ページ専用の機能コンポーネント。ビジネスロジックを含む              │
│       例: MarketDashboard, StockTable, TradeForm                       │
│    └─ 相対パスでインポート                                              │
│                                                                         │
│  【Shared UI Components】 (components/ui/)                             │
│    └─ 複数ページで使用する汎用プレゼンテーション                         │
│       例: Button, Card, Badge                                          │
│    └─ @/ エイリアスでインポート                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### ページ専用コンポーネント一覧

#### / (Dashboard) - `app/_components/`

| コンポーネント | 責務 |
|---------------|------|
| MarketDashboard | マーケット状態の統合表示 |
| MarketStatus | 市場ステータス（開場/閉場、VIX等） |
| IndicatorCard | 個別指標の表示カード |

#### /screener - `app/screener/_components/`

| コンポーネント | 責務 |
|---------------|------|
| StockTable | スクリーニング結果の一覧表示 |
| FilterPanel | フィルタ条件の入力パネル |

#### /stock/[symbol] - `app/stock/[symbol]/_components/`

| コンポーネント | 責務 |
|---------------|------|
| PriceChart | 株価チャート（Recharts使用） |
| FundamentalsCard | 財務指標の表示 |
| CANSLIMScoreCard | CAN-SLIMスコアの視覚化 |

#### /portfolio - `app/portfolio/_components/`

| コンポーネント | 責務 |
|---------------|------|
| WatchlistTable | ウォッチリスト一覧 |
| TradeHistory | 取引履歴一覧 |
| TradeForm | 取引記録フォーム |
| PerformanceSummary | パフォーマンスサマリー |
| AddToWatchlistButton | ウォッチリスト追加ボタン |

#### /admin/screener - `app/admin/screener/_components/`

| コンポーネント | 責務 |
|---------------|------|
| RefreshPanel | データ更新操作パネル |
| ProgressBar | 進捗バー表示 |
| ErrorList | エラー一覧表示 |

### 共有コンポーネント一覧

#### layout/ - `components/layout/`

| コンポーネント | 責務 |
|---------------|------|
| Header | アプリケーションヘッダー、ナビゲーション |

#### ui/ - `components/ui/`

| コンポーネント | 責務 |
|---------------|------|
| Button | 汎用ボタン |
| Card | カードレイアウト |
| Badge | ステータスバッジ |
| StatusCard | ステータス表示カード |
| ModuleCard | モジュールカード |

---

## 状態管理

### 方針

- **グローバル状態**: 使用しない（React Context / Redux不使用）
- **ローカル状態**: 各コンポーネント / ページで useState
- **サーバー状態**: カスタムフックで管理

### フック設計

フックは各ページの `_hooks/` ディレクトリに配置し、ページ専用として管理する。

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ページ専用 Hooks 構成                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  app/_hooks/                   app/screener/_hooks/                    │
│  ┌─────────────────┐           ┌─────────────────┐                     │
│  │ useMarketStatus │           │   useScreener   │                     │
│  │                 │           │                 │                     │
│  │ - status        │           │ - stocks        │                     │
│  │ - indicators    │           │ - filter        │                     │
│  │ - isLoading     │           │ - sort          │                     │
│  │ - error         │           │ - isLoading     │                     │
│  └─────────────────┘           └─────────────────┘                     │
│                                                                         │
│  app/stock/[symbol]/_hooks/    app/portfolio/_hooks/                   │
│  ┌─────────────────┐           ┌─────────────────┐                     │
│  │  useStockData   │           │   useWatchlist  │                     │
│  │                 │           │   useTrades     │                     │
│  │ - quote         │           │   usePerformance│                     │
│  │ - priceHistory  │           │                 │                     │
│  │ - financials    │           │                 │                     │
│  │ - canslimScore  │           │                 │                     │
│  └─────────────────┘           └─────────────────┘                     │
│                                                                         │
│  app/admin/screener/_hooks/                                            │
│  ┌─────────────────┐                                                   │
│  │ useAdminRefresh │                                                   │
│  │                 │                                                   │
│  │ - jobStatus     │                                                   │
│  │ - startRefresh  │                                                   │
│  │ - cancelJob     │                                                   │
│  │ - polling       │                                                   │
│  └─────────────────┘                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### フックの責務

| フック | 責務 | 配置場所 |
|--------|------|---------|
| useMarketStatus | マーケット状態の取得・キャッシュ | `app/_hooks/` |
| useScreener | スクリーニング結果の取得・フィルタ・ソート | `app/screener/_hooks/` |
| useStockData | 個別銘柄データの取得 | `app/stock/[symbol]/_hooks/` |
| useWatchlist | ウォッチリストのCRUD操作 | `app/portfolio/_hooks/` |
| useTrades | 取引記録のCRUD操作 | `app/portfolio/_hooks/` |
| usePerformance | パフォーマンス指標の取得 | `app/portfolio/_hooks/` |
| useAdminRefresh | データ更新ジョブの管理・ポーリング | `app/admin/screener/_hooks/` |

---

## BFF (Backend For Frontend) 設計

### 概念

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           BFF パターン                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [Browser]                                                              │
│      │                                                                  │
│      │  fetch('/api/screener/canslim')                                 │
│      ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Next.js Route Handler (app/api/screener/canslim/route.ts)      │   │
│  │                                                                   │   │
│  │  - リクエストの検証                                               │   │
│  │  - バックエンドAPI呼び出し                                        │   │
│  │  - レスポンス変換                                                 │   │
│  │  - エラーハンドリング                                             │   │
│  │  - キャッシュ制御                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│      │                                                                  │
│      │  backendGet('/api/v1/screener/canslim')                         │
│      ▼                                                                  │
│  [Backend API - FastAPI]                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### BFF Route Handler 一覧

| パス | メソッド | 責務 |
|------|---------|------|
| `/api/market/status` | GET | マーケット状態取得 |
| `/api/market/indicators` | GET | 市場指標取得 |
| `/api/screener/canslim` | GET | CAN-SLIMスクリーニング |
| `/api/screener/stock/[symbol]` | GET | 銘柄詳細取得 |
| `/api/watchlist` | GET, POST | ウォッチリスト取得・追加 |
| `/api/watchlist/[symbol]` | DELETE | ウォッチリスト削除 |
| `/api/trades` | GET, POST | 取引一覧・記録 |
| `/api/trades/[id]/close` | POST | 取引クローズ |
| `/api/trades/[id]/cancel` | POST | 取引キャンセル |
| `/api/performance` | GET | パフォーマンス取得 |
| `/api/admin/screener/refresh` | POST | データ更新開始 |
| `/api/admin/screener/refresh/[jobId]` | GET, DELETE | ジョブ状態・キャンセル |

### BFF のメリット

| 観点 | 説明 |
|------|------|
| セキュリティ | バックエンドURLをクライアントから隠蔽 |
| 柔軟性 | フロントエンド用にレスポンス形式を調整可能 |
| キャッシュ | Next.js のキャッシュ機構を活用 |
| エラー変換 | バックエンドエラーをユーザーフレンドリーに変換 |

---

## UIデザイン指針

### カラーパレット

| 用途 | CSS変数 | 説明 |
|------|---------|------|
| 背景 | `--background` | ページ背景 |
| カード背景 | `--card` | カード・パネル背景 |
| 文字（主） | `--foreground` | 主要テキスト |
| 文字（副） | `--muted-foreground` | 補助テキスト |
| プライマリ | `--primary` | アクションボタン、強調 |
| 成功 | `--success` / green | 上昇、成功状態 |
| 危険 | `--destructive` / red | 下落、エラー状態 |
| 警告 | yellow | 注意が必要な状態 |

### レイアウト原則

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Header (固定)                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Main Content Area                                               │   │
│  │                                                                   │   │
│  │  max-width: 7xl (1280px)                                         │   │
│  │  padding: 4 (16px) horizontal, 8 (32px) vertical                 │   │
│  │                                                                   │   │
│  │  ┌──────────────────┐  ┌──────────────────────────────────┐     │   │
│  │  │   Sidebar/Filter │  │   Main Content                    │     │   │
│  │  │   (1/4 width)    │  │   (3/4 width)                     │     │   │
│  │  │                  │  │                                    │     │   │
│  │  │                  │  │                                    │     │   │
│  │  └──────────────────┘  └──────────────────────────────────┘     │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### レスポンシブ対応

| ブレークポイント | 幅 | レイアウト |
|-----------------|-----|-----------|
| sm | 640px | 1カラム |
| md | 768px | 1-2カラム |
| lg | 1024px | 2カラム（サイドバー + メイン） |
| xl | 1280px | フル幅 |

---

## データフロー

### 取得パターン

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        データ取得フロー                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. ページマウント                                                       │
│     └─→ useEffect で hook の fetch 関数を呼び出し                        │
│                                                                         │
│  2. フック内                                                             │
│     └─→ isLoading = true                                                │
│     └─→ fetch('/api/...') via BFF                                       │
│     └─→ レスポンス処理                                                   │
│     └─→ state 更新                                                      │
│     └─→ isLoading = false                                               │
│                                                                         │
│  3. コンポーネント                                                       │
│     └─→ isLoading 時はスケルトン/スピナー表示                            │
│     └─→ error 時はエラーメッセージ表示                                   │
│     └─→ data 時は通常表示                                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 更新パターン

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        データ更新フロー                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. ユーザーアクション（ボタンクリック等）                                 │
│     └─→ hook の mutation 関数を呼び出し                                  │
│                                                                         │
│  2. フック内                                                             │
│     └─→ isLoading = true                                                │
│     └─→ fetch('/api/...', { method: 'POST/PUT/DELETE' })               │
│     └─→ 成功時: state 更新 or refetch                                   │
│     └─→ 失敗時: error 設定                                              │
│     └─→ isLoading = false                                               │
│                                                                         │
│  3. 楽観的更新（オプション）                                             │
│     └─→ API呼び出し前に UI を先行更新                                   │
│     └─→ 失敗時にロールバック                                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## エラーハンドリング

### エラー表示パターン

| パターン | 用途 | 表示場所 |
|---------|------|---------|
| インライン | フォームバリデーション | フィールド直下 |
| トースト | 操作結果通知 | 画面右上（未実装） |
| バナー | ページレベルエラー | コンテンツ上部 |
| フルページ | 致命的エラー | ページ全体 |

### エラー状態の視覚化

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ⚠ エラーが発生しました                                                  │
│  データの取得に失敗しました。ネットワーク接続を確認してください。          │
│                                                                         │
│  [再試行]                                                               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ローディング表示

### パターン

| パターン | 用途 |
|---------|------|
| スケルトン | テーブル、カード等の初回ロード |
| スピナー | ボタン内、小領域 |
| プログレスバー | 長時間処理（データ更新ジョブ） |
| 無効化 | 処理中のボタン・フォーム |

---

## 型定義

### 配置

```
types/
├── api.ts          # API共通型（ApiResponse等）
├── market.ts       # マーケット関連型
├── stock.ts        # 銘柄関連型
└── portfolio.ts    # ポートフォリオ関連型
```

### 命名規則

| 分類 | 命名パターン | 例 |
|------|-------------|-----|
| APIレスポンス | `{Entity}Response` | `MarketStatusResponse` |
| フォーム入力 | `{Action}Input` | `TradeInput` |
| フィルタ | `{Entity}Filter` | `ScreenerFilter` |
| 状態 | `{Entity}Status` | `JobStatus` |

---

## 今後の拡張ポイント

### 検討事項

| 項目 | 現状 | 将来 |
|------|------|------|
| 状態管理 | ローカル state | Zustand / Jotai 検討 |
| データフェッチ | カスタムフック | TanStack Query 検討 |
| フォーム | 手動管理 | React Hook Form 検討 |
| 通知 | 未実装 | Toast コンポーネント追加 |
| テーマ | ライトのみ | ダークモード対応 |
| i18n | 日本語のみ | 英語対応 |

---

## 関連ドキュメント

- `docs/poc/coding-standard/frontend-guidelines.md` - フロントエンドコーディング規約（ディレクトリ構成・インポート規則）
- `docs/poc/architectures/api-design.md` - API設計
