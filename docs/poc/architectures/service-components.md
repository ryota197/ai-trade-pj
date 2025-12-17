# サービスコンポーネント設計（クリーンアーキテクチャ）

## 概要

本プロジェクトはクリーンアーキテクチャに基づいて設計する。
依存関係は外側から内側に向かい、ビジネスロジックは外部の詳細（DB、API、フレームワーク）に依存しない。

---

## アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frameworks & Drivers                          │
│         (FastAPI, PostgreSQL, yfinance, Web Browser)            │
├─────────────────────────────────────────────────────────────────┤
│                    Interface Adapters                            │
│              (Controllers, Gateways, Presenters)                │
├─────────────────────────────────────────────────────────────────┤
│                      Application                                 │
│                      (Use Cases)                                │
├─────────────────────────────────────────────────────────────────┤
│                        Domain                                    │
│               (Entities, Value Objects, Rules)                  │
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
| Entity | ビジネスエンティティ（Stock, MarketStatus等） |
| Value Object | 不変の値オブジェクト（CANSLIMScore等） |
| Domain Service | 複数エンティティにまたがるロジック |
| Repository Interface | データアクセスの抽象インターフェース |

> 詳細・コード例: [layers/domain-layer.md](./layers/domain-layer.md)

---

### 2. Application層（ユースケース層）

**責務**: アプリケーション固有のビジネスルール、ユースケースの実装

- Domain層のみに依存
- 外部の詳細（DB、API）はインターフェース経由で利用

| 要素 | 説明 |
|------|------|
| Use Case | アプリケーション固有のビジネスロジック |
| DTO | 入出力データの定義 |
| Gateway Interface | 外部サービスの抽象インターフェース |

> 詳細・コード例: [layers/application-layer.md](./layers/application-layer.md)

---

### 3. Infrastructure層（インフラ層）

**責務**: 外部サービス、データベース、APIとの実際の連携

- Domain/Application層のインターフェースを実装
- 外部ライブラリ（yfinance, SQLAlchemy等）に依存

| 要素 | 説明 |
|------|------|
| Repository Impl | リポジトリインターフェースの実装 |
| Gateway Impl | ゲートウェイインターフェースの実装 |
| Database | DB接続、SQLAlchemyモデル |

> 詳細・コード例: [layers/infrastructure-layer.md](./layers/infrastructure-layer.md)

---

### 4. Presentation層（プレゼンテーション層）

**責務**: HTTPリクエスト/レスポンスの処理、API定義

- Application層のユースケースを呼び出す
- FastAPIのルーター、Pydanticスキーマを定義

| 要素 | 説明 |
|------|------|
| Controller | APIルーター、エンドポイント定義 |
| Schema | Pydanticスキーマ（リクエスト/レスポンス） |
| Dependencies | 依存性注入設定 |

> 詳細・コード例: [layers/presentation-layer.md](./layers/presentation-layer.md)

---

## Frontend（参考）

フロントエンドは厳密なクリーンアーキテクチャではなく、
シンプルな構成を維持しつつ、責務分離を意識する。

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
Presentation → Application → Domain ← Infrastructure
                    ↓                      ↓
              (uses interfaces)    (implements interfaces)
```

- **Domain**: 何にも依存しない
- **Application**: Domainのみに依存、Infrastructureはインターフェース経由
- **Infrastructure**: Domain/Applicationのインターフェースを実装
- **Presentation**: Application（ユースケース）に依存

---

## テスト戦略

| レイヤー | テスト種別 | 特徴 |
|---------|-----------|------|
| Domain | 単体テスト | モック不要、純粋なロジックテスト |
| Application | 単体テスト | リポジトリ/ゲートウェイをモック化 |
| Infrastructure | 統合テスト | 実際のDB/APIとの接続テスト |
| Presentation | E2Eテスト | 全レイヤー統合テスト |

---

## 関連ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| [layers/domain-layer.md](./layers/domain-layer.md) | Domain層の詳細・コード例 |
| [layers/application-layer.md](./layers/application-layer.md) | Application層の詳細・コード例 |
| [layers/infrastructure-layer.md](./layers/infrastructure-layer.md) | Infrastructure層の詳細・コード例 |
| [layers/presentation-layer.md](./layers/presentation-layer.md) | Presentation層の詳細・コード例 |
| [directory-structure.md](./directory-structure.md) | ディレクトリ構成 |
