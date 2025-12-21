# クラス図

## 概要

主要なクラス・インターフェースの構造と関係を可視化。

---

## 1. Domain Layer

### Entities & Value Objects

```mermaid
classDiagram
    class Stock {
        +symbol: str
        +name: str
        +price: float
        +change_percent: float
        +volume: int
        +avg_volume: int
        +market_cap: float?
        +pe_ratio: float?
        +week_52_high: float
        +week_52_low: float
        +eps_growth_quarterly: float?
        +eps_growth_annual: float?
        +rs_rating: int
        +institutional_ownership: float?
        +canslim_score: CANSLIMScore?
        +updated_at: datetime
        +volume_ratio() float
        +distance_from_52w_high() float
        +is_near_52w_high() bool
        +has_strong_eps_growth() bool
    }

    class StockSummary {
        +symbol: str
        +name: str
        +price: float
        +change_percent: float
        +rs_rating: int
        +canslim_total_score: int
    }

    class CANSLIMScore {
        +total_score: int
        +overall_grade: str
        +passing_count: int
        +c_score: CANSLIMCriteria
        +a_score: CANSLIMCriteria
        +n_score: CANSLIMCriteria
        +s_score: CANSLIMCriteria
        +l_score: CANSLIMCriteria
        +i_score: CANSLIMCriteria
        +calculate()$ CANSLIMScore
    }

    class CANSLIMCriteria {
        +name: str
        +score: int
        +grade: str
        +value: float?
        +threshold: float
        +description: str
    }

    Stock --> CANSLIMScore
    CANSLIMScore --> CANSLIMCriteria
```

### Market関連

```mermaid
classDiagram
    class MarketStatus {
        +condition: MarketCondition
        +confidence: float
        +score: int
        +recommendation: str
        +recorded_at: datetime
    }

    class MarketCondition {
        <<enumeration>>
        RISK_ON
        RISK_OFF
        NEUTRAL
    }

    class MarketIndicators {
        +vix: VIXIndicator
        +sp500_rsi: RSIIndicator
        +put_call_ratio: PutCallIndicator
        +sp500_ma200: MA200Indicator
        +timestamp: datetime
    }

    class VIXIndicator {
        +value: float
        +signal: str
    }

    MarketStatus --> MarketCondition
    MarketIndicators --> VIXIndicator
```

---

## 2. Domain Services

```mermaid
classDiagram
    class MarketAnalyzer {
        +analyze(indicators: MarketIndicators) MarketStatus
        -_calculate_score(indicators) int
        -_determine_condition(score) MarketCondition
        -_generate_recommendation(condition, indicators) str
    }

    class RSRatingCalculator {
        +calculate_single(symbol, stock_prices, benchmark_prices) RSRatingResult
        +calculate_bulk(symbols, price_data, benchmark_prices) list~RSRatingResult~
        -_calculate_relative_strength(stock, benchmark) float
    }

    class RSRatingResult {
        +symbol: str
        +rs_rating: int
        +relative_strength: float
    }

    class EPSGrowthCalculator {
        +calculate(eps_data: EPSData)$ EPSGrowthResult
        +calculate_quarterly_growth(eps_data: EPSData)$ float?
        +calculate_annual_growth(eps_data: EPSData)$ float?
    }

    class EPSData {
        +quarterly_eps: list~float~
        +annual_eps: list~float~
    }

    class EPSGrowthResult {
        +quarterly_growth: float?
        +annual_growth: float?
    }

    RSRatingCalculator --> RSRatingResult
    EPSGrowthCalculator --> EPSData
    EPSGrowthCalculator --> EPSGrowthResult
```

---

## 3. Repository Interfaces

```mermaid
classDiagram
    class StockRepository {
        <<interface>>
        +get_by_symbol(symbol: str) Stock?
        +get_by_symbols(symbols: list) list~Stock~
        +screen(filter, limit, offset) ScreenerResult
        +save(stock: Stock) void
        +save_many(stocks: list) void
        +delete_by_symbol(symbol: str) bool
        +get_all_symbols() list~str~
    }

    class MarketDataRepository {
        <<interface>>
        +get_vix() float
        +get_sp500_data() SP500Data
        +get_put_call_ratio() float
        +get_market_indicators() MarketIndicators
    }

    class ScreenerFilter {
        +min_rs_rating: int
        +min_eps_growth_quarterly: float
        +min_eps_growth_annual: float
        +max_distance_from_52w_high: float
        +min_volume_ratio: float
        +min_canslim_score: int
        +min_market_cap: float?
        +max_market_cap: float?
        +symbols: list?
    }

    class ScreenerResult {
        +total_count: int
        +stocks: list~StockSummary~
    }

    StockRepository --> ScreenerFilter
    StockRepository --> ScreenerResult
```

---

## 4. Application Layer (Use Cases)

