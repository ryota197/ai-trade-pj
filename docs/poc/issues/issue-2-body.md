## 概要

個別銘柄詳細ページ（`/stock/[symbol]`）でCAN-SLIMスコアが表示されない。

## 現状

```tsx
// frontend/src/app/stock/[symbol]/page.tsx (122行目)
<CANSLIMScoreCard score={null} isLoading={isLoading} />
```

常に `score={null}` を渡しているため、「スコアデータがありません」と表示される。

## 原因

`useStockData` hookは以下のデータのみ取得している：
- `quote` - 株価クォート（`/api/data/quote/{symbol}`）
- `priceHistory` - 価格履歴（`/api/data/history/{symbol}`）
- `financials` - 財務指標（`/api/data/financials/{symbol}`）

CAN-SLIMスコアは `/api/screener/stock/{symbol}` から取得する必要があるが、呼び出していない。

## 対策

### 案1: useStockData を拡張

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

### 案2: 専用hook を作成

```tsx
// frontend/src/hooks/useStockDetail.ts
export function useStockDetail(symbol: string) {
  // /api/screener/stock/{symbol} を呼び出してStockDetailを取得
}
```

## 関連ドキュメント

- `docs/poc/plan/implementation-status.md` PENDING-002
- `docs/poc/plan/phase3-screener.md` 3.6節

## 工数

中（1時間程度）
