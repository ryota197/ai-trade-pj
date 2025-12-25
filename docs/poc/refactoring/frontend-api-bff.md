# Frontend API リファクタリング計画

## 概要

現在のフロントエンドAPI呼び出しを、Next.js App Router の Route Handlers (BFFパターン) に変更する。

---

## 進捗状況

| Phase | 内容 | 状態 |
|-------|------|------|
| Phase 1 | 基盤整備 | ✅ 完了 |
| Phase 2 | Market API | ✅ 完了 |
| Phase 3 | Portfolio API | ✅ 完了 |
| Phase 4 | Screener & Data API | ✅ 完了 |
| Phase 5 | クリーンアップ | ✅ 完了 |
| Phase 6 | lib/api.ts 削除 | 🔜 未着手 |

---

## 現在のアーキテクチャ

```
┌─────────────┐         ┌─────────────┐
│   Browser   │ ──────► │   FastAPI   │
│  (React)    │  fetch  │  Backend    │
└─────────────┘         └─────────────┘
```

**問題点:**
- バックエンドURL (`localhost:8000`) がクライアントに露出
- CORS設定が必要
- サーバーサイドでのデータ加工ができない
- Next.js のキャッシュ機能を活用できない

---

## 目標アーキテクチャ

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Browser   │ ──────► │  Next.js    │ ──────► │   FastAPI   │
│  (React)    │  fetch  │  API Routes │  fetch  │  Backend    │
└─────────────┘         └─────────────┘         └─────────────┘
                         (BFF Layer)
