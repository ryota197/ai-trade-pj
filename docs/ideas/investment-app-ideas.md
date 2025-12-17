# 投資アプリ アイディア

## 背景・課題

### 現状の投資スタイル
- インデックスファンド（S&P500）で年15%前後のリターン
- 暴落後の買い、天井付近での売りでタイミング投資が得意
- CAN-SLIMでの個別株投資はエントリーポイントのミスで期待リターンを下回った

### 解決したい課題
1. **個別株のエントリーポイント判断の精度向上**
2. マーケットタイミングの定量化・再現性向上
3. 感覚に頼っている部分をデータドリブンに

---

## アプリアイディア

### 案1: CAN-SLIM Entry Point Detector

**概要**: AIを活用してCAN-SLIM投資法のエントリーポイントを自動検出

**主要機能**:
- チャートパターン認識（カップウィズハンドル、ダブルボトム、フラットベース等）
- ピボットポイント（ブレイクアウトライン）の自動算出
- 出来高分析（機関投資家の買い集め検出）
- エントリー条件成立時のアラート通知

**技術スタック**:
- Frontend: Next.js + TypeScript
- Backend: Python (FastAPI)
- ML: PyTorch/TensorFlow（パターン認識）
- Data: Yahoo Finance API / Alpha Vantage

**差別化ポイント**:
- 単なるスクリーニングではなく、AIによるチャートパターンの視覚的認識
- CAN-SLIMに特化した設計

---

### 案2: Market Timing Intelligence

**概要**: 市場全体の過熱度・売られすぎを定量化し、S&P500のタイミング投資を支援

**主要機能**:
- Fear & Greed Index の独自実装
- VIX、Put/Call Ratio、騰落レシオなどの統合ダッシュボード
- 過去の暴落パターンとの類似度分析
- 買い時・売り時のシグナル通知

**技術スタック**:
- Frontend: Next.js + TypeScript
- Backend: Python (FastAPI)
- Data Pipeline: Airflow / Prefect
- DB: PostgreSQL + TimescaleDB

**差別化ポイント**:
- 既存の感覚的なタイミング判断を数値化・可視化
- 過去の自分の成功パターンを学習させる機能

---

### 案3: Hybrid Analyzer（推奨）

**概要**: 案1と案2を統合し、マーケットタイミング + 個別株エントリーの両方を支援

**コンセプト**:
```
市場全体が「買い時」の時に、CAN-SLIM条件を満たす銘柄の
最適エントリーポイントを提示する
```

**主要機能**:

#### Phase 1: Market Timing Module
- マーケット全体の状態判定（Risk-on / Risk-off）
- 暴落検知・回復フェーズ判定
- ポジションサイズ推奨（市場状態に応じた資金配分）

#### Phase 2: Stock Screening Module
- CAN-SLIM条件スクリーニング
  - C: Current Quarterly Earnings（四半期EPS成長率）
  - A: Annual Earnings Growth（年間EPS成長率）
  - N: New Products/Management/Price Highs
  - S: Supply and Demand（出来高・浮動株）
  - L: Leader or Laggard（RS Rating）
  - I: Institutional Sponsorship（機関投資家保有）
  - M: Market Direction

#### Phase 3: Entry Point Detection
- チャートパターン認識（CNN/Vision Transformer）
- ピボットポイント算出
- リスク/リワード比の自動計算
- 損切りライン提案

#### Phase 4: Portfolio & Risk Management
- ポジション管理
- 損切り・利確のアラート
- パフォーマンストラッキング

**技術アーキテクチャ**:
```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│              Next.js + TypeScript                │
│         (Dashboard, Charts, Alerts)              │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│                   Backend                        │
│                Python FastAPI                    │
├─────────────────────────────────────────────────┤
│  Market Analysis  │  Screener  │  ML Pipeline   │
│     Service       │   Service  │    Service     │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│                 Data Layer                       │
│  PostgreSQL + TimescaleDB │ Redis (Cache)       │
└─────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│               External APIs                      │
│  Yahoo Finance │ Alpha Vantage │ SEC EDGAR      │
└─────────────────────────────────────────────────┘
```

---

## MVP（最小限の実装範囲）

### MVP for 案3
1. S&P500の市場状態ダッシュボード（VIX、騰落レシオ等）
2. 基本的なCAN-SLIMスクリーニング（EPS成長率、RS Rating）
3. 選択銘柄のチャート表示 + 手動でのピボットポイント設定
4. ウォッチリスト機能

---

## 次のステップ
1. MVPの詳細設計
2. データソースの調査・選定
3. 技術的なPoCの実施（特にチャートパターン認識のML部分）

---

## 参考リソース
- 「オニールの成長株発掘法」- William J. O'Neil
- IBD (Investor's Business Daily)
- TradingView Pine Script（チャート分析の参考）
