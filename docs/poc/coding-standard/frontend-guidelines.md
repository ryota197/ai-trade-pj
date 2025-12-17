# Frontend コーディング規約

## 概要

Next.js 14 + TypeScript + TailwindCSS を使用したフロントエンド開発のコーディング規約。

---

## プロジェクト構成

### ディレクトリ構成

```
src/
├── app/           # App Router（ページ）
├── components/    # コンポーネント
├── hooks/         # カスタムフック
├── lib/           # ユーティリティ
└── types/         # 型定義
```

### ファイル命名規則

| 種別 | 命名規則 | 例 |
|-----|---------|-----|
| コンポーネント | PascalCase | `StockCard.tsx` |
| フック | camelCase（use prefix） | `useStockData.ts` |
| ユーティリティ | camelCase | `formatPrice.ts` |
| 型定義 | camelCase | `market.ts` |
| ページ | `page.tsx`（固定） | `app/screener/page.tsx` |

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
interface StockCardProps {
  stock: Stock;
  onSelect?: (symbol: string) => void;
}

export function StockCard({ stock, onSelect }: StockCardProps) {
  // ...
}
```

### 型のエクスポート

```typescript
// types/market.ts
export interface MarketStatus {
  status: 'risk_on' | 'risk_off' | 'neutral';
  confidence: number;
  indicators: MarketIndicators;
}

// types/index.ts（re-export）
export * from './market';
export * from './stock';
```

---

## React / Next.js

### コンポーネント

#### Server Components（デフォルト）

```typescript
// app/screener/page.tsx
// Server Component（デフォルト）
export default async function ScreenerPage() {
  const stocks = await fetchStocks();

  return (
    <div>
      <h1>Screener</h1>
      <StockTable stocks={stocks} />
    </div>
  );
}
```

#### Client Components（必要な場合のみ）

```typescript
// components/screener/FilterPanel.tsx
'use client';

import { useState } from 'react';

export function FilterPanel() {
  const [minRsRating, setMinRsRating] = useState(80);

  return (
    // インタラクティブなUI
  );
}
```

### フック

```typescript
// hooks/useStockData.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useStockData(symbol: string) {
  return useQuery({
    queryKey: ['stock', symbol],
    queryFn: () => api.getStock(symbol),
    staleTime: 60 * 1000, // 1分
  });
}
```

### 状態管理

```typescript
// サーバー状態: TanStack Query
const { data, isLoading } = useStockData('AAPL');

// クライアント状態: useState
const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);

// フォーム状態: useState or React Hook Form
const [filters, setFilters] = useState<ScreenerFilters>(defaultFilters);
```

---

## スタイリング (TailwindCSS)

### 基本方針

```tsx
// Good: クラス直書き
<div className="flex items-center gap-4 p-4 bg-white rounded-lg shadow">
  <span className="text-lg font-bold text-gray-900">{stock.symbol}</span>
</div>

// Bad: @apply の多用（避ける）
// styles.css
// .stock-card { @apply flex items-center gap-4 p-4 bg-white rounded-lg shadow; }
```

### 条件付きスタイル

```tsx
import { cn } from '@/lib/utils';

// Good: cn() ユーティリティを使用
<span className={cn(
  "text-sm font-medium",
  change >= 0 ? "text-green-600" : "text-red-600"
)}>
  {change}%
</span>
```

### レスポンシブ

```tsx
// モバイルファースト
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* ... */}
</div>
```

---

## API通信

### APIクライアント

```typescript
// lib/api.ts
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: { code: string; message: string } | null;
}

async function fetchApi<T>(endpoint: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${endpoint}`);
  const json: ApiResponse<T> = await res.json();

  if (!json.success) {
    throw new Error(json.error?.message || 'API Error');
  }

  return json.data as T;
}

export const api = {
  getMarketStatus: () => fetchApi<MarketStatus>('/market/status'),
  getStocks: (params?: ScreenerParams) =>
    fetchApi<ScreenerResult>(`/screener/canslim?${new URLSearchParams(params)}`),
  getStock: (symbol: string) => fetchApi<Stock>(`/data/quote/${symbol}`),
};
```

### TanStack Query の使用

```typescript
// hooks/useMarketStatus.ts
export function useMarketStatus() {
  return useQuery({
    queryKey: ['market', 'status'],
    queryFn: api.getMarketStatus,
    refetchInterval: 60 * 1000, // 1分ごとに更新
  });
}
```

---

## エラーハンドリング

### コンポーネント内

```tsx
export function StockList() {
  const { data, isLoading, error } = useStocks();

  if (isLoading) return <Loading />;
  if (error) return <ErrorMessage message={error.message} />;
  if (!data?.stocks.length) return <EmptyState />;

  return (
    <ul>
      {data.stocks.map((stock) => (
        <StockCard key={stock.symbol} stock={stock} />
      ))}
    </ul>
  );
}
```

### Error Boundary

```tsx
// app/error.tsx
'use client';

export default function Error({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div className="p-4">
      <h2>Something went wrong</h2>
      <p>{error.message}</p>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

---

## テスト

### コンポーネントテスト

```typescript
// __tests__/StockCard.test.tsx
import { render, screen } from '@testing-library/react';
import { StockCard } from '@/components/screener/StockCard';

describe('StockCard', () => {
  it('displays stock symbol and price', () => {
    const stock = { symbol: 'AAPL', name: 'Apple', price: 185.5 };

    render(<StockCard stock={stock} />);

    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('$185.50')).toBeInTheDocument();
  });
});
```

---

## パフォーマンス

### 画像最適化

```tsx
import Image from 'next/image';

// Good: next/image を使用
<Image
  src="/logo.png"
  alt="Logo"
  width={100}
  height={100}
  priority // Above the fold
/>
```

### メモ化

```tsx
// 必要な場合のみ useMemo / useCallback
const sortedStocks = useMemo(
  () => stocks.sort((a, b) => b.rsRating - a.rsRating),
  [stocks]
);
```

### 遅延ロード

```tsx
import dynamic from 'next/dynamic';

// 重いコンポーネントを遅延ロード
const PriceChart = dynamic(
  () => import('@/components/charts/PriceChart'),
  { loading: () => <Loading /> }
);
```
