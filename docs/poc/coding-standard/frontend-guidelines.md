# Frontend コーディング規約

## 概要

Next.js 16 + TypeScript + TailwindCSS + shadcn/ui を使用したフロントエンド開発のコーディング規約。

---

## ディレクトリ構成

### 全体構成

```
frontend/src/
├── app/                          # App Router（ページ & BFF）
│   ├── layout.tsx
│   ├── globals.css
│   │
│   ├── (dashboard)/              # ダッシュボード（ルートグループ）
│   │   ├── page.tsx
│   │   ├── _components/          # ページ専用コンポーネント
│   │   └── _hooks/               # ページ専用フック
│   │
│   ├── screener/
│   │   ├── page.tsx
│   │   ├── _components/
│   │   └── _hooks/
│   │
│   ├── stock/[symbol]/
│   │   ├── page.tsx
│   │   ├── _components/
│   │   └── _hooks/
│   │
│   ├── portfolio/
│   │   ├── page.tsx
│   │   ├── _components/
│   │   └── _hooks/
│   │
│   ├── admin/screener/
│   │   ├── page.tsx
│   │   ├── _components/
│   │   └── _hooks/
│   │
│   └── api/                      # BFF Route Handlers
│       └── ...
│
├── components/                   # 共通コンポーネントのみ
│   ├── layout/
│   │   └── Header.tsx
│   ├── charts/
│   │   └── PriceChart.tsx
│   └── ui/                       # shadcn/ui
│       ├── button.tsx
│       ├── card.tsx
│       └── ...
│
├── lib/                          # 共通ユーティリティ
│   ├── backend-fetch.ts
│   └── utils.ts
│
└── types/                        # 共通型定義
    ├── api.ts
    ├── market.ts
    ├── stock.ts
    └── portfolio.ts
```

### ディレクトリ命名規則

| ディレクトリ | プレフィックス | 説明 |
|-------------|---------------|------|
| `_components/` | `_` | ページ専用コンポーネント。Next.js がルーティングから除外 |
| `_hooks/` | `_` | ページ専用フック |
| `_lib/` | `_` | ページ専用ユーティリティ（必要な場合のみ） |
| `(groupName)/` | `()` | ルートグループ。URLに影響しない |

### ファイル命名規則

| 種別 | 命名規則 | 例 |
|-----|---------|-----|
| コンポーネント | PascalCase | `StockTable.tsx` |
| フック | camelCase（use prefix） | `useScreener.ts` |
| ユーティリティ | camelCase | `formatPrice.ts` |
| 型定義 | camelCase | `market.ts` |
| ページ | `page.tsx`（固定） | `app/screener/page.tsx` |

---

## コンポーネント配置ルール

### ページ専用 vs 共通

| 配置場所 | 条件 | 例 |
|---------|------|-----|
| `app/{page}/_components/` | そのページでのみ使用 | StockTable, FilterPanel |
| `components/` | 2つ以上のページで使用 | Header, PriceChart |
| `components/ui/` | shadcn/ui（汎用UI部品） | Button, Card, Badge |

### barrel file (index.ts) は使用しない

```
# Bad: index.ts を使った re-export
app/screener/_components/
├── StockTable.tsx
├── FilterPanel.tsx
└── index.ts          # ← 作成しない

# Good: 個別にインポート
app/screener/_components/
├── StockTable.tsx
└── FilterPanel.tsx
```

---

## インポートルール

### ページ専用コンポーネント・フック

**相対パスでインポート**

```typescript
// app/screener/page.tsx

// Good: 相対パス
import { StockTable } from "./_components/StockTable";
import { FilterPanel } from "./_components/FilterPanel";
import { useScreener } from "./_hooks/useScreener";

// Bad: エイリアスパス（ページ専用には使わない）
import { StockTable } from "@/app/screener/_components/StockTable";
```

### 共通コンポーネント・ユーティリティ

**エイリアスパス (`@/`) でインポート**

```typescript
// app/screener/page.tsx

// Good: エイリアスパス
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { PriceChart } from "@/components/charts/PriceChart";
import type { Stock } from "@/types/stock";

// Bad: 相対パス（共通には使わない）
import { Header } from "../../components/layout/Header";
```

### インポート順序

```typescript
// 1. React/Next.js
import { useState, useCallback } from "react";
import Link from "next/link";

// 2. 外部ライブラリ
import { RefreshCw, AlertCircle } from "lucide-react";

// 3. 共通コンポーネント（@/ エイリアス）
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";

// 4. 共通ユーティリティ・型（@/ エイリアス）
import { cn } from "@/lib/utils";
import type { Stock } from "@/types/stock";

// 5. ページ専用（相対パス）
import { StockTable } from "./_components/StockTable";
import { useScreener } from "./_hooks/useScreener";
```

---

## TypeScript

### 型定義

```typescript
// Good: 明示的な型定義
interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
}

// Good: 型を再利用
type StockList = Stock[];

// Bad: any の使用
const data: any = fetchData(); // 禁止
```

### Props の型定義

