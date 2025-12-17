# API設計

## 共通仕様

### Base URL

```
http://localhost:8000/api
```

### レスポンス形式

すべてのAPIは統一されたレスポンス形式を返す。

**成功時**:
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

**エラー時**:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid symbol format"
  }
}
```

### エラーコード

| コード | HTTPステータス | 説明 |
|-------|---------------|------|
| VALIDATION_ERROR | 400 | リクエストパラメータ不正 |
| NOT_FOUND | 404 | リソースが見つからない |
| EXTERNAL_API_ERROR | 502 | 外部APIエラー |
| INTERNAL_ERROR | 500 | サーバー内部エラー |

---

## Market API

### GET /api/market/status

マーケット全体の現在の状態を取得

**Response**:
```json
{
  "success": true,
  "data": {
    "status": "risk_on",
    "confidence": 0.75,
    "indicators": {
      "vix": 15.2,
      "vix_signal": "bullish",
      "put_call_ratio": 0.82,
      "put_call_signal": "neutral",
      "advance_decline": 1.8,
      "advance_decline_signal": "bullish",
      "sp500_rsi": 62.5,
      "sp500_above_200ma": true
    },
    "recommendation": "市場環境は良好。個別株のエントリー検討可。",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### GET /api/market/indicators

各指標の詳細値を取得

**Response**:
```json
{
  "success": true,
  "data": {
    "vix": {
      "value": 15.2,
      "change": -1.3,
      "change_percent": -7.88,
      "signal": "bullish",
      "thresholds": {
        "bullish": "< 20",
        "bearish": "> 30"
      }
    },
    "put_call_ratio": {
      "value": 0.82,
      "signal": "neutral"
    },
    "advance_decline": {
      "advancing": 320,
      "declining": 180,
      "ratio": 1.78,
      "signal": "bullish"
    },
    "sp500": {
      "price": 4850.50,
      "rsi": 62.5,
      "above_200ma": true,
      "distance_from_200ma": 8.5
    }
  }
}
```

### GET /api/market/history

マーケット状態の履歴を取得

**Query Parameters**:
| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| days | int | No | 30 | 取得日数 |

**Response**:
```json
{
  "success": true,
  "data": {
    "history": [
      {
        "date": "2024-01-15",
        "status": "risk_on",
        "vix": 15.2,
        "sp500_close": 4850.50
      }
    ]
  }
}
```

---

## Screener API

### GET /api/screener/canslim

CAN-SLIM条件を満たす銘柄を取得

**Query Parameters**:
| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| min_eps_growth | float | No | 25 | 最小EPS成長率(%) |
| min_rs_rating | float | No | 80 | 最小RS Rating |
| max_distance_from_high | float | No | 15 | 高値からの最大乖離(%) |
| min_volume_ratio | float | No | 1.5 | 最小出来高倍率 |
| limit | int | No | 50 | 取得件数 |
| offset | int | No | 0 | オフセット |

**Response**:
```json
{
  "success": true,
  "data": {
    "count": 15,
    "total": 15,
    "stocks": [
      {
        "symbol": "NVDA",
        "name": "NVIDIA Corporation",
        "price": 450.00,
        "change_percent": 2.5,
        "eps_growth_q": 122.5,
        "eps_growth_y": 85.3,
        "rs_rating": 98,
        "volume_ratio": 1.8,
        "distance_from_high": -5.2,
        "industry": "Semiconductors",
        "market_cap": "1.1T",
        "canslim_score": 95
      }
    ],
    "screened_at": "2024-01-15T10:00:00Z"
  }
}
```

### GET /api/screener/filters

現在のフィルター設定を取得

**Response**:
```json
{
  "success": true,
  "data": {
    "filters": {
      "min_eps_growth": 25,
      "min_rs_rating": 80,
      "max_distance_from_high": 15,
      "min_volume_ratio": 1.5,
      "min_market_cap": 1000000000
    }
  }
}
```

### POST /api/screener/custom

カスタム条件でスクリーニング

**Request Body**:
```json
{
  "filters": {
    "min_eps_growth": 30,
    "min_rs_rating": 90,
    "industries": ["Technology", "Healthcare"]
  }
}
```

---

## Data API

### GET /api/data/quote/{symbol}

リアルタイム株価を取得

**Path Parameters**:
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| symbol | string | 銘柄シンボル（例: AAPL） |

**Response**:
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "price": 185.50,
    "change": 2.30,
    "change_percent": 1.26,
    "open": 183.20,
    "high": 186.00,
    "low": 182.50,
    "volume": 52000000,
    "market_cap": "2.9T",
    "pe_ratio": 28.5,
    "52w_high": 199.62,
    "52w_low": 143.90,
    "updated_at": "2024-01-15T16:00:00Z"
  }
}
```

### GET /api/data/history/{symbol}

過去株価（OHLCV）を取得

**Path Parameters**:
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| symbol | string | 銘柄シンボル |

**Query Parameters**:
| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| period | string | No | 1y | 期間（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y） |
| interval | string | No | 1d | 間隔（1d, 1wk, 1mo） |

**Response**:
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "period": "1y",
    "interval": "1d",
    "history": [
      {
        "date": "2024-01-15",
        "open": 182.50,
        "high": 185.20,
        "low": 181.80,
        "close": 184.90,
        "volume": 52000000
      }
    ]
  }
}
```

