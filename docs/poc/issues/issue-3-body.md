## 概要

スクリーニングデータを手動で更新するための管理者向けAPI・UIを実装する。

## 背景

スクリーニングデータの計算（yfinance API呼び出し、RS Rating計算、CAN-SLIMスコア計算）はコストが高いため、ユーザーリクエスト毎ではなく、事前にバッチ処理で計算しDBにキャッシュする設計。

PoC段階では、管理者が手動でデータ更新をトリガーできるAPIを提供する。

## 実装内容

### Backend API

| メソッド | エンドポイント | 説明 | 優先度 |
|---------|---------------|------|--------|
| POST | `/api/admin/screener/refresh` | 更新開始 | P1 |
| GET | `/api/admin/screener/refresh/{job_id}/status` | 進捗確認 | P2 |
| DELETE | `/api/admin/screener/refresh/{job_id}` | キャンセル | P3 |

### Frontend

- `/admin/screener` ページ作成
- 更新開始ボタン
- プログレスバーコンポーネント
- リアルタイム進捗表示（ポーリング）
- エラー一覧表示

## 詳細設計

`docs/poc/plan/phase3-admin-refresh.md` を参照

## 関連ドキュメント

- `docs/poc/plan/implementation-status.md` PENDING-003
- `docs/poc/plan/phase3-admin-refresh.md`

## 工数

大（1日程度）
