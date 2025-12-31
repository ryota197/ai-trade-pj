# ドメインモデリング

## 概要

DDDに基づくドメインモデルの設計ドキュメント。

---

## ドキュメント構成

```
docs/poc/domain/
├── README.md                    # このファイル
├── 00-ubiquitous-language.md    # ユビキタス言語（用語集）
├── 01-subdomain-analysis.md     # サブドメイン分析
├── 02-context-map.md            # コンテキストマップ
├── screener/                    # Screenerコンテキスト
│   ├── aggregates.md            # 集約・エンティティ・値オブジェクト
│   └── domain-services.md       # ドメインサービス
├── portfolio/                   # Portfolioコンテキスト
│   ├── aggregates.md
│   └── domain-services.md
└── market/                      # Marketコンテキスト
    ├── aggregates.md
    └── domain-services.md
```

---

## 設計プロセス

```
1. ユビキタス言語の定義
   └── 用語の統一、認識合わせ

2. コンテキストマップの作成
   └── 境界の定義、関係の明確化

3. 各コンテキストの詳細設計
   ├── 集約ルートの特定
   ├── エンティティの定義
   ├── 値オブジェクトの定義
   └── ドメインサービスの定義

4. DB設計
   └── ドメインモデルに基づくスキーマ設計
```

---

## 現在の状態

| ドキュメント | 状態 |
|-------------|------|
| ユビキタス言語 | 作成中 |
| コンテキストマップ | 作成中 |
| Screener Context | 未着手 |
| Portfolio Context | 未着手 |
| Market Context | 未着手 |

---

## 関連ドキュメント

- [アーキテクチャ設計](../architectures/)
- [ビジネスロジック](../business-logic/)
- [リファクタリング](../refactoring/)
