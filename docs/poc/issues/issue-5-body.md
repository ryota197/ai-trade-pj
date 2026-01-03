## 概要

管理者機能へのアクセス制御のため、認証機能を実装する。

## 背景

現在のPoC実装ではローカル環境専用のため認証機能がない。
デプロイ時には管理者APIエンドポイントへの不正アクセスを防ぐ必要がある。

## 対象エンドポイント

| エンドポイント | 説明 |
|---------------|------|
| `POST /api/admin/screener/refresh` | スクリーニングデータ更新開始 |
| `GET /api/admin/screener/refresh/{job_id}/status` | 進捗確認 |
| `DELETE /api/admin/screener/refresh/{job_id}` | キャンセル |
| `/admin/*` | 管理者UIページ |

## 実装案

### 案1: API Key認証（シンプル）

```python
# バックエンド
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

def verify_admin_key(api_key: str = Header(...)):
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401)
```

```typescript
// フロントエンド BFF
const ADMIN_API_KEY = process.env.ADMIN_API_KEY;
// BFF経由でのみ管理者APIを呼び出し
```

### 案2: Basic認証

- `admin:password` 形式
- 環境変数で設定

### 案3: OAuth/JWT（本格的）

- 将来的にマルチユーザー対応する場合

## 推奨

デプロイ初期は**案1（API Key）または案2（Basic認証）**で十分。
将来マルチユーザー対応が必要になった時点で案3を検討。

## 関連ドキュメント

- `docs/poc/plan/plan-overview.md` - PoC対象外として記載
- `docs/poc/issues/issue-3-body.md` - 管理者機能

## 工数

中（半日〜1日程度）
