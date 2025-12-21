# Frontend API リファクタリング計画

## 概要

現在のフロントエンドAPI呼び出しを、Next.js App Router の Route Handlers (BFFパターン) に変更する。

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

| ファイル | 説明 |
|---------|------|
| `frontend/src/app/api/market/status/route.ts` | マーケットステータスAPI |
| `frontend/src/app/api/market/indices/route.ts` | インデックスAPI |
| `frontend/src/app/api/market/quote/[symbol]/route.ts` | 株価取得API |
| `frontend/src/app/api/market/chart/[symbol]/route.ts` | チャートデータAPI |
| `frontend/src/app/api/watchlist/route.ts` | Watchlist CRUD |
| `frontend/src/app/api/watchlist/[symbol]/route.ts` | Watchlist個別操作 |
| `frontend/src/app/api/trades/route.ts` | Trade一覧・新規作成 |
| `frontend/src/app/api/trades/[id]/route.ts` | Trade個別操作 |
| `frontend/src/app/api/trades/[id]/close/route.ts` | Trade決済 |
| `frontend/src/app/api/trades/[id]/cancel/route.ts` | Tradeキャンセル |
| `frontend/src/app/api/performance/route.ts` | パフォーマンス取得 |
| `frontend/src/app/api/screener/run/route.ts` | スクリーナー実行 |
| `frontend/src/app/api/screener/templates/route.ts` | テンプレート取得 |
| `frontend/src/app/api/admin/[...path]/route.ts` | 管理API（プロキシ） |

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

### Phase 1: 基盤整備
1. 環境変数の設定変更
2. 共通ユーティリティ関数の作成（`lib/backend-fetch.ts`）

### Phase 2: Market API
1. `/api/market/status`
2. `/api/market/indices`
3. `/api/market/quote/[symbol]`
4. `/api/market/chart/[symbol]`

### Phase 3: Portfolio API
1. `/api/watchlist`
2. `/api/watchlist/[symbol]`
3. `/api/trades`
4. `/api/trades/[id]`
5. `/api/trades/[id]/close`
6. `/api/trades/[id]/cancel`
7. `/api/performance`

### Phase 4: Screener API
1. `/api/screener/run`
2. `/api/screener/templates`

### Phase 5: Admin API
1. `/api/admin/[...path]` (Catch-all route)

### Phase 6: クリーンアップ
1. `lib/api.ts` の修正
2. 不要な環境変数の削除
3. CORS設定の削除（バックエンド側）

---

## キャッシュ戦略

| エンドポイント | 戦略 | 理由 |
|--------------|------|------|
| `/api/market/status` | `revalidate: 60` | 市場ステータスは頻繁に変わらない |
| `/api/market/indices` | `revalidate: 30` | インデックスは定期更新 |
| `/api/market/quote/*` | `revalidate: 0` (no-store) | リアルタイム性が必要 |
| `/api/watchlist` | `revalidate: 0` | ユーザー固有データ |
| `/api/trades` | `revalidate: 0` | ユーザー固有データ |
| `/api/performance` | `revalidate: 0` | ユーザー固有データ |

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
