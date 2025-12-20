# Phase 3 補足: 管理者向けデータ更新機能

## 背景

スクリーニングデータの計算（yfinance API呼び出し、RS Rating計算、CAN-SLIMスコア計算）は
コストが高いため、ユーザーリクエスト毎に実行するのではなく、
事前にバッチ処理で計算しDBにキャッシュする設計としている。

PoC段階では、管理者が手動でデータ更新をトリガーできるAPIを提供する。

---

## 機能要件

### 1. データ更新API

```
POST /api/admin/screener/refresh
```

- 指定したシンボルリストのデータを更新
- 進捗状況をリアルタイムで取得可能
- 認証は将来的に追加（PoC段階ではなし）

### 2. 進捗確認機能

管理画面で以下を確認できる:

- 更新対象の銘柄数
- 処理済み銘柄数
- 成功/失敗の内訳
- 推定残り時間
- エラー詳細

---

## 技術設計

### アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                      データ更新フロー                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [管理者]                                                        │
│     │                                                           │
│     ▼                                                           │
│  POST /admin/screener/refresh                                   │
│     │                                                           │
│     ├─→ ジョブID発行 & 即座にレスポンス                           │
│     │                                                           │
│     ▼                                                           │
│  ┌─────────────────┐                                            │
│  │ Background Task │ ← asyncio / Celery / ARQ                   │
│  │                 │                                            │
│  │  for symbol in symbols:                                      │
│  │    1. yfinance API呼び出し                                   │
│  │    2. RS Rating計算                                          │
│  │    3. CAN-SLIMスコア計算                                      │
│  │    4. DB保存                                                 │
│  │    5. 進捗更新 → Redis/DB                                    │
│  │                                                              │
│  └─────────────────┘                                            │
│     │                                                           │
│     ▼                                                           │
│  GET /admin/screener/refresh/{job_id}/status                    │
│     │                                                           │
│     └─→ { progress: 45, total: 100, status: "running", ... }    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### API設計

#### 1. 更新開始

```http
POST /api/admin/screener/refresh
Content-Type: application/json

{
  "symbols": ["AAPL", "NVDA", "MSFT", ...],
  "source": "sp500"  // または "custom"
}
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "job_id": "refresh_20240115_103000",
    "total_symbols": 500,
    "status": "started",
    "started_at": "2024-01-15T10:30:00Z"
  }
}
```

#### 2. 進捗確認

```http
GET /api/admin/screener/refresh/{job_id}/status
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "job_id": "refresh_20240115_103000",
    "status": "running",  // "pending" | "running" | "completed" | "failed"
    "progress": {
      "total": 500,
      "processed": 225,
      "succeeded": 220,
      "failed": 5,
      "percentage": 45.0
    },
    "timing": {
      "started_at": "2024-01-15T10:30:00Z",
      "elapsed_seconds": 120,
      "estimated_remaining_seconds": 150
    },
    "errors": [
      {"symbol": "XYZ", "error": "Invalid symbol"}
    ]
  }
}
```

#### 3. 更新キャンセル

```http
DELETE /api/admin/screener/refresh/{job_id}
```

---

## 実装タスク

### Backend

- [ ] `RefreshJobModel` SQLAlchemyモデル作成（ジョブ状態管理）
- [ ] `RefreshScreenerDataUseCase` 作成
- [ ] `AdminController` ルーター作成
- [ ] バックグラウンドタスク実装（FastAPI BackgroundTasks or ARQ）
- [ ] 進捗更新ロジック実装

### Frontend（管理画面）

- [ ] `/admin/screener` ページ作成
- [ ] 更新開始ボタン
- [ ] プログレスバーコンポーネント
- [ ] リアルタイム進捗表示（ポーリング or SSE）
- [ ] エラー一覧表示

---

## 成果物

```
backend/src/
├── application/
│   └── use_cases/
│       └── admin/
│           └── refresh_screener_data.py
├── infrastructure/
│   └── database/
│       └── models/
│           └── refresh_job_model.py
└── presentation/
    └── api/
        └── admin_controller.py

frontend/src/
├── app/
│   └── admin/
│       └── screener/
│           └── page.tsx
└── components/
    └── admin/
        ├── RefreshPanel.tsx
        └── ProgressBar.tsx
```

---

## 優先度・スケジュール

| 項目 | 優先度 | 備考 |
|------|--------|------|
| 更新API（同期版） | P1 | 最小限の実装 |
| 進捗確認API | P2 | バックグラウンド処理と合わせて |
| 管理画面UI | P2 | API完成後 |
| キャンセル機能 | P3 | あれば便利 |

---

## 将来拡張

- **定期実行（Cron）**: 市場クローズ後に自動実行
- **Webhook通知**: 完了時にSlack通知
- **認証**: 管理者のみアクセス可能に
- **銘柄リスト管理**: S&P500、NASDAQ100などプリセット管理
