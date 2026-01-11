# サービスコンポーネント設計（シンプル3層アーキテクチャ）

## 概要

本プロジェクトは「A Philosophy of Software Design」の原則に基づき、
**浅いモジュール（pass-through層）を排除したシンプルな3層アーキテクチャ**を採用する。

---

## アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frameworks & Drivers                          │
│         (FastAPI, PostgreSQL, yfinance, Web Browser)            │
├─────────────────────────────────────────────────────────────────┤
│                  Presentation + Jobs                             │
│              (Controllers, Schemas, Batch Flows)                │
├─────────────────────────────────────────────────────────────────┤
│                    Infrastructure                                │
│              (Repositories, Gateways)                           │
├─────────────────────────────────────────────────────────────────┤
│                        Domain                                    │
│               (Models, Services, Repository Interfaces)         │
└─────────────────────────────────────────────────────────────────┘

依存の方向: 外側 → 内側（内側は外側を知らない）
```

---

## レイヤー構成

### 1. Domain層（最内層）

**責務**: ビジネスルール、ドメインロジックの定義

- フレームワークに依存しない純粋なPythonコード
- 他のどのレイヤーにも依存しない

| 要素 | 説明 |
|------|------|
| Model | ビジネスエンティティ（CANSLIMStock, Trade等） |
| Domain Service | 複数エンティティにまたがるロジック（RSCalculator等） |
| Repository Interface | データアクセスの抽象インターフェース |

---

### 2. Infrastructure層（インフラ層）

**責務**: 外部サービス、データベース、APIとの実際の連携

- Domain層のインターフェースを実装
- 外部ライブラリ（yfinance, SQLAlchemy等）に依存

| 要素 | 説明 |
|------|------|
| Repository Impl | リポジトリインターフェースの実装 |
| Gateway | 外部APIとの連携（インターフェース＋実装） |
| Database | DB接続設定 |

---

### 3. Presentation層（プレゼンテーション層）

**責務**: HTTPリクエスト/レスポンスの処理、API定義

- Repository/Gatewayを直接呼び出す
- Domain Model → Schema変換を担当
- FastAPIのルーター、Pydanticスキーマを定義

| 要素 | 説明 |
|------|------|
| Controller | APIルーター、Repository/Gateway呼び出し |
| Schema | Pydanticスキーマ（リクエスト/レスポンス） |
| Dependencies | 依存性注入設定 |

---

### 4. Jobs層（バッチ処理層）

**責務**: 長時間バッチ処理のオーケストレーション

- Repository/Gatewayを直接利用
- 管理画面からトリガーで実行

| 要素 | 説明 |
|------|------|
| Flow | 複数Jobのオーケストレーション |
| Job | 個別の処理単位 |

---

## Frontend（参考）

フロントエンドはシンプルな構成を維持しつつ、責務分離を意識する。

```
src/
├── app/           # ページ（Presentation）
├── components/    # UIコンポーネント（Presentation）
├── hooks/         # カスタムフック（Application相当）
├── lib/           # API通信、ユーティリティ（Infrastructure相当）
└── types/         # 型定義（Domain相当）
```

---

## 依存関係の方向

```
Presentation ──┬──> Infrastructure ──> Domain
               │
Jobs ──────────┘
```

- **Domain**: 何にも依存しない（最内層）
- **Infrastructure**: Domainのインターフェースを実装
- **Presentation**: Domain, Infrastructureに依存
- **Jobs**: Domain, Infrastructureに依存

---

## 設計原則

### なぜApplication層を削除したか

従来のクリーンアーキテクチャでは4層構造だったが、以下の理由で3層に簡素化：

1. **浅いモジュール問題**: UseCaseがRepository呼び出し→DTO変換のみの「pass-through」になっていた
2. **不要な抽象化**: 本PoCでは複数実装の差し替えが不要
3. **YAGNI原則**: 必要になるまで抽象化層を追加しない

> 参考: "A Philosophy of Software Design" by John Ousterhout

---

## テスト戦略

| レイヤー | テスト種別 | 特徴 |
|---------|-----------|------|
| Domain | 単体テスト | モック不要、純粋なロジックテスト |
| Infrastructure | 統合テスト | 実際のDB/APIとの接続テスト |
| Presentation | E2Eテスト | 全レイヤー統合テスト |

---

## 関連ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| [service-architecture.md](../service-architecture.md) | サービスアーキテクチャ全体設計 |
| [backend-guidelines.md](../coding-standard/backend-guidelines.md) | バックエンドコーディング規約 |
