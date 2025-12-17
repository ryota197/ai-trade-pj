# Claude Skills - AI Trade App

このファイルはClaude Codeがプロジェクトで従うルールを定義します。

---

## ドキュメント作成ルール

### 学習ドキュメント（docs/learnings/）

- **ユーザーの明示的な指示があった場合のみ** 追加する
- 自動的に追加しない
- フォーマット: Markdown
- 命名規則: `{技術名}-{トピック}.md`（例: `python-lru-cache.md`）

---

## プロジェクト構成

### バックエンド（backend/）

- **クリーンアーキテクチャ**を採用
- 4層構造: Domain → Application → Infrastructure → Presentation
- Python 3.11+ / FastAPI / SQLAlchemy 2.x

### フロントエンド（frontend/）

- Next.js 14 / TypeScript / TailwindCSS
- App Router使用

### データベース

- PostgreSQL 16（Docker）
- スキーマ定義: `backend/src/infrastructure/database/init.sql`

---

## コーディング規約

- 型ヒント必須（Python）
- TypeScript strict mode（Frontend）
- 詳細: `docs/poc/coding-standard/`

---

## 開発フェーズ

現在: **Phase 1 - 基盤構築**

詳細: `docs/poc/plan/plan-overview.md`