```typescript
// Good: interface で Props を定義
interface StockTableProps {
  stocks: Stock[];
  isLoading?: boolean;
  onSelect?: (symbol: string) => void;
}

export function StockTable({ stocks, isLoading, onSelect }: StockTableProps) {
  // ...
}
```

### 型定義の配置

| 配置場所 | 条件 |
|---------|------|
| `types/` | 複数ページで共有する型（API レスポンス等） |
| コンポーネントファイル内 | そのコンポーネントでのみ使用する Props 型 |
| `_hooks/` 内 | そのフックでのみ使用する型 |

---

## React / Next.js

### Client Components

```typescript
// app/screener/_components/FilterPanel.tsx
"use client";

import { useState } from "react";

interface FilterPanelProps {
  onFilterChange: (filter: ScreenerFilter) => void;
}

export function FilterPanel({ onFilterChange }: FilterPanelProps) {
  const [minRsRating, setMinRsRating] = useState(80);
  // ...
}
```

### カスタムフック

```typescript
// app/screener/_hooks/useScreener.ts
"use client";

import { useState, useCallback, useEffect } from "react";

export function useScreener() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStocks = useCallback(async () => {
    setIsLoading(true);
    // ...
  }, []);

  useEffect(() => {
    fetchStocks();
  }, [fetchStocks]);

  return { stocks, isLoading, error, refetch: fetchStocks };
}
```

---

## スタイリング (TailwindCSS)

### 基本方針

```tsx
// Good: クラス直書き
<div className="flex items-center gap-4 p-4 bg-card rounded-lg border">
  <span className="text-lg font-bold text-foreground">{stock.symbol}</span>
</div>

// Bad: @apply の多用
```

### 条件付きスタイル

```tsx
import { cn } from "@/lib/utils";

// Good: cn() ユーティリティを使用
<span className={cn(
  "text-sm font-medium",
  change >= 0 ? "text-green-600" : "text-red-600"
)}>
  {change}%
</span>
```

---

## shadcn/ui

### コンポーネントの追加

```bash
npx shadcn@latest add card button badge
```

### 使用方法

```tsx
// 共通コンポーネントからインポート
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
```

### カスタマイズ方針

| 種類 | 方針 |
|------|------|
| `ui/` 内のファイル | 基本的に編集しない |
| スタイル調整 | `globals.css` の CSS変数で調整 |
| 機能拡張 | 新しいコンポーネントを作成し `ui/` を組み合わせる |

---

## BFF (Backend For Frontend)

### Route Handler の配置

```
app/api/
├── market/
│   ├── status/route.ts
│   └── indicators/route.ts
├── screener/
│   ├── canslim/route.ts
│   └── stock/[symbol]/route.ts
├── watchlist/
│   ├── route.ts
│   └── [symbol]/route.ts
└── admin/
    └── screener/
        └── refresh/
            ├── route.ts
            └── [jobId]/route.ts
```

### backend-fetch の使用

```typescript
// app/api/screener/canslim/route.ts
import { backendGet } from "@/lib/backend-fetch";

export async function GET() {
  const result = await backendGet<ApiResponse<ScreenerResult>>(
    "/screener/canslim"
  );
  // ...
}
```

---

## エラーハンドリング

### コンポーネント内

```tsx
export function StockList() {
  const { stocks, isLoading, error, refetch } = useStocks();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return (
      <div className="p-4 bg-destructive/10 rounded-lg">
        <p className="text-destructive">{error}</p>
        <Button onClick={refetch}>再試行</Button>
      </div>
    );
  }

  if (!stocks.length) {
    return <div>データがありません</div>;
  }

  return (
    <ul>
      {stocks.map((stock) => (
        <StockCard key={stock.symbol} stock={stock} />
      ))}
    </ul>
  );
}
```

---

## ページ実装例

```typescript
// app/screener/page.tsx
"use client";

import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";

import { StockTable } from "./_components/StockTable";
import { FilterPanel } from "./_components/FilterPanel";
import { useScreener } from "./_hooks/useScreener";

export default function ScreenerPage() {
  const { stocks, isLoading, error, filter, setFilter, refetch } = useScreener();

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="mx-auto max-w-7xl px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold">CAN-SLIM スクリーナー</h1>
          <Button variant="outline" onClick={refetch} disabled={isLoading}>
            <RefreshCw className={isLoading ? "animate-spin" : ""} />
            更新
          </Button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-destructive/10 rounded-lg">
            <p className="text-destructive">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1">
            <FilterPanel filter={filter} onFilterChange={setFilter} />
          </div>
          <div className="lg:col-span-3">
            <StockTable stocks={stocks} isLoading={isLoading} />
          </div>
        </div>
      </main>
    </div>
  );
}
```

---

## 関連ドキュメント

- `docs/poc/architectures/frontend-architecture.md` - フロントエンドアーキテクチャ
- `docs/poc/architectures/directory-structure.md` - ディレクトリ構成
- `docs/poc/coding-standard/tech-stack.md` - 技術スタック
