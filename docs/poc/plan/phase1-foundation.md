# Phase 1: 基盤構築

## 目的

開発環境の構築と、Frontend/Backend/Databaseの基本構成を確立する。

---

## ゴール

- Docker環境でPostgreSQLが動作する
- FastAPIでヘルスチェックAPIが応答する
- Next.jsでトップページが表示される
- yfinanceから株価データが取得できる

---

## タスク

### 1.1 Docker + PostgreSQL環境構築

- [ ] `docker-compose.yml` 作成
- [ ] PostgreSQL 16 コンテナ設定
- [ ] 初期化SQL（`init.sql`）作成
- [ ] `.env.example` 作成
- [ ] 動作確認（`docker compose up -d`）

**成果物**:
```
ai-trade-app/
├── docker-compose.yml
├── .env.example
└── backend/
    └── src/
        └── infrastructure/
            └── database/
                └── init.sql
```

---

### 1.2 Backend基本構成（FastAPI）

- [ ] `backend/` ディレクトリ作成
- [ ] `pyproject.toml` または `requirements.txt` 作成
- [ ] クリーンアーキテクチャのディレクトリ構成作成
- [ ] `main.py` エントリーポイント作成
- [ ] `config.py` 設定管理作成
- [ ] DB接続設定（`infrastructure/database/connection.py`）
- [ ] ヘルスチェックAPI（`GET /api/health`）実装
- [ ] 動作確認（`uvicorn src.main:app --reload`）

**成果物**:
```
backend/
├── pyproject.toml
├── requirements.txt
└── src/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── domain/
    ├── application/
    ├── infrastructure/
    │   └── database/
    │       ├── connection.py
    │       └── models/
    └── presentation/
        ├── api/
        │   └── health_controller.py
        └── schemas/
```

**API確認**:
```bash
curl http://localhost:8000/api/health
# {"status": "ok", "database": "connected"}
```

---

### 1.3 Frontend基本構成（Next.js）

- [ ] `frontend/` ディレクトリ作成（`npx create-next-app@latest`）
- [ ] TypeScript + TailwindCSS設定
- [ ] App Router構成
- [ ] 基本レイアウト作成（`app/layout.tsx`）
- [ ] トップページ作成（`app/page.tsx`）
- [ ] APIクライアント設定（`lib/api.ts`）
- [ ] 動作確認（`npm run dev`）

**成果物**:
```
frontend/
├── package.json
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
└── src/
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx
    │   └── globals.css
    ├── lib/
    │   └── api.ts
    └── types/
```

---

### 1.4 Data Service実装（yfinance連携）

- [ ] yfinanceラッパー作成（`infrastructure/gateways/yfinance_gateway.py`）
- [ ] 株価取得機能実装（`get_quote`）
- [ ] 過去データ取得機能実装（`get_history`）
- [ ] テスト用API作成（`GET /api/data/quote/{symbol}`）
- [ ] 動作確認

**成果物**:
```
backend/src/
├── infrastructure/
│   └── gateways/
│       └── yfinance_gateway.py
└── presentation/
    └── api/
        └── data_controller.py
```

**API確認**:
```bash
curl http://localhost:8000/api/data/quote/AAPL
# {"symbol": "AAPL", "price": 185.50, "change": 2.30, ...}
```

---

## 完了条件

| # | 条件 | 確認方法 |
|---|------|----------|
| 1 | PostgreSQLが起動する | `docker compose ps` でhealthyを確認 |
| 2 | FastAPIが起動する | `http://localhost:8000/docs` でSwagger UI表示 |
| 3 | ヘルスチェックが通る | `GET /api/health` が200を返す |
| 4 | Next.jsが起動する | `http://localhost:3000` でページ表示 |
| 5 | 株価データが取得できる | `GET /api/data/quote/AAPL` がデータを返す |

---

## 参考コマンド

```bash
# PostgreSQL起動
docker compose up -d

# Backend起動
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# Frontend起動
cd frontend
npm install
npm run dev
```

---

## 次のフェーズへ

Phase 1 完了後 → [Phase 2: Market Module](./phase2-market.md)
