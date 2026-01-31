# AI Trade App

CAN-SLIM投資手法を支援するHybrid Analyzerアプリケーション。

## 概要

マーケット環境の分析、CAN-SLIM条件でのスクリーニング、ペーパートレードによる検証を行うPoCアプリケーション。

### 主な機能

- **Market Module**: マーケット状態（Risk On/Off/Neutral）の判定・可視化
- **Screener Module**: CAN-SLIM条件に基づく銘柄スクリーニング
- **Portfolio Module**: ウォッチリスト管理、ペーパートレード記録
- **Admin Module**: スクリーニングデータの更新・ジョブ管理

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| Frontend | Next.js 14, TypeScript, TailwindCSS |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.x |
| Database | PostgreSQL 16 |
| External | yfinance |

## クイックスタート

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
# テーブルが表示されれば成功
```

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

## 動作確認

### スクリーニングデータの更新（管理画面）

管理画面からS&P 500銘柄のスクリーニングデータを更新できます。

1. **全サービス起動**（PostgreSQL, Backend, Frontend）

2. **管理画面にアクセス**
   ```
   http://localhost:3000/admin/screener
   ```

3. **「更新開始」ボタンをクリック**
   - Job 1: データ収集（yfinance APIから株価・財務データ取得）
   - Job 2: RS Rating計算（パーセンタイルランキング）
   - Job 3: CAN-SLIMスコア計算

4. **進捗確認**
   - 画面上で各ジョブの進捗がリアルタイム表示
   - 完了まで数分かかります（500銘柄 × API呼び出し）

### APIエンドポイント確認

| エンドポイント | 説明 |
|---------------|------|
| `GET /api/health` | ヘルスチェック |
| `GET /api/market/status` | マーケット状態 |
| `GET /api/screener/canslim` | CAN-SLIMスクリーニング結果 |
| `POST /api/admin/screener/refresh` | データ更新開始 |
| `GET /api/admin/screener/refresh/latest` | 最新フロー一覧 |

Swagger UI: http://localhost:8000/api/docs

---

## アーキテクチャ

### Backend（シンプル5層アーキテクチャ）

```
backend/src/
├── models/           # ORM モデル（テーブル定義）
├── services/         # ビジネスロジック（計算処理）
├── queries/          # データアクセス（CRUD操作）
├── adapters/         # 外部連携（DB接続、yfinance）
├── presentation/     # API層（コントローラ、スキーマ）
├── jobs/             # バッチ処理（ジョブ、フロー）
├── main.py
└── config.py
```

#### 層の役割

| 層 | 役割 | 例 |
|----|------|-----|
| models/ | テーブル構造 + エンティティメソッド | CANSLIMStock, FlowExecution |
| services/ | ビジネスロジック、計算 | RSCalculator, CANSLIMScorer |
| queries/ | DBクエリ | CANSLIMStockQuery |
| adapters/ | 外部システム接続 | YFinanceGateway, database |
| presentation/ | APIエンドポイント | controllers/, schemas/ |
| jobs/ | バックグラウンド処理 | RefreshScreenerFlow |

#### 依存関係

```
presentation ──> queries ──> models
      │              ↓
      │          adapters
      ↓
   services ──────> models
      │
   jobs ───────────────┘
```

詳細: [docs/poc/architectures/service-components.md](docs/poc/architectures/service-components.md)

### Frontend

```
frontend/src/
├── app/              # App Router（ページ）
│   ├── admin/        # 管理画面
│   ├── screener/     # スクリーナー
│   ├── portfolio/    # ポートフォリオ
│   └── api/          # API Routes（Backend proxy）
├── components/       # 共通UIコンポーネント
├── hooks/            # カスタムフック
├── lib/              # ユーティリティ
└── types/            # 型定義
```

---

## DBマイグレーション

PoCではマイグレーションツールを使用せず、init.sqlを直接編集する方式を採用。

### スキーマ変更時の手順

```bash
# 1. init.sql を編集
vim docker/postgres/init.sql

# 2. 既存のコンテナ・ボリュームを削除（データも削除される）
docker compose down -v

# 3. 再起動（init.sql が自動実行される）
docker compose up -d

# 4. テーブル確認
docker compose exec postgres psql -U trader -d trading -c "\dt"
```

### テーブル一覧

| テーブル | 説明 |
|---------|------|
| canslim_stocks | CAN-SLIM銘柄データ |
| market_snapshots | マーケット状態の履歴 |
| watchlist | ウォッチリスト |
| trades | トレード記録 |
| flow_executions | フロー実行履歴 |
| job_executions | ジョブ実行履歴 |

詳細: [docs/poc/architectures/database-design.md](docs/poc/architectures/database-design.md)

---

## pgAdmin（DB管理ツール）

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

---

## コマンド一覧

```bash
# PostgreSQL
docker compose up -d      # 起動
docker compose down       # 停止
docker compose down -v    # 停止 + ボリューム削除（DB初期化）
docker compose logs -f    # ログ確認

# Backend
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload --port 8000

# Frontend
cd frontend
npm run dev               # 開発サーバー
npm run build             # ビルド
npm run lint              # Lint
```

---

## 開発フェーズ

| Phase | 内容 | 状態 |
|-------|------|------|
| 1 | 基盤構築（Docker, FastAPI, Next.js） | 完了 |
| 2 | Market Module | 完了 |
| 3 | Screener Module | 完了 |
| 4 | Portfolio Module | 完了 |

## ドキュメント

- [PoC概要](docs/poc/overview.md)
- [アーキテクチャ設計](docs/poc/architectures/service-components.md)
- [ディレクトリ構成](docs/poc/architectures/directory-structure.md)
- [API設計](docs/poc/architectures/api-design.md)
- [DB設計](docs/poc/architectures/database-design.md)
- [フロントエンド設計](docs/poc/architectures/frontend-architecture.md)
