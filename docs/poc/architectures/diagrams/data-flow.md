# データフロー図

## 概要

主要機能のリクエスト/レスポンスの流れをシーケンス図で可視化。

---

## 1. スクリーニング機能

`/screener` ページでCAN-SLIM条件の銘柄一覧を取得するフロー。

```mermaid
sequenceDiagram
    participant Browser
    participant ScreenerPage
    participant useScreener
    participant API as api.ts
    participant Controller as screener_controller
    participant UseCase as ScreenCANSLIMStocksUseCase
    participant Repository as PostgresScreenerRepository
    participant DB as PostgreSQL

    Browser->>ScreenerPage: アクセス
    ScreenerPage->>useScreener: フック呼び出し
    useScreener->>API: screenStocks(filter)
    API->>Controller: GET /api/screener/canslim
    Controller->>UseCase: execute(filter_input)
    UseCase->>Repository: screen(filter, limit, offset)
    Repository->>DB: SELECT ... WHERE ...
    DB-->>Repository: rows
    Repository-->>UseCase: ScreenerResult
    UseCase-->>Controller: ScreenerResultOutput
    Controller-->>API: ApiResponse<ScreenerResponse>
    API-->>useScreener: response
    useScreener-->>ScreenerPage: { stocks, isLoading }
    ScreenerPage-->>Browser: 銘柄一覧表示
```

---

## 2. 銘柄詳細ページ

`/stock/[symbol]` ページで株価・財務データを取得するフロー。

```mermaid
sequenceDiagram
    participant Browser
    participant StockPage as /stock/[symbol]
    participant useStockData
    participant API as api.ts
    participant DataCtrl as data_controller
    participant YFinance as YFinanceGateway

    Browser->>StockPage: /stock/AAPL アクセス
    StockPage->>useStockData: useStockData("AAPL")

    par 並列リクエスト
        useStockData->>API: getQuote("AAPL")
        API->>DataCtrl: GET /api/data/quote/AAPL
        DataCtrl->>YFinance: get_quote_sync("AAPL")
        YFinance-->>DataCtrl: Quote
        DataCtrl-->>API: ApiResponse
        API-->>useStockData: quote
    and
        useStockData->>API: getPriceHistory("AAPL")
        API->>DataCtrl: GET /api/data/history/AAPL
        DataCtrl->>YFinance: get_history_sync("AAPL")
        YFinance-->>DataCtrl: HistoricalPrice[]
        DataCtrl-->>API: ApiResponse
        API-->>useStockData: priceHistory
    and
        useStockData->>API: getFinancials("AAPL")
        API->>DataCtrl: GET /api/data/financials/AAPL
        DataCtrl->>YFinance: get_financial_metrics("AAPL")
        YFinance-->>DataCtrl: FinancialMetrics
        DataCtrl-->>API: ApiResponse
        API-->>useStockData: financials
    end

    useStockData-->>StockPage: { quote, priceHistory, financials }
    StockPage-->>Browser: チャート・財務データ表示
```

---

## 3. マーケット状態取得

ダッシュボードでマーケット状態（Risk On/Off）を取得するフロー。

```mermaid
sequenceDiagram
    participant Browser
    participant Dashboard as MarketDashboard
    participant Hook as useMarketStatus
    participant API as api.ts
    participant Controller as market_controller
    participant UseCase as GetMarketStatusUseCase
    participant Gateway as YFinanceMarketDataGateway
    participant Analyzer as MarketAnalyzer
    participant YFinance as yfinance

    Browser->>Dashboard: ダッシュボード表示
    Dashboard->>Hook: useMarketStatus()
    Hook->>API: getMarketStatus()
    API->>Controller: GET /api/market/status
    Controller->>UseCase: execute()
    UseCase->>Gateway: get_vix()
    Gateway->>YFinance: yf.Ticker("^VIX")
    YFinance-->>Gateway: VIX data
    UseCase->>Gateway: get_sp500_data()
    Gateway->>YFinance: yf.Ticker("^GSPC")
    YFinance-->>Gateway: S&P500 data
    UseCase->>Gateway: get_put_call_ratio()
    Gateway-->>UseCase: MarketIndicators
    UseCase->>Analyzer: analyze(indicators)
    Analyzer-->>UseCase: MarketStatus
    UseCase-->>Controller: MarketStatusOutput
    Controller-->>API: ApiResponse
    API-->>Hook: response
    Hook-->>Dashboard: { status, indicators }
    Dashboard-->>Browser: マーケット状態表示
```

