# スコアリングルール

## 概要

本システムでは、投資判断を支援するために複数のスコアリングシステムを使用する。
各スコアは明確なルールに基づいて計算され、透明性と再現性を確保する。

---

## スコアリングシステム一覧

| スコア名 | 目的 | 範囲 | 使用場面 |
|---------|------|------|----------|
| Market Score | 市場環境判定 | -5 〜 +5 | Market Module |
| CAN-SLIM Score | 銘柄評価 | 0 〜 100 | Screener Module |
| RS Rating | 相対強度 | 0 〜 100 | Screener Module |

---

## 1. Market Score（市場環境スコア）

### 目的

市場全体の環境を数値化し、Risk On/Off/Neutral を判定する。

### 構成要素

| 指標 | 重み | Bullish | Neutral | Bearish |
|------|------|---------|---------|---------|
| VIX | ±2 | < 20 | 20-30 | > 30 |
| S&P500 RSI | ±1 | 30-70 | - | <30 or >70 |
| S&P500 vs 200MA | ±1 | 上回る | - | 下回る |
| Put/Call Ratio | ±1 | > 1.0 | 0.7-1.0 | < 0.7 |

### 計算式

```python
market_score = vix_score + rsi_score + ma_score + pc_ratio_score
# 範囲: -5 〜 +5
```

### 判定閾値

```python
if market_score >= 3:
    condition = RISK_ON
elif market_score <= -2:
    condition = RISK_OFF
else:
    condition = NEUTRAL
```

### 設計根拠

**非対称閾値の理由**:
- Risk On: +3（5指標中3つ以上が強気）→ 高い確信が必要
- Risk Off: -2（5指標中2つ以上が弱気）→ 早めに警戒

これは「損失回避」を優先する設計。上昇機会を逃すリスクより、下落に巻き込まれるリスクを重視。

---

## 2. CAN-SLIM Score（銘柄評価スコア）

### 目的

個別銘柄がCAN-SLIM条件をどの程度満たしているかを数値化する。

### 構成要素

| 要素 | 配点 | 条件 |
|------|------|------|
| C (Current Earnings) | 20点 | 四半期EPS成長率 ≥ 25% |
| A (Annual Earnings) | 20点 | 年間EPS成長率 ≥ 25% |
| N (New Highs) | 15点 | 52週高値の90%以上 |
| S (Supply/Demand) | 15点 | 出来高比率 ≥ 1.5 |
| L (Leader) | 20点 | RS Rating ≥ 80 |
| I (Institutional) | 10点 | 機関保有あり |
| M (Market) | - | 別途Market Scoreで評価 |

### 計算式

```python
canslim_score = 0

# C: Current Quarterly Earnings
if eps_growth_q >= 25:
    canslim_score += 20
elif eps_growth_q >= 15:
    canslim_score += 10

# A: Annual Earnings Growth
if eps_growth_annual >= 25:
    canslim_score += 20
elif eps_growth_annual >= 15:
    canslim_score += 10

# N: New Highs
high_ratio = current_price / week_52_high
if high_ratio >= 0.95:
    canslim_score += 15
elif high_ratio >= 0.90:
    canslim_score += 10

# S: Supply and Demand
if volume_ratio >= 1.5:
    canslim_score += 15
elif volume_ratio >= 1.2:
    canslim_score += 8

# L: Leader
if rs_rating >= 80:
    canslim_score += 20
elif rs_rating >= 70:
    canslim_score += 10

# I: Institutional
if institutional_holding > 0:
    canslim_score += 10

# 範囲: 0 〜 100
```

### 判定閾値

| スコア | 評価 | 推奨アクション |
|--------|------|---------------|
| 80-100 | A（優良） | 積極的にエントリー検討 |
| 60-79 | B（良好） | 条件付きでエントリー検討 |
| 40-59 | C（普通） | ウォッチリストに追加 |
| 0-39 | D（不合格） | 見送り |

---

## 3. RS Rating（相対強度レーティング）

### 目的

銘柄のパフォーマンスを市場全体と比較し、相対的な強さを評価する。

### 計算式（簡易版 - PoC用）

```python
# 12ヶ月リターンを計算
stock_return = (current_price - price_12m_ago) / price_12m_ago
market_return = (sp500_current - sp500_12m_ago) / sp500_12m_ago

# 相対強度
relative_strength = stock_return / market_return

# 正規化（0-100）
# 簡易的に、RS 0.5〜2.0 を 0〜100 にマッピング
rs_rating = min(100, max(0, (relative_strength - 0.5) / 1.5 * 100))
```

### 計算式（本格版 - 将来実装）

```python
# 全銘柄のリターンを計算
all_returns = [calculate_return(stock) for stock in universe]

# パーセンタイル順位を計算
rs_rating = percentile_rank(stock_return, all_returns)
# 範囲: 0 〜 99（上位1%が99）
```

### 判定閾値

| RS Rating | 評価 | 意味 |
|-----------|------|------|
| 90-99 | 最強 | 上位10%、真の主導株 |
| 80-89 | 強い | 上位20%、主導株候補 |
| 70-79 | 平均以上 | 市場平均を上回る |
| 50-69 | 平均 | 市場並み |
| 0-49 | 弱い | 市場平均以下、出遅れ株 |

---

## スコアの組み合わせ

### スクリーニング優先度

```
1. Market Score (Risk On/Neutral のみ通過)
      ↓
2. CAN-SLIM Score (60点以上のみ通過)
      ↓
3. RS Rating でソート (高い順)
```

### 総合判定マトリクス

| Market | CAN-SLIM | RS Rating | 推奨 |
|--------|----------|-----------|------|
| Risk On | A (80+) | 80+ | 強く推奨 |
| Risk On | B (60-79) | 70+ | 推奨 |
| Neutral | A (80+) | 80+ | 条件付き推奨 |
| Neutral | B (60-79) | - | ウォッチ |
| Risk Off | - | - | 見送り |

---

## スコア更新頻度

| スコア | 更新頻度 | 理由 |
|--------|----------|------|
| Market Score | 1時間ごと | 市場環境は頻繁に変化 |
| CAN-SLIM Score | 1日1回 | 財務データは日次で十分 |
| RS Rating | 1日1回 | 価格データベース |

---

## エッジケース処理

### データ欠損時

| 状況 | 処理 |
|------|------|
| EPS成長率が計算不可 | 該当要素のスコア = 0 |
| 52週高値がない | 現在価格 = 52週高値として計算 |
| 出来高データなし | 出来高比率 = 1.0（中立） |

### 異常値

| 状況 | 処理 |
|------|------|
| EPS成長率 > 1000% | 上限 1000% でキャップ |
| RS Rating 計算で0除算 | RS Rating = 50（中立） |
| VIX > 80（極端な恐怖） | 最大スコア -2 のまま |

---

## 実装コード参照

- Market Score: `backend/src/domain/services/market_analyzer.py`
- CAN-SLIM Score: `backend/src/domain/value_objects/canslim_score.py`（Phase 3）
- RS Rating: `backend/src/domain/services/rs_calculator.py`（Phase 3）
