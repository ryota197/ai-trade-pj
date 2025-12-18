# 技術スタック

## 概要

本プロジェクトで使用する技術スタックとバージョンを定義する。

---

## 一覧

| レイヤー | 技術 | バージョン | 用途 |
|---------|------|-----------|------|
| **Frontend** | Next.js | 16.x | Reactフレームワーク |
| | React | 19.x | UIライブラリ |
| | TypeScript | 5.x | 型安全な開発 |
| | TailwindCSS | 4.x | スタイリング |
| | shadcn/ui | latest | UIコンポーネント |
| | TanStack Query | 5.x | データフェッチ・キャッシュ |
| | Lightweight Charts | 4.x | 金融チャート描画 |
| **Backend** | Python | 3.11+ | サーバーサイド言語 |
| | FastAPI | 0.109+ | Webフレームワーク |
| | SQLAlchemy | 2.x | ORM |
| | Pydantic | 2.x | バリデーション・シリアライズ |
| | yfinance | 0.2.x | 株価データ取得 |
| **Database** | PostgreSQL | 16 | RDB |
| **Infrastructure** | Docker | 24.x | コンテナ |
| | Docker Compose | 2.x | ローカル環境構築 |

---

## Frontend 詳細

### Next.js 14

- **App Router** を使用（Pages Router は使わない）
- **Server Components** を基本とし、必要な箇所のみ Client Components
- API通信は TanStack Query 経由

### TypeScript

- **strict mode** を有効化
- `any` 型の使用は禁止
- 型定義は `src/types/` に集約

### TailwindCSS 4

- カスタムテーマは最小限に
- `@apply` の使用は避け、クラス直書きを基本とする

### shadcn/ui

- **コピー&ペースト方式** のコンポーネントライブラリ
- Radix UI + TailwindCSS ベース
- カスタマイズ性が高い（コンポーネントは `components/ui/` に配置）
- 必要なコンポーネントのみ追加（`npx shadcn@latest add <component>`）

**使用するコンポーネント例**:
- Card, Button, Badge（基本UI）
- Table, Dialog（データ表示）
- Select, Input（フォーム）

### TanStack Query (React Query)

- サーバー状態管理に使用
- クライアント状態は React の useState / useReducer で管理
- キャッシュ時間はデータ特性に応じて設定

### Lightweight Charts

- TradingView 製の軽量チャートライブラリ
- 金融データの可視化に最適化
- Recharts より高速、金融特化

---

## Backend 詳細

### Python 3.11+

- 型ヒントを必須とする
- f-string を使用（format() は使わない）
- パッケージ管理は `uv` または `pip` + `requirements.txt`

### FastAPI

- 非同期処理（async/await）を積極的に使用
- 依存性注入（Depends）でサービスを注入
- OpenAPI ドキュメント自動生成を活用

### SQLAlchemy 2.x

- **2.0 スタイル** を使用（1.x スタイルは使わない）
- Mapped 型アノテーションを使用
- セッション管理は依存性注入で行う

### Pydantic 2.x

- リクエスト/レスポンスのバリデーション
- 設定管理（BaseSettings）
- **2.x** の新しい記法を使用

### yfinance

- 株価データ取得のメインソース
- レート制限に注意（過度なリクエストを避ける）
- データはキャッシュして再利用

---

## Database 詳細

### PostgreSQL 16

- JSONBカラムは必要最小限に（正規化優先）
- インデックスは設計時に検討
- DECIMAL型で金額を扱う（浮動小数点は使わない）

---

## 開発ツール

### 共通

| ツール | 用途 |
|-------|------|
| Git | バージョン管理 |
| Docker Desktop | コンテナ実行環境 |
| VS Code | エディタ（推奨） |

### Frontend

| ツール | 用途 |
|-------|------|
| ESLint | Linter |
| Prettier | Formatter |
| npm / pnpm | パッケージ管理 |

### Backend

| ツール | 用途 |
|-------|------|
| Ruff | Linter + Formatter |
| pytest | テストフレームワーク |
| uv / pip | パッケージ管理 |

---

## バージョン固定方針

### Frontend

`package.json` でバージョンを固定：
```json
{
  "dependencies": {
    "next": "14.2.x",
    "@tanstack/react-query": "5.x"
  }
}
```

### Backend

`requirements.txt` でバージョンを固定：
```
fastapi>=0.109.0,<0.120.0
sqlalchemy>=2.0.0,<3.0.0
pydantic>=2.0.0,<3.0.0
```

---

## アップグレード方針

- セキュリティパッチは速やかに適用
- メジャーバージョンアップは慎重に検討
- 依存関係の更新は定期的に確認（月1回程度）
