# システム可視化ドキュメント

## 概要

AI Trade Appのアーキテクチャを可視化したドキュメント集。
コードを読まずに全体像を把握するための参照資料。

---

## ドキュメント一覧

| ドキュメント | 内容 | 用途 |
|-------------|------|------|
| [module-dependencies.md](./diagrams/module-dependencies.md) | モジュール依存関係図 | 全体構成・レイヤー間の関係を把握 |
| [data-flow.md](./diagrams/data-flow.md) | データフロー図 | 機能ごとのリクエスト/レスポンスの流れを把握 |
| [class-diagrams.md](./diagrams/class-diagrams.md) | クラス図 | 主要クラスの構造と関係を把握 |
| [file-reference.md](./diagrams/file-reference.md) | ファイルリファレンス | ファイルの場所・役割を素早く特定 |

---

## 目的別ガイド

### 全体像を把握したい

1. **[module-dependencies.md](./diagrams/module-dependencies.md)** を読む
   - システム全体構成図
   - レイヤー構成図
   - バックエンド/フロントエンドの依存関係

### 特定機能の流れを追いたい

1. **[data-flow.md](./diagrams/data-flow.md)** を読む
   - スクリーニング機能のフロー
   - 銘柄詳細ページのフロー
   - マーケット状態取得のフロー

### クラスの関係を知りたい

1. **[class-diagrams.md](./diagrams/class-diagrams.md)** を読む
   - Domain層のEntity/VO
   - Application層のUseCase
   - Infrastructure層のRepository/Gateway

### ファイルを探したい

1. **[file-reference.md](./diagrams/file-reference.md)** を読む
   - バックエンド/フロントエンドのディレクトリ構成
   - 「〇〇を変更したい時に見るファイル」早見表

---

## 関連ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| [use-case-diagram.md](./use-case-diagram.md) | ユースケース図 |
| [api-design.md](./api-design.md) | REST API設計 |
| [database-design.md](./database-design.md) | データベース設計 |
| [directory-structure.md](./directory-structure.md) | ディレクトリ構成詳細 |
