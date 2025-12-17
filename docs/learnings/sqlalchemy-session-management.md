# SQLAlchemy セッション管理

## 概要

SQLAlchemyにおけるEngine、Session、Connectionの違いと、
なぜSessionをシングルトンにしないかを解説する。

---

## 3つの概念

| 概念 | 役割 | ライフサイクル |
|------|------|---------------|
| **Engine** | コネクションプールの管理 | アプリケーション全体で1つ |
| **Connection** | 物理的なDB接続 | プールで再利用 |
| **Session** | 論理的な作業単位（トランザクション） | リクエストごとに新規作成 |

---

## なぜSessionをシングルトンにしないか

### ❌ シングルトンの問題

```python
# 悪い例: 全リクエストで同じセッションを共有
@lru_cache
def get_db():
    return SessionLocal()
```

| 問題 | 説明 |
|------|------|
| トランザクション混在 | リクエストAのcommitがリクエストBのデータも確定 |
| rollback影響 | 1つのエラーで全リクエストがrollback |
| 並行処理の競合 | 複数リクエストが同じセッションを操作 |

### ✅ リクエストごとに新規作成

```python
# 正しい例: 毎回新しいセッションを作成
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- 各リクエストが独立したトランザクションを持つ
- エラーの影響範囲がリクエスト内に限定
- `finally` で確実にセッションをクローズ

---

## コネクションプールの仕組み

```
┌─────────────────────────────────────┐
│        Connection Pool              │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│  │Conn1│ │Conn2│ │Conn3│ │Conn4│   │
│  └──┬──┘ └──┬──┘ └─────┘ └─────┘   │
└─────┼───────┼───────────────────────┘
      │       │
      ▼       ▼
  Request1  Request2
  (Session) (Session)
```

- **Session作成**: プールから空きConnectionを取得
- **Session終了**: Connectionをプールに返却
- **物理接続は再利用**: 毎回TCP接続を張り直すわけではない

### プール設定

```python
engine = create_engine(
    database_url,
    pool_size=5,        # 常時保持する接続数
    max_overflow=10,    # 追加で作成可能な接続数
    pool_pre_ping=True, # 使用前に接続の有効性を確認
)
```

---

## FastAPIでの使い方

```python
from fastapi import Depends
from sqlalchemy.orm import Session

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/items")
def get_items(db: Session = Depends(get_db)):
    # リクエスト開始時: セッション作成
    items = db.query(Item).all()
    return items
    # リクエスト終了時: finallyでセッションクローズ
```

---

## シングルトンにすべきもの・すべきでないもの

| 対象 | パターン | 理由 |
|------|----------|------|
| `Settings` | シングルトン（`@lru_cache`） | 設定は不変、1回読めば十分 |
| `Engine` | シングルトン（モジュール変数） | コネクションプール管理 |
| `Session` | リクエストごとに新規 | トランザクション分離が必要 |

---

## 参考

- [SQLAlchemy公式 - Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [FastAPI公式 - SQL Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)
