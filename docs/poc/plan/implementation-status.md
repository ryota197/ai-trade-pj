# 実装状況レポート

## 概要

2024年12月実施の実装状況調査結果。
`docs/poc/plan/` 配下の実装計画と実際のソースコードを比較し、積み残しを特定した。

---

## 全体サマリー

| Phase | 名称 | 状態 | 積み残し |
|-------|------|------|----------|
| Phase 1 | 基盤構築 | ✅ 完了 | なし |
| Phase 2 | Market Module | ⚠️ 一部残 | バッチ処理（将来対応） |
| Phase 3 | Screener Module | ⚠️ 一部残 | 詳細ページCAN-SLIMスコア、管理者機能 |
| Phase 4 | Portfolio Module | ⚠️ 一部残 | Headerなし |

---

## Phase 1: Foundation ✅

すべて実装済み。

| タスク | 状態 |
|--------|------|
| 1.1 Docker + PostgreSQL環境構築 | ✅ |
| 1.2 Backend基本構成（FastAPI） | ✅ |
| 1.3 Frontend基本構成（Next.js） | ✅ |
| 1.4 Data Service実装（yfinance連携） | ✅ |

---

## Phase 2: Market Module ⚠️

### 実装済み

| タスク | 状態 |
|--------|------|
| 2.1 Domain層実装 | ✅ |
| 2.2 Application層実装 | ✅ |
| 2.3 Infrastructure層実装 | ✅ |
| 2.4 Presentation層実装 | ✅ |
| 2.5 Frontend - shadcn/ui セットアップ | ✅ |
| 2.6 Frontend - コンポーネントリファクタリング | ✅ |
| 2.7 Frontend - ダッシュボードUI | ✅ |

### 積み残し

#### PENDING-001: バッチ処理によるスナップショット保存

| 項目 | 内容 |
|------|------|
| 計画箇所 | phase2-market.md「将来対応（バックログ）」 |
| 説明 | 1時間ごとのcronジョブでMarket状態をDBに保存 |
| 用途 | 履歴分析・トレンド把握 |
| 優先度 | 低（PoC範囲外） |
| 状態 | 🟡 未着手（将来対応として明記済み） |

**補足**: `market_snapshots` テーブル・モデルは定義済み。保存ロジックと定期実行の仕組みが未実装。

---

## Phase 3: Screener Module ⚠️

### 実装済み

| タスク | 状態 |
|--------|------|
| 3.1 Domain層実装 | ✅ |
| 3.2 Application層実装 | ✅ |
| 3.3 Infrastructure層実装 | ✅ |
| 3.4 Presentation層実装 | ✅ |
| 3.5 Frontend - スクリーナーUI | ✅ |
| 3.6 Frontend - 個別銘柄詳細ページ | ⚠️ 一部 |

### 積み残し

#### PENDING-002: 個別銘柄ページでCAN-SLIMスコアが表示されない

| 項目 | 内容 |
|------|------|
| 計画箇所 | phase3-screener.md 3.6節 |
| 場所 | `frontend/src/app/stock/[symbol]/page.tsx` |
| 問題 | `<CANSLIMScoreCard score={null} />` で常にnullを渡している |
| 原因 | `useStockData` hookがCAN-SLIMスコアを取得していない |
| 優先度 | 高（機能不全） |
| 状態 | 🔴 未対応 |

**対策案**:
1. `useStockData` を拡張して `/api/screener/stock/{symbol}` からCAN-SLIMスコアも取得
2. または専用hook `useStockDetail` を作成

```typescript
// 現状
const { quote, priceHistory, financials } = useStockData(symbol);
<CANSLIMScoreCard score={null} />

// 修正後
const { quote, priceHistory, financials, canslimScore } = useStockData(symbol);
<CANSLIMScoreCard score={canslimScore} />
```

---

#### PENDING-003: 管理者向けデータ更新機能

| 項目 | 内容 |
|------|------|
| 計画箇所 | phase3-admin-refresh.md |
| 説明 | スクリーニングデータを手動で更新するAPI・UI |
| 優先度 | 中（PoC段階では任意） |
| 状態 | 🟡 未着手 |

**未実装項目**:

| 機能 | エンドポイント | 優先度 |
|------|---------------|--------|
| 更新開始 | POST `/api/admin/screener/refresh` | P1 |
| 進捗確認 | GET `/api/admin/screener/refresh/{job_id}/status` | P2 |
| キャンセル | DELETE `/api/admin/screener/refresh/{job_id}` | P3 |
| 管理画面 | `/admin/screener` ページ | P2 |

**補足**: PoC段階では「あれば便利」レベル。将来的に定期実行（Cron）への拡張を想定。

---

## Phase 4: Portfolio Module ⚠️

### 実装済み

| タスク | 状態 |
|--------|------|
| 4.1 Domain層実装 | ✅ |
| 4.2 Application層実装 | ✅ |
| 4.3 Infrastructure層実装 | ✅ |
| 4.4 Presentation層実装 | ✅ |
| 4.5 Frontend - ポートフォリオUI | ⚠️ 一部 |

### 積み残し

#### PENDING-004: PortfolioページにHeaderがない

| 項目 | 内容 |
|------|------|
| 計画箇所 | phase4-portfolio.md 4.5節（暗黙的） |
| 場所 | `frontend/src/app/portfolio/page.tsx` |
| 問題 | 他のページ（`/`, `/screener`, `/stock/*`）にはHeaderがあるが、Portfolioにはない |
| 影響 | ナビゲーション体験の不整合。ホームに戻るリンクがない |
| 優先度 | 高（UX問題） |
| 状態 | 🔴 未対応 |

**対策**:
```tsx
// frontend/src/app/portfolio/page.tsx に追加
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

**関連**: architecture-review.md ISSUE-010

---

## 優先度別対応リスト

### 高優先度（機能・UXに直接影響）

| ID | 内容 | 工数 |
|----|------|------|
| PENDING-004 | PortfolioページにHeader追加 | 小 |
| PENDING-002 | 個別銘柄ページでCAN-SLIMスコア取得・表示 | 中 |

### 中優先度（将来対応・任意）

| ID | 内容 | 工数 |
|----|------|------|
| PENDING-003 | 管理者向けデータ更新機能 | 大 |
| PENDING-001 | Marketスナップショットバッチ処理 | 中 |

---

## 推奨対応順序

```
1. PENDING-004: PortfolioページにHeader追加（10分）
   ↓
2. PENDING-002: 個別銘柄ページCAN-SLIMスコア表示（1時間）
   ↓
3. (任意) PENDING-003: 管理者機能（1日）
   ↓
4. (任意) PENDING-001: バッチ処理（半日）
```

---

## 関連ドキュメント

- [../issues/pending-issues.md](../issues/pending-issues.md) - 積み残しIssue一覧
- [plan-overview.md](./plan-overview.md) - 全体計画
- [phase1-foundation.md](./phase1-foundation.md) - Phase 1 詳細
- [phase2-market.md](./phase2-market.md) - Phase 2 詳細
- [phase3-screener.md](./phase3-screener.md) - Phase 3 詳細
- [phase3-admin-refresh.md](./phase3-admin-refresh.md) - 管理者機能詳細
- [phase4-portfolio.md](./phase4-portfolio.md) - Phase 4 詳細
- [../architecture-review.md](../architecture-review.md) - アーキテクチャレビュー結果