```mermaid
classDiagram
    class ScreenCANSLIMStocksUseCase {
        -_stock_repo: StockRepository
        -_financial_gateway: FinancialDataGateway
        -_rs_calculator: RSRatingCalculator
        +execute(filter_input) ScreenerResultOutput
        +refresh_stock_data(symbols) int
    }

    class GetStockDetailUseCase {
        -_stock_repo: StockRepository
        +execute(input) StockDetailOutput?
    }

    class GetMarketStatusUseCase {
        -_market_data_repo: MarketDataRepository
        -_market_analyzer: MarketAnalyzer
        +execute() MarketStatusOutput
    }

    class GetMarketIndicatorsUseCase {
        -_market_data_repo: MarketDataRepository
        +execute() MarketIndicatorsOutput
    }

    class GetFinancialMetricsUseCase {
        -_gateway: FinancialDataGateway
        -_eps_calculator: EPSGrowthCalculator
        +execute(symbol: str) FinancialMetrics?
    }

    class FinancialDataGateway {
        <<interface>>
        +get_quote(symbol) Quote?
        +get_quotes(symbols) dict
        +get_price_history(symbol) list~HistoricalBar~
        +get_raw_financials(symbol) RawFinancialData?
        +get_financial_metrics(symbol) FinancialMetrics?
        +get_sp500_history(period) list~HistoricalBar~
    }

    class RawFinancialData {
        +symbol: str
        +quarterly_eps: list~float~
        +annual_eps: list~float~
        +eps_ttm: float?
        +revenue_growth: float?
        +profit_margin: float?
        +roe: float?
        +debt_to_equity: float?
        +institutional_ownership: float?
    }

    ScreenCANSLIMStocksUseCase --> StockRepository
    ScreenCANSLIMStocksUseCase --> FinancialDataGateway
    ScreenCANSLIMStocksUseCase --> RSRatingCalculator
    GetStockDetailUseCase --> StockRepository
    GetMarketStatusUseCase --> MarketDataRepository
    GetMarketStatusUseCase --> MarketAnalyzer
    GetMarketIndicatorsUseCase --> MarketDataRepository
    GetFinancialMetricsUseCase --> FinancialDataGateway
    GetFinancialMetricsUseCase --> EPSGrowthCalculator
    FinancialDataGateway --> RawFinancialData
```

---

## 5. Infrastructure Layer

### Repositories

```mermaid
classDiagram
    class PostgresScreenerRepository {
        -_session: Session
        +get_by_symbol(symbol) Stock?
        +get_by_symbols(symbols) list~Stock~
        +screen(filter, limit, offset) ScreenerResult
        +save(stock) void
        +save_many(stocks) void
        +delete_by_symbol(symbol) bool
        +get_all_symbols() list~str~
        -_model_to_entity(model) Stock
        -_calc_distance_from_high(price, high) float
    }

    class ScreenerResultModel {
        +id: int
        +symbol: str
        +name: str
        +price: Decimal
        +change_percent: Decimal
        +volume: int
        +avg_volume: int
        +market_cap: Decimal?
        +pe_ratio: Decimal?
        +week_52_high: Decimal
        +week_52_low: Decimal
        +eps_growth_quarterly: Decimal?
        +eps_growth_annual: Decimal?
        +rs_rating: int
        +institutional_ownership: Decimal?
        +canslim_total_score: int
        +canslim_detail: str?
        +updated_at: datetime
        +created_at: datetime
    }

    PostgresScreenerRepository --> ScreenerResultModel
    PostgresScreenerRepository ..|> StockRepository
```

### Gateways

```mermaid
classDiagram
    class YFinanceGateway {
        +get_quote(symbol) Quote?
        +get_quotes(symbols) dict
        +get_price_history(symbol, period, interval) list~HistoricalBar~
        +get_financial_metrics(symbol) FinancialMetrics?
        +get_sp500_history(period) list~HistoricalBar~
        +get_quote_sync(symbol) Quote
        +get_history_sync(symbol, period, interval) list~HistoricalPrice~
    }

    class YFinanceMarketDataGateway {
        +get_vix() float
        +get_sp500_data() SP500Data
        +get_put_call_ratio() float
        +get_market_indicators() MarketIndicators
        -_calculate_rsi(prices, period) float
    }

    YFinanceGateway ..|> FinancialDataGateway
    YFinanceMarketDataGateway ..|> MarketDataRepository
```

---

## 6. 全体の継承・実装関係

```mermaid
classDiagram
    %% Interfaces
    class StockRepository {
        <<interface>>
    }
    class MarketDataRepository {
        <<interface>>
    }
    class FinancialDataGateway {
        <<interface>>
    }

    %% Implementations
    class PostgresScreenerRepository
    class YFinanceMarketDataGateway
    class YFinanceGateway

    %% Relationships
    PostgresScreenerRepository ..|> StockRepository : implements
    YFinanceMarketDataGateway ..|> MarketDataRepository : implements
    YFinanceGateway ..|> FinancialDataGateway : implements

    %% Use Cases using interfaces
    class ScreenCANSLIMStocksUseCase
    class GetMarketStatusUseCase

    ScreenCANSLIMStocksUseCase --> StockRepository : uses
    ScreenCANSLIMStocksUseCase --> FinancialDataGateway : uses
    GetMarketStatusUseCase --> MarketDataRepository : uses
```
