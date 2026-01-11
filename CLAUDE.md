# Claude Skills - AI Trade App

このファイルは Claude Code がプロジェクトで従うルールを定義します。

---

## プロジェクト概要

CAN-SLIM 投資手法に基づく株式スクリーニングアプリケーション（PoC）

-   S&P 500 銘柄を対象に CAN-SLIM スコアを算出
-   RS Rating（相対強度）によるランキング
-   管理画面からスクリーニングデータの更新・確認

---

## ドキュメント作成ルール

### 学習ドキュメント

-   **保存先**: Obsidian `00_Development_Notes/ai-trade-pj/learnings/`
-   **ユーザーの明示的な指示があった場合のみ** 追加する
-   自動的に追加しない
-   フォーマット: Markdown
-   命名規則: `{技術名}-{トピック}.md`（例: `python-lru-cache.md`）

---

## プロジェクト構成

### バックエンド（backend/）

-   **クリーンアーキテクチャ**を採用
-   4 層構造: Domain → Application → Infrastructure → Presentation
-   Python 3.11+ / FastAPI / SQLAlchemy 2.x

### フロントエンド（frontend/）

-   Next.js 14 / TypeScript / TailwindCSS
-   App Router 使用

### データベース

-   PostgreSQL 16（Docker）
-   スキーマ定義: `backend/src/infrastructure/database/init.sql`

---

## コーディング規約

-   型ヒント必須（Python）
-   TypeScript strict mode（Frontend）
-   詳細: `docs/poc/coding-standard/`

---

## 開発環境ルール

### パッケージ管理

-   **仮想環境**: `backend/.venv` を使用
-   **`pip install` を直接実行しない**
-   新規パッケージが必要な場合:
    1. `backend/requirements.txt` に追記
    2. ユーザーに確認してからインストール
    3. インストール時: `backend/.venv/bin/pip install -r requirements.txt`
-   フロントエンドも同様（`npm install` は確認後）

### テスト方針

-   ユニットテストは現状不要（必要性を感じたら追加）
-   手動テストで動作確認
-   AI 修正後の検証が必要になったら再検討

---

## 参考ドキュメント

| フォルダ                   | 内容                                   |
| -------------------------- | -------------------------------------- |
| `docs/poc/phases/`         | 開発フェーズ計画                       |
| `docs/poc/designs/`        | 機能設計書                             |
| `docs/poc/architectures/`  | アーキテクチャ設計（レイヤー構成、図） |
| `docs/poc/domain/`         | ドメイン設計（screener, portfolio, market） |
| `docs/poc/business-logic/` | ビジネスロジック仕様                   |
| `docs/poc/coding-standard/`| コーディング規約                       |
| `docs/poc/issues/`         | 課題・検討事項                         |
| `docs/poc/archive/`        | 完了・旧ドキュメント                   |
