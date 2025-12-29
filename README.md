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
# 6つのテーブルが表示されれば成功
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

API確認: http://localhost:8000/api/docs

### 5. Frontend起動

```bash
cd frontend
npm install
npm run dev
```

アプリ確認: http://localhost:3000

---

## DBマイグレーション

PoCではマイグレーションツールを使用せず、init.sqlを直接編集する方式を採用。

### スキーマ変更時の手順

```bash
# 1. init.sql を編集
vim backend/src/infrastructure/database/init.sql

# 2. 既存のコンテナ・ボリュームを削除（データも削除される）
docker compose down -v

# 3. 再起動（init.sql が自動実行される）
docker compose up -d

# 4. テーブル確認
docker compose exec postgres psql -U trader -d trading -c "\dt"
```

### データを保持したい場合

```bash
# 1. 既存データをバックアップ
docker compose exec postgres pg_dump -U trader trading > backup.sql

# 2. 手動でALTER TABLE等を実行
docker compose exec postgres psql -U trader -d trading

# psql内で実行
ALTER TABLE stocks ADD COLUMN new_column VARCHAR(50);
\q
```

### テーブル一覧

| テーブル | 説明 |
|---------|------|
| stocks | 銘柄データ（CAN-SLIM指標含む） |
| market_snapshots | マーケット状態の履歴 |
| watchlist | ウォッチリスト |
| paper_trades | ペーパートレード記録 |
| price_cache | 株価キャッシュ |
| job_executions | ジョブ実行履歴 |

詳細: [DB設計](docs/poc/architectures/database-design.md)

---

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
│       ├── domain/          # ビジネスルール
│       ├── application/     # ユースケース
│       ├── infrastructure/  # DB・外部API
│       ├── presentation/    # APIエンドポイント
│       └── jobs/            # バックグラウンドジョブ
│           ├── lib/         # 共通基盤
│           ├── executions/  # 個別ジョブ
│           └── flows/       # オーケストレーション
└── frontend/                # Next.js
    └── src/
        ├── app/             # App Router
        │   ├── _components/ # 共通コンポーネント
        │   ├── dashboard/   # ダッシュボード
        │   ├── screener/    # スクリーナー
        │   ├── stock/       # 銘柄詳細
        │   ├── portfolio/   # ポートフォリオ
        │   └── admin/       # 管理画面
        ├── components/      # 共通UIコンポーネント
        ├── hooks/           # 共通フック
        └── lib/             # ユーティリティ
```

## 開発フェーズ

| Phase | 内容 | 状態 |
|-------|------|------|
| 1 | 基盤構築（Docker, FastAPI, Next.js） | 完了 |
| 2 | Market Module | 完了 |
| 3 | Screener Module | 進行中 |
| 4 | Portfolio Module | - |

詳細: [docs/poc/plan/plan-overview.md](docs/poc/plan/plan-overview.md)

## ドキュメント

- [PoC概要](docs/poc/overview.md)
- [実装プラン](docs/poc/plan/plan-overview.md)
- [アーキテクチャ設計](docs/poc/architectures/service-components.md)
- [レイヤー設計](docs/poc/architectures/layers/overview.md)
- [API設計](docs/poc/architectures/api-design.md)
- [DB設計](docs/poc/architectures/database-design.md)
- [フロントエンド設計](docs/poc/architectures/frontend-architecture.md)

## コマンド一覧

```bash
# PostgreSQL
docker compose up -d      # 起動
docker compose down       # 停止
docker compose down -v    # 停止 + ボリューム削除（DB初期化）
docker compose logs -f    # ログ確認

# Backend
uvicorn src.main:app --reload --port 8000

# Frontend
npm run dev               # 開発サーバー
npm run build             # ビルド
npm run lint              # Lint
```