```

**メリット:**
- バックエンドURLの隠蔽（環境変数で管理）
- CORS不要（同一オリジン）
- サーバーサイドでのデータ変換・集約が可能
- Next.js のキャッシュ/再検証機能を活用可能
- エラーハンドリングの統一

---

## 対象ファイル

### 変更対象

| ファイル | 変更内容 |
|---------|---------|
| `frontend/src/lib/api.ts` | バックエンドURL → `/api/*` に変更 |
| `frontend/.env.local` | `NEXT_PUBLIC_API_URL` 削除、`BACKEND_URL` 追加 |

### 新規作成

| ファイル | 説明 | 状態 |
|---------|------|------|
| `frontend/src/app/api/market/status/route.ts` | マーケットステータスAPI | ✅ |
| `frontend/src/app/api/market/indicators/route.ts` | マーケット指標API | ✅ |
| `frontend/src/app/api/market/quote/[symbol]/route.ts` | 株価取得API | ✅ |
| `frontend/src/app/api/market/chart/[symbol]/route.ts` | チャートデータAPI | ✅ |
| `frontend/src/app/api/watchlist/route.ts` | Watchlist CRUD | ✅ |
| `frontend/src/app/api/watchlist/[symbol]/route.ts` | Watchlist個別操作 | ✅ |
| `frontend/src/app/api/trades/route.ts` | Trade一覧・新規作成 | ✅ |
| `frontend/src/app/api/trades/[id]/route.ts` | Trade個別操作 | ✅ |
| `frontend/src/app/api/trades/[id]/close/route.ts` | Trade決済 | ✅ |
| `frontend/src/app/api/trades/[id]/cancel/route.ts` | Tradeキャンセル | ✅ |
| `frontend/src/app/api/performance/route.ts` | パフォーマンス取得 | ✅ |
| `frontend/src/app/api/screener/canslim/route.ts` | CAN-SLIMスクリーニング | ✅ |
| `frontend/src/app/api/screener/stock/[symbol]/route.ts` | 銘柄詳細取得 | ✅ |
| `frontend/src/app/api/data/history/[symbol]/route.ts` | 株価履歴取得 | ✅ |
| `frontend/src/app/api/data/financials/[symbol]/route.ts` | 財務指標取得 | ✅ |
| `frontend/src/app/api/data/quote/[symbol]/route.ts` | 株価クォート取得 | ✅ |

---

## 実装詳細

### 1. 環境変数

```env
# frontend/.env.local
BACKEND_URL=http://localhost:8000
```

※ `NEXT_PUBLIC_` プレフィックスを外し、サーバーサイドのみで使用

### 2. Route Handler 基本パターン

```typescript
// frontend/src/app/api/market/status/route.ts
import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/market/status`, {
      headers: {
        "Content-Type": "application/json",
      },
      // キャッシュ設定（必要に応じて）
      next: { revalidate: 60 }, // 60秒キャッシュ
    });

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: { code: "BACKEND_ERROR", message: "Backend request failed" } },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { success: false, error: { code: "INTERNAL_ERROR", message: "Internal server error" } },
      { status: 500 }
    );
  }
}
```

### 3. 動的ルート パターン

```typescript
// frontend/src/app/api/market/quote/[symbol]/route.ts
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: { symbol: string } }
) {
  const { symbol } = params;

  try {
    const response = await fetch(`${BACKEND_URL}/api/market/quote/${symbol}`);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { success: false, error: { code: "INTERNAL_ERROR", message: "Internal server error" } },
      { status: 500 }
    );
  }
}
```

### 4. POST/PUT/DELETE パターン

```typescript
// frontend/src/app/api/trades/route.ts
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET() {
  const response = await fetch(`${BACKEND_URL}/api/trades`);
  const data = await response.json();
  return NextResponse.json(data);
}

export async function POST(request: NextRequest) {
  const body = await request.json();

  const response = await fetch(`${BACKEND_URL}/api/trades`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}
```

### 5. lib/api.ts の変更

```typescript
// 変更前
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// 変更後
const API_BASE = "/api";  // Next.js API Routes を使用
```

---

## 実装順序

### Phase 1: 基盤整備 ✅ 完了
1. 環境変数の設定変更（`.env.local`, `.env.example`）
2. 共通ユーティリティ関数の作成（`lib/backend-fetch.ts`）

### Phase 2: Market API ✅ 完了
1. `/api/market/status`
2. `/api/market/indicators`
3. `/api/market/quote/[symbol]`
4. `/api/market/chart/[symbol]`

### Phase 3: Portfolio API ✅ 完了
1. `/api/watchlist`
2. `/api/watchlist/[symbol]`
3. `/api/trades`
4. `/api/trades/[id]`
5. `/api/trades/[id]/close`
6. `/api/trades/[id]/cancel`
7. `/api/performance`

### Phase 4: Screener & Data API ✅ 完了
1. `/api/screener/canslim`
2. `/api/screener/stock/[symbol]`
3. `/api/data/history/[symbol]`
4. `/api/data/financials/[symbol]`
5. `/api/data/quote/[symbol]`

### Phase 5: クリーンアップ ✅ 完了
1. `lib/api.ts` の修正（エンドポイントを `/api/*` に変更）
2. `useWatchlist.ts` の修正（API引数変更に対応）
3. 環境変数の整理（`.env.example` 更新）

**変更内容:**
- `API_BASE_URL` を `"/api"` に変更（BFF経由）
- 旧 `NEXT_PUBLIC_API_URL` は不要に
- ヘルスチェックのみ直接バックエンド呼び出し（開発用）

### Phase 6: lib/api.ts 削除 🔜 未着手

BFFパターン導入により `lib/api.ts` が冗長になったため削除する。

**現在の構成（冗長）:**
```
Component → lib/api.ts → Route Handlers → Backend
```

**目標の構成（シンプル）:**
```
Component/Hook → Route Handlers → Backend
```

**作業内容:**
1. 各hooks（`useWatchlist.ts`, `useTrades.ts`, `usePerformance.ts`）で直接 `fetch('/api/*')` を呼び出すよう修正
2. 各ページ/コンポーネントで直接 `fetch('/api/*')` を呼び出すよう修正
3. `lib/api.ts` を削除

**削除理由:**
- Route Handlersで型安全性・エラーハンドリングは確保済み
- 中間層が不要になり、コードがシンプルになる
- 認証が必要になった場合はRoute Handler側で対応可能

**影響範囲:**
- `src/hooks/useWatchlist.ts`
- `src/hooks/useTrades.ts`
- `src/hooks/usePerformance.ts`
- `src/components/` 配下でAPIを呼び出しているコンポーネント
- `src/app/` 配下でAPIを呼び出しているページ

### ~~Admin API~~ ❌ 不要（当初計画から削除）

**当初の計画:**
- `/api/admin/[...path]` (Catch-all route) を作成
- 管理者向けAPI（データ更新、キャッシュクリア、システム設定等）をプロキシ

**不要と判断した理由:**
- 現時点でバックエンドにAdmin APIエンドポイントが存在しない
- フロントエンドからAdmin機能を呼び出す実装がない
- 将来的に必要になった場合は、その時点で実装する

---

## キャッシュ戦略

| エンドポイント | 戦略 | 理由 |
|--------------|------|------|
| `/api/market/status` | `revalidate: 60` | 市場ステータスは頻繁に変わらない |
| `/api/market/indicators` | `revalidate: 30` | インデックスは定期更新 |
| `/api/market/quote/*` | `revalidate: 0` | リアルタイム性が必要 |
| `/api/market/chart/*` | `revalidate: 60` | チャートデータはある程度キャッシュ可能 |
| `/api/watchlist` | `revalidate: 0` | ユーザー固有データ |
| `/api/trades` | `revalidate: 0` | ユーザー固有データ |
| `/api/performance` | `revalidate: 0` | ユーザー固有データ |
| `/api/screener/canslim` | `revalidate: 0` | 最新データが必要 |
| `/api/screener/stock/*` | `revalidate: 0` | 最新データが必要 |
| `/api/data/history/*` | `revalidate: 60` | 履歴データはキャッシュ可能 |
| `/api/data/financials/*` | `revalidate: 300` | 財務データは5分キャッシュ |
| `/api/data/quote/*` | `revalidate: 0` | リアルタイム性が必要 |

---

## 注意事項

1. **認証が必要な場合**: 将来的にJWT等を導入する場合、Route Handlers でトークンを検証してからバックエンドに転送する
2. **エラーハンドリング**: バックエンドのエラーレスポンスをそのまま返すか、加工するか統一する
3. **タイムアウト**: fetch にタイムアウト設定を追加することを検討
4. **ロギング**: サーバーサイドでのリクエストログを追加

---

## 関連ドキュメント

- [API設計](../architectures/api-design.md)
- [ディレクトリ構造](../architectures/directory-structure.md)
