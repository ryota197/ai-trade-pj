## 概要

Market状態を定期的にDBに保存するバッチ処理を実装する。

## 背景

現在のAPIはリアルタイムでyfinanceからデータを取得し、DBには保存しない。
履歴分析やトレンド把握のため、将来的にバッチジョブでスナップショットを保存する。

## 現状

- `market_snapshots` テーブル: ✅ 定義済み（`init.sql`）
- `MarketSnapshotModel`: ✅ 定義済み
- `PostgresMarketRepository.save()`: ✅ 実装済み
- 定期実行の仕組み: ❌ 未実装

## 実装内容

### 1. バッチジョブの実装

- APScheduler または cron を使用
- 1時間ごとに実行

### 2. 実行ロジック

```python
# 疑似コード
async def save_market_snapshot():
    use_case = GetMarketStatusUseCase(...)
    status = await use_case.execute()
    repository = PostgresMarketRepository(...)
    await repository.save(status)
```

### 3. 履歴取得API（オプション）

- `GET /api/market/history` - 過去のスナップショット一覧

## 関連ドキュメント

- `docs/poc/plan/implementation-status.md` PENDING-001
- `docs/poc/plan/phase2-market.md`「将来対応（バックログ）」

## 工数

中（半日程度）
