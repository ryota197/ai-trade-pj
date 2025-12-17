# PoC 実装プラン概要

## 目的

CAN-SLIM投資手法を支援するHybrid Analyzerアプリケーションの仮説検証。
ローカル環境で完結し、コスト$0で基本機能を実装・検証する。

---

## フェーズ構成

```
Phase 1        Phase 2        Phase 3        Phase 4
基盤構築   →   Market    →   Screener  →   Portfolio
                Module        Module        Module
   ↓              ↓              ↓              ↓
環境構築      ダッシュ       銘柄          ウォッチ
DB接続        ボード        スクリー       リスト
API基盤       市場状態      ニング        ペーパー
                判定                       トレード
```

---

## フェーズ一覧

| Phase | 名称 | 目的 | 詳細 |
|-------|------|------|------|
| 1 | 基盤構築 | 開発環境・基本構成の確立 | [phase1-foundation.md](./phase1-foundation.md) |
| 2 | Market Module | 市場環境の可視化・判定 | [phase2-market.md](./phase2-market.md) |
| 3 | Screener Module | CAN-SLIM銘柄スクリーニング | [phase3-screener.md](./phase3-screener.md) |
| 4 | Portfolio Module | ウォッチリスト・トレード記録 | [phase4-portfolio.md](./phase4-portfolio.md) |

> **Note**: Phase 5（ML）はPoC検証後に判断

---

## 全体スコープ

### PoC対象（In Scope）

- [x] マーケット状態の可視化（VIX, RSI, 200MA等）
- [x] CAN-SLIM条件でのスクリーニング
- [x] 個別銘柄の詳細表示
- [x] ウォッチリスト管理
- [x] ペーパートレード記録
- [x] パフォーマンス集計

### PoC対象外（Out of Scope）

- [ ] ユーザー認証・マルチユーザー
- [ ] 本番環境デプロイ
- [ ] リアルタイム株価（WebSocket）
- [ ] MLによるパターン認識（Phase 5）
- [ ] アラート・通知機能
- [ ] モバイル対応

---

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| Frontend | Next.js 14, TypeScript, TailwindCSS |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.x |
| Database | PostgreSQL 16 (Docker) |
| External | yfinance, FMP (free tier) |

---

## 成果物

### Phase 1 完了時
- Docker環境で動作するPostgreSQL
- FastAPI基本構成（ヘルスチェックAPI）
- Next.js基本構成（トップページ）
- yfinanceからの株価取得確認

### Phase 2 完了時
- マーケット状態を表示するダッシュボード
- VIX, Put/Call Ratio, S&P500 RSI等の指標表示
- Risk On/Off/Neutral の判定表示

### Phase 3 完了時
- CAN-SLIM条件でフィルタリングされた銘柄一覧
- 個別銘柄の詳細ページ（チャート、財務データ）
- フィルター条件のカスタマイズ

### Phase 4 完了時
- ウォッチリストの追加・削除
- ペーパートレードの記録
- パフォーマンス集計（勝率、平均リターン等）

---

## 依存関係

```
Phase 1 ─────────────────────────────────────────────┐
    │                                                │
    ▼                                                │
Phase 2 (Market)                                     │
    │                                                │ 共通基盤
    ▼                                                │
Phase 3 (Screener) ←─ Phase 2のMarket状態を参照      │
    │                                                │
    ▼                                                │
Phase 4 (Portfolio) ←─ Phase 3のStock情報を参照 ─────┘
```

---

## 関連ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| [../overview.md](../overview.md) | PoC全体概要 |
| [../architectures/service-components.md](../architectures/service-components.md) | クリーンアーキテクチャ設計 |
| [../architectures/api-design.md](../architectures/api-design.md) | API設計 |
| [../architectures/database-design.md](../architectures/database-design.md) | DB設計 |
