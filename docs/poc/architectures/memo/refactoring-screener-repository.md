# PostgresScreenerRepository 責務分離 リファクタリング計画

## ステータス: 検討中

作成日: 2024-12-21

---

## 背景

Phase 3実装時に `PostgresScreenerRepository` が複数の責務を持つようになり、
Single Responsibility Principle (SRP) に違反している状態。

---

## 現状の問題点

### 1. PostgresScreenerRepositoryの責務過多

| 責務 | メソッド/コード | 問題レベル |
|------|----------------|-----------|
| CRUD操作 | `get_by_symbol()`, `save()`, `delete_by_symbol()` 等 | ○ 本来の責務 |
| スクリーニングクエリ | `screen()` | △ 複雑なクエリビルダー |
| ドメインロジック | `_calc_distance_from_high()` | ✗ SRP違反 |
| CAN-SLIMスコア再計算 | `_model_to_entity()` 内の `CANSLIMScore.calculate()` | ✗ SRP違反 |
| JSONシリアライズ | `save()`, `_model_to_entity()` 内 | △ 変換ロジック |
| エンティティ変換 | `_model_to_entity()` | △ マッパーに分離可能 |

### 2. ドメインロジックの混入

52週高値からの乖離率計算がInfrastructure層に存在している。
これはビジネスルールであり、Domain層（Stockエンティティ）に属すべき。

```python
# 現状（問題あり）
# infrastructure/repositories/postgres_screener_repository.py
@staticmethod
def _calc_distance_from_high(price: float, week_52_high: float) -> float:
    """52週高値からの乖離率を計算"""
    # ビジネスロジックがInfrastructure層に...
```

### 3. エンティティ変換時のスコア再計算

モデルからエンティティへの変換時に `CANSLIMScore.calculate()` を呼び出している。
これは以下の問題を引き起こす：

- 保存時と復元時でスコアが異なる可能性
- 不要な計算コスト
- テストの複雑化

```python
# 現状（問題あり）
def _model_to_entity(self, model: ScreenerResultModel) -> Stock:
    # JSONからスコア詳細を読んでいるのに再計算している
    canslim_score = CANSLIMScore.calculate(...)  # ← 再計算すべきでない
```

### 4. screen()メソッドの肥大化

複雑なフィルター条件の構築ロジックがリポジトリに直接記述されている。
Specificationパターンに分離することで、再利用性とテスタビリティが向上する。

---

## 責務分離案

### レイヤー別の責務

```
┌─────────────────────────────────────────────────────────────┐
│  Domain層（ビジネスロジック）                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Stock Entity（既存・拡張）                                  │
│  └─ distance_from_52w_high プロパティ（既存）                │
│     ※ 現状Entityにあるので、Repositoryから呼び出すべき       │
│                                                             │
│  CANSLIMScore Value Object（既存）                          │
│  └─ from_dict() クラスメソッド追加                          │
│     ※ JSONから直接復元できるようにする                       │
│                                                             │
│  ScreenerSpecification（新規）                               │
│  └─ 責務: スクリーニング条件の仕様化                         │
│     ├─ is_satisfied_by(stock: Stock) -> bool                │
│     └─ to_sql_filter() -> SQLAlchemy式                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Infrastructure層（データアクセス）                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  StockModelMapper（新規）                                    │
│  └─ 責務: Model ↔ Entity の変換                            │
│     ├─ to_entity(model) -> Stock                           │
│     └─ to_model(entity) -> ScreenerResultModel             │
│                                                             │
│  PostgresScreenerRepository（リファクタ後）                  │
│  └─ 責務: 純粋なCRUD操作のみ                                │
│     ├─ get_by_symbol()                                     │
│     ├─ save()                                              │
│     └─ delete_by_symbol()                                  │
│                                                             │
│  PostgresScreenerQueryService（新規・オプション）            │
│  └─ 責務: 複雑なクエリ操作                                  │
│     └─ screen(specification) -> ScreenerResult             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 具体的な変更内容

### 1. Domain層の変更

#### CANSLIMScore に from_dict() を追加

```python
# domain/value_objects/canslim_score.py
@dataclass(frozen=True)
class CANSLIMScore:
    # ... 既存コード ...

    @classmethod
    def from_dict(cls, data: dict, context: "CANSLIMContext") -> "CANSLIMScore":
        """JSONデータから復元（再計算なし）"""
        return cls(
            total_score=data.get("total_score", 0),
            c_score=CANSLIMCriteria.from_dict(data.get("c_score", {})),
            a_score=CANSLIMCriteria.from_dict(data.get("a_score", {})),
            # ...
        )
```

#### ScreenerSpecification の追加（オプション）

```python
# domain/specifications/screener_specification.py
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass(frozen=True)
class ScreenerSpecification(ABC):
    """スクリーニング条件の仕様"""

    @abstractmethod
    def is_satisfied_by(self, stock: Stock) -> bool:
        """銘柄が条件を満たすか判定"""
        pass


@dataclass(frozen=True)
class RSRatingSpecification(ScreenerSpecification):
    """RS Rating条件"""
    min_rating: int = 80

    def is_satisfied_by(self, stock: Stock) -> bool:
        return stock.rs_rating >= self.min_rating


@dataclass(frozen=True)
class CompositeSpecification(ScreenerSpecification):
    """複合条件（AND）"""
    specifications: tuple[ScreenerSpecification, ...]

    def is_satisfied_by(self, stock: Stock) -> bool:
        return all(spec.is_satisfied_by(stock) for spec in self.specifications)
