# AI Trade App

CAN-SLIM投資手法を支援するHybrid Analyzerアプリケーション。

## 概要

マーケット環境の分析、CAN-SLIM条件でのスクリーニング、ペーパートレードによる検証を行うPoCアプリケーション。

### 主な機能

- **Market Module**: マーケット状態（Risk On/Off/Neutral）の判定・可視化
- **Screener Module**: CAN-SLIM条件に基づく銘柄スクリーニング
- **Portfolio Module**: ウォッチリスト管理、ペーパートレード記録

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| Frontend | Next.js 14, TypeScript, TailwindCSS |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.x |
| Database | PostgreSQL 16 |
| External | yfinance, FMP API |

## セットアップ

### 必要環境

- Docker / Docker Compose
- Python 3.11+
- Node.js 18+

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd ai-trade-app
```

### 2. 環境変数の設定

```bash
cp .env.example .env
# 必要に応じて .env を編集
```

### 3. PostgreSQL起動

```bash
docker compose up -d
```

起動確認:
```bash
docker compose ps
# STATUS が healthy になっていることを確認
```

DB接続確認:
```bash
docker compose exec postgres psql -U trader -d trading -c "\dt"
# 5つのテーブルが表示されれば成功
```

### pgAdmin（DB管理ツール）

ブラウザでDBを確認・操作できます。

1. http://localhost:5050 にアクセス
2. ログイン
   - Email: `admin@local.dev`
   - Password: `admin`
3. サーバー追加（Add New Server）
   - **General** > Name: `trading`（任意）
   - **Connection**:
     - Host: `postgres`
     - Port: `5432`
     - Database: `trading`
     - Username: `trader`
     - Password: `localdev`

### 4. Backend起動

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

API確認: http://localhost:8000/docs

### 5. Frontend起動

```bash
cd frontend
npm install
npm run dev
```

アプリ確認: http://localhost:3000

## ディレクトリ構成

```
ai-trade-app/
├── docker-compose.yml
├── .env.example
├── docs/                    # ドキュメント
│   └── poc/
│       ├── overview.md
│       ├── plan/            # 実装プラン
│       ├── architectures/   # 設計ドキュメント
│       └── coding-standard/ # コーディング規約
├── backend/                 # FastAPI（クリーンアーキテクチャ）
│   └── src/
│       ├── domain/
│       ├── application/
│       ├── infrastructure/
│       └── presentation/
└── frontend/                # Next.js
    └── src/
        ├── app/
        ├── components/
        ├── hooks/
        └── lib/
```

## 開発フェーズ

| Phase | 内容 | 状態 |
|-------|------|------|
| 1 | 基盤構築（Docker, FastAPI, Next.js） | 進行中 |
| 2 | Market Module | - |
| 3 | Screener Module | - |
| 4 | Portfolio Module | - |

詳細: [docs/poc/plan/plan-overview.md](docs/poc/plan/plan-overview.md)

## ドキュメント

- [PoC概要](docs/poc/overview.md)
- [実装プラン](docs/poc/plan/plan-overview.md)
- [アーキテクチャ設計](docs/poc/architectures/service-components.md)
- [API設計](docs/poc/architectures/api-design.md)
- [DB設計](docs/poc/architectures/database-design.md)

## コマンド一覧

```bash
# PostgreSQL
docker compose up -d      # 起動
docker compose down       # 停止
docker compose logs -f    # ログ確認

# Backend
uvicorn src.main:app --reload --port 8000

# Frontend
npm run dev               # 開発サーバー
npm run build             # ビルド
npm run lint              # Lint
```
