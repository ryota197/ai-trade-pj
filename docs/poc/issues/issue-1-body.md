## 概要

PortfolioページにHeaderコンポーネントがなく、ナビゲーション体験が他のページと不整合になっている。

## 現状

| ページ | Header |
|--------|--------|
| `/` (ホーム) | ✅ あり |
| `/screener` | ✅ あり |
| `/stock/*` | ✅ あり |
| `/portfolio` | ❌ なし |

## 影響

- ホームに戻るリンクがない
- ナビゲーション体験の不整合

## 対策

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

## 関連ドキュメント

- `docs/poc/plan/implementation-status.md` PENDING-004
- `docs/poc/architecture-review.md` ISSUE-010

## 工数

小（10分程度）