### GET /api/data/financials/{symbol}

財務データを取得

**Response**:
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "quarterly": [
      {
        "period": "2024-Q1",
        "revenue": 119575000000,
        "net_income": 33916000000,
        "eps": 2.18,
        "eps_growth": 16.2
      }
    ],
    "annual": [
      {
        "year": 2023,
        "revenue": 383285000000,
        "net_income": 96995000000,
        "eps": 6.13,
        "eps_growth": 8.5
      }
    ]
  }
}
```

### GET /api/data/fundamentals/{symbol}

ファンダメンタル指標を取得

**Response**:
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "pe_ratio": 28.5,
    "forward_pe": 25.2,
    "peg_ratio": 2.1,
    "price_to_book": 45.3,
    "price_to_sales": 7.2,
    "debt_to_equity": 1.8,
    "roe": 147.5,
    "eps_growth_quarterly": 16.2,
    "eps_growth_annual": 8.5,
    "revenue_growth": 2.1,
    "rs_rating": 85
  }
}
```

---

## Portfolio API

### GET /api/portfolio/watchlist

ウォッチリストを取得

**Response**:
```json
{
  "success": true,
  "data": {
    "watchlist": [
      {
        "id": 1,
        "symbol": "NVDA",
        "name": "NVIDIA Corporation",
        "added_at": "2024-01-10T09:00:00Z",
        "target_entry_price": 440.00,
        "stop_loss_price": 410.00,
        "current_price": 450.00,
        "notes": "カップウィズハンドル形成中"
      }
    ]
  }
}
```

### POST /api/portfolio/watchlist

ウォッチリストに銘柄追加

**Request Body**:
```json
{
  "symbol": "NVDA",
  "target_entry_price": 440.00,
  "stop_loss_price": 410.00,
  "notes": "カップウィズハンドル形成中"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "symbol": "NVDA",
    "added_at": "2024-01-10T09:00:00Z"
  }
}
```

### DELETE /api/portfolio/watchlist/{symbol}

ウォッチリストから銘柄削除

### GET /api/portfolio/trades

ペーパートレード履歴を取得

**Query Parameters**:
| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| limit | int | No | 50 | 取得件数 |
| offset | int | No | 0 | オフセット |

**Response**:
```json
{
  "success": true,
  "data": {
    "trades": [
      {
        "id": 1,
        "symbol": "AAPL",
        "trade_type": "buy",
        "quantity": 10,
        "price": 180.00,
        "traded_at": "2024-01-05T10:30:00Z",
        "notes": "ブレイクアウトでエントリー"
      },
      {
        "id": 2,
        "symbol": "AAPL",
        "trade_type": "sell",
        "quantity": 10,
        "price": 195.00,
        "traded_at": "2024-01-15T14:00:00Z",
        "notes": "目標価格到達"
      }
    ]
  }
}
```

### POST /api/portfolio/trades

ペーパートレードを記録

**Request Body**:
```json
{
  "symbol": "AAPL",
  "trade_type": "buy",
  "quantity": 10,
  "price": 180.00,
  "traded_at": "2024-01-05T10:30:00Z",
  "notes": "ブレイクアウトでエントリー"
}
```

### GET /api/portfolio/performance

パフォーマンス集計を取得

**Query Parameters**:
| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| period | string | No | all | 集計期間（1m, 3m, 6m, 1y, all） |

**Response**:
```json
{
  "success": true,
  "data": {
    "period": "all",
    "metrics": {
      "total_trades": 25,
      "winning_trades": 18,
      "losing_trades": 7,
      "win_rate": 72.0,
      "average_return": 8.5,
      "total_return": 42.5,
      "max_drawdown": -12.3,
      "profit_factor": 2.8,
      "average_holding_days": 15
    },
    "by_symbol": [
      {
        "symbol": "NVDA",
        "trades": 5,
        "total_return": 25.3,
        "win_rate": 80.0
      }
    ]
  }
}
```

---

## ML API（Phase 2以降）

### POST /api/ml/detect-pattern

チャートパターンを検出

**Request Body**:
```json
{
  "symbol": "NVDA",
  "period": "6mo"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "symbol": "NVDA",
    "patterns": [
      {
        "type": "cup_with_handle",
        "confidence": 0.85,
        "start_date": "2023-10-01",
        "end_date": "2024-01-10",
        "pivot_point": 450.00,
        "buy_zone": {
          "min": 450.00,
          "max": 472.50
        }
      }
    ]
  }
}
```

### GET /api/ml/entry-point/{symbol}

エントリーポイント提案を取得

**Response**:
```json
{
  "success": true,
  "data": {
    "symbol": "NVDA",
    "current_price": 448.00,
    "recommendation": "wait",
    "entry_point": {
      "price": 450.00,
      "type": "breakout",
      "pattern": "cup_with_handle"
    },
    "stop_loss": 418.50,
    "target_prices": [
      { "price": 495.00, "reason": "10% profit target" },
      { "price": 540.00, "reason": "20% profit target" }
    ],
    "risk_reward_ratio": 3.2
  }
}
```