```

### 2. Infrastructure層の変更

#### StockModelMapper の追加

```python
# infrastructure/mappers/stock_model_mapper.py
import json
from src.domain.entities.stock import Stock
from src.domain.value_objects.canslim_score import CANSLIMScore
from src.infrastructure.database.models.screener_result_model import ScreenerResultModel


class StockModelMapper:
    """Stock Entity ↔ ScreenerResultModel の変換"""

    @staticmethod
    def to_entity(model: ScreenerResultModel) -> Stock:
        """モデルからエンティティに変換"""
        canslim_score = None
        if model.canslim_detail:
            try:
                detail = json.loads(model.canslim_detail)
                # 再計算ではなく、保存されたデータから復元
                canslim_score = CANSLIMScore.from_dict(detail)
            except Exception:
                pass

        return Stock(
            symbol=model.symbol,
            name=model.name,
            price=float(model.price),
            # ... その他のフィールド
            canslim_score=canslim_score,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Stock, existing: ScreenerResultModel | None = None) -> ScreenerResultModel:
        """エンティティからモデルに変換"""
        canslim_detail = None
        if entity.canslim_score:
            canslim_detail = json.dumps(entity.canslim_score.to_dict())

        if existing:
            # 既存レコードを更新
            existing.name = entity.name
            existing.price = entity.price
            # ... 他のフィールドも更新
            existing.canslim_detail = canslim_detail
            return existing
        else:
            # 新規作成
            return ScreenerResultModel(
                symbol=entity.symbol.upper(),
                name=entity.name,
                price=entity.price,
                # ... 他のフィールド
                canslim_detail=canslim_detail,
            )
```

#### PostgresScreenerRepository のリファクタ

```python
# infrastructure/repositories/postgres_screener_repository.py（リファクタ後）
class PostgresScreenerRepository(StockRepository):
    """
    PostgreSQLによるスクリーナーリポジトリ実装

    責務: 純粋なCRUD操作のみ
    """

    def __init__(
        self,
        session: Session,
        mapper: StockModelMapper | None = None,
    ) -> None:
        self._session = session
        self._mapper = mapper or StockModelMapper()

    async def get_by_symbol(self, symbol: str) -> Stock | None:
        stmt = select(ScreenerResultModel).where(
            ScreenerResultModel.symbol == symbol.upper()
        )
        model = self._session.scalars(stmt).first()

        if model is None:
            return None

        return self._mapper.to_entity(model)  # マッパーを使用

    async def save(self, stock: Stock) -> None:
        stmt = select(ScreenerResultModel).where(
            ScreenerResultModel.symbol == stock.symbol.upper()
        )
        existing = self._session.scalars(stmt).first()

        model = self._mapper.to_model(stock, existing)  # マッパーを使用

        if not existing:
            self._session.add(model)

        self._session.commit()

    # screen() は別クラスに移動するか、Specificationを受け取る形に変更
```

---

## 分離オプション

### Option A: 最小限の変更（推奨）

1. `_calc_distance_from_high()` を削除（Stockエンティティのプロパティを使用）
2. `CANSLIMScore.from_dict()` を追加
3. `StockModelMapper` を作成してエンティティ変換を委譲

**メリット**: 変更範囲が小さい、既存APIに影響なし
**デメリット**: screen()の複雑さは残る

### Option B: 完全分離

1. Option A の内容
2. `ScreenerSpecification` パターンを導入
3. `PostgresScreenerQueryService` を作成

**メリット**: 責務が明確に分離、テスタビリティ向上
**デメリット**: 変更範囲が大きい、オーバーエンジニアリングのリスク

### Option C: CQRSパターン

1. Option A の内容
2. 読み取り用のクエリサービス（Read Model）と書き込み用のリポジトリ（Write Model）を分離

**メリット**: 読み取りパフォーマンス最適化が可能
**デメリット**: 複雑度が大幅に増加、PoCには過剰

---

## 優先度と実施タイミング

| 優先度 | アクション | 理由 | 実施時期 |
|--------|-----------|------|----------|
| **高** | `_calc_distance_from_high()` 削除 | SRP違反の解消、既にStockにプロパティあり | Phase 3完了後 |
| **高** | `CANSLIMScore.from_dict()` 追加 | 再計算防止 | 同上 |
| **中** | `StockModelMapper` 作成 | 変換ロジックの分離 | 同上 |
| **中** | Repository の screen() 簡素化 | 複雑度削減 | Phase 4以降 |
| **低** | Specificationパターン導入 | オプション、必要に応じて | 将来 |

---

## 判断基準

### リファクタリング実施の条件

1. Phase 3の基本機能が動作確認済み
2. 単体テストが整備されている
3. 他の開発に影響しないタイミング

### リファクタリング見送りの条件

1. 現状で機能要件を満たしている
2. パフォーマンス問題がない
3. コードの理解が困難でない（現状は理解可能なレベル）

---

## 影響範囲

### 変更が必要なファイル（Option A の場合）

```
backend/src/
├── domain/
│   └── value_objects/
│       └── canslim_score.py          # from_dict() 追加
├── infrastructure/
│   ├── mappers/
│   │   └── stock_model_mapper.py     # 新規作成
│   └── repositories/
│       └── postgres_screener_repository.py  # リファクタ
└── presentation/
    └── dependencies.py               # マッパーの注入
```

### 変更不要（API互換性維持）

- `StockRepository` インターフェース
- Presentation層のコントローラー
- フロントエンド

---

## 関連ドキュメント

- [refactoring-gateway-responsibilities.md](./refactoring-gateway-responsibilities.md)
- [infrastructure-layer.md](../layers/infrastructure-layer.md)
- [directory-structure.md](../directory-structure.md)
- [Phase 3: Screener Module](../../plan/phase3-screener.md)
