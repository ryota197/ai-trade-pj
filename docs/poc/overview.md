# PoC アーキテクチャ概要

## 概要

案3: Hybrid Analyzer のPoC構成。ローカル環境で完結し、コスト$0で仮説検証を行う。

---

## 全体アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client (Browser)                          │
│                      localhost:3000                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                           │
│                      localhost:3000                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │  Dashboard   │ │  Screener    │ │  Portfolio   │             │
│  │    Page      │ │    Page      │ │    Page      │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
└─────────────────────────────┬───────────────────────────────────┘
                              │ REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                            │
│                      localhost:8000                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │   Market     │ │  Screener    │ │  Portfolio   │             │
│  │   Service    │ │   Service    │ │   Service    │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
│  ┌──────────────┐ ┌──────────────┐                              │
│  │    Data      │ │     ML       │                              │
│  │   Service    │ │   Service    │                              │
│  └──────────────┘ └──────────────┘                              │
└───────────┬─────────────────┬───────────────────────────────────┘
            │                 │
            ▼                 ▼
┌───────────────────┐  ┌─────────────────────────────────────────┐
│    PostgreSQL     │  │           External APIs                  │
│   localhost:5432  │  │  yfinance │ SEC EDGAR │ FMP (free tier) │
│    (Docker)       │  └─────────────────────────────────────────┘
└───────────────────┘
```

---

## サービス構成

| サービス | 責務 |
|---------|------|
| **Market Service** | マーケット全体の状態分析・判定 |
| **Screener Service** | CAN-SLIMスクリーニング |
| **Data Service** | 外部APIからのデータ取得・正規化 |
| **Portfolio Service** | ウォッチリスト・ペーパートレード管理 |
| **ML Service** | チャートパターン認識（Phase 2以降） |

> **Note**: バックエンドは**クリーンアーキテクチャ**を採用。
> 各サービスはユースケース層として実装され、Domain/Application/Infrastructure/Presentationの4層構造で構成される。
> 詳細は [service-components.md](./architectures/service-components.md) を参照。

---

## 開発フェーズ

### Phase 1: 基盤構築
1. Docker + PostgreSQL環境構築
2. FastAPI基本構成（プロジェクト作成、DB接続）
3. Next.js基本構成（プロジェクト作成、API連携）
4. Data Service実装（yfinance連携）

### Phase 2: Market Module
1. マーケット指標取得実装
2. マーケット状態判定ロジック
3. ダッシュボードUI

### Phase 3: Screener Module
1. CAN-SLIMスクリーニングロジック
2. スクリーナーUI
3. 個別銘柄詳細ページ

### Phase 4: Portfolio Module
1. ウォッチリスト機能
2. ペーパートレード記録
3. パフォーマンス計測

### Phase 5: ML（検証後）
1. チャートパターン認識PoC
2. エントリーポイント提案機能

---

## 詳細ドキュメント

### アーキテクチャ

| ドキュメント | 内容 |
|-------------|------|
| [service-components.md](./architectures/service-components.md) | 各サービスの詳細設計 |
| [api-design.md](./architectures/api-design.md) | REST API設計 |
| [database-design.md](./architectures/database-design.md) | データベース設計・DDL |
| [directory-structure.md](./architectures/directory-structure.md) | ディレクトリ構成 |

### コーディング規約

| ドキュメント | 内容 |
|-------------|------|
| [tech-stack.md](./coding-standard/tech-stack.md) | 技術スタック・バージョン |
| [frontend-guidelines.md](./coding-standard/frontend-guidelines.md) | フロントエンド規約 |
| [backend-guidelines.md](./coding-standard/backend-guidelines.md) | バックエンド規約 |

---

## クイックスタート

```bash
# 1. PostgreSQL起動
docker compose up -d

# 2. Backend起動
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# 3. Frontend起動
cd frontend
npm install
npm run dev
```

---

## 技術スタック（概要）

| レイヤー | 技術 |
|---------|------|
| Frontend | Next.js 14, TypeScript, TailwindCSS |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.x |
| Database | PostgreSQL 16 (Docker) |
| External | yfinance, SEC EDGAR, FMP |