---

## 4. マーケット指標取得

個別の指標データ（VIX、RSI等）を取得するフロー。

```mermaid
sequenceDiagram
    participant Browser
    participant Dashboard as MarketDashboard
    participant Hook as useMarketStatus
    participant API as api.ts
    participant Controller as market_controller
    participant UseCase as GetMarketIndicatorsUseCase
    participant Gateway as YFinanceMarketDataGateway

    Browser->>Dashboard: ダッシュボード表示
    Dashboard->>Hook: useMarketStatus()
    Hook->>API: getMarketIndicators()
    API->>Controller: GET /api/market/indicators
    Controller->>UseCase: execute()
    UseCase->>Gateway: get_market_indicators()
    Gateway-->>UseCase: MarketIndicators
    UseCase-->>Controller: MarketIndicatorsOutput
    Controller-->>API: ApiResponse
    API-->>Hook: response
    Hook-->>Dashboard: indicators
    Dashboard-->>Browser: 指標カード表示
```

---

## 5. 財務指標取得（リファクタリング後）

`/data/financials/{symbol}` エンドポイントでEPS成長率を含む財務指標を取得するフロー。

```mermaid
sequenceDiagram
    participant Browser
    participant StockPage as /stock/[symbol]
    participant useStockData
    participant API as api.ts
    participant Controller as data_controller
    participant UseCase as GetFinancialMetricsUseCase
    participant Gateway as YFinanceGateway
    participant Calculator as EPSGrowthCalculator
    participant YFinance as yfinance

    Browser->>StockPage: /stock/AAPL アクセス
    StockPage->>useStockData: useStockData("AAPL")
    useStockData->>API: getFinancials("AAPL")
    API->>Controller: GET /api/data/financials/AAPL
    Controller->>UseCase: execute("AAPL")

    Note over UseCase: 1. 生データ取得（Infrastructure層）
    UseCase->>Gateway: get_raw_financials("AAPL")
    Gateway->>YFinance: ticker.quarterly_earnings
    YFinance-->>Gateway: quarterly EPS data
    Gateway->>YFinance: ticker.earnings
    YFinance-->>Gateway: annual EPS data
    Gateway-->>UseCase: RawFinancialData

    Note over UseCase: 2. EPS成長率計算（Domain層）
    UseCase->>Calculator: calculate(EPSData)
    Calculator-->>UseCase: EPSGrowthResult

    Note over UseCase: 3. DTO構築
    UseCase-->>Controller: FinancialMetrics
    Controller-->>API: ApiResponse
    API-->>useStockData: financials
    useStockData-->>StockPage: { financials }
    StockPage-->>Browser: 財務指標表示
```

---

## API エンドポイント対応表

| 機能 | エンドポイント | データフロー |
|------|---------------|-------------|
| スクリーニング | `GET /api/screener/canslim` | Controller → UseCase → Repository → DB |
| 銘柄詳細 | `GET /api/screener/stock/{symbol}` | Controller → UseCase → Repository |
| 株価取得 | `GET /api/data/quote/{symbol}` | Controller → Gateway → yfinance |
| 株価履歴 | `GET /api/data/history/{symbol}` | Controller → Gateway → yfinance |
| 財務指標 | `GET /api/data/financials/{symbol}` | Controller → UseCase → Gateway → Calculator |
| マーケット状態 | `GET /api/market/status` | Controller → UseCase → Gateway → Analyzer |
| マーケット指標 | `GET /api/market/indicators` | Controller → UseCase → Gateway |
