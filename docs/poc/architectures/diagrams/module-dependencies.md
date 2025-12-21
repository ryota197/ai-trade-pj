# モジュール依存関係図

## 概要

バックエンド・フロントエンドの各モジュール間の依存関係を可視化。

---

## システム全体構成

```mermaid
graph TB
    subgraph "Client"
        Browser[Browser<br/>localhost:3000]
    end

    subgraph "Frontend - Next.js"
        Pages[Pages]
        Components[Components]
        Hooks[Hooks]
        API_Client[API Client]
    end

    subgraph "Backend - FastAPI"
        Controllers[Controllers]
        UseCases[Use Cases]
        DomainServices[Domain Services]
        Repositories[Repositories]
        Gateways[Gateways]
    end

    subgraph "External"
        PostgreSQL[(PostgreSQL<br/>localhost:5432)]
        YFinance[yfinance API]
    end

    Browser --> Pages
    Pages --> Components
    Pages --> Hooks
    Hooks --> API_Client
    API_Client -->|REST API| Controllers
    Controllers --> UseCases
    UseCases --> DomainServices
    UseCases --> Repositories
    UseCases --> Gateways
    Repositories --> PostgreSQL
    Gateways --> YFinance
```

---

## バックエンド レイヤー構成

```mermaid
graph TB
    subgraph "Presentation Layer"
        direction LR
        P1[screener_controller]
        P2[market_controller]
        P3[data_controller]
        P4[health_controller]
        P5[dependencies]
    end

    subgraph "Application Layer"
        direction LR
        A1[ScreenCANSLIMStocksUseCase]
        A2[GetStockDetailUseCase]
        A3[GetMarketStatusUseCase]
        A4[GetMarketIndicatorsUseCase]
        A5[GetFinancialMetricsUseCase]
    end

    subgraph "Domain Layer"
        direction LR
        D1[Stock Entity]
        D2[MarketStatus Entity]
        D3[CANSLIMScore VO]
        D5[MarketAnalyzer Service]
        D6[RSRatingCalculator Service]
        D7[EPSGrowthCalculator Service]
    end

    subgraph "Infrastructure Layer"
        direction LR
        I1[PostgresScreenerRepository]
        I2[StockModelMapper]
        I3[YFinanceGateway]
        I4[YFinanceMarketDataGateway]
    end

    P1 & P2 & P3 --> A1 & A2 & A3 & A4 & A5
    A1 & A2 & A3 & A4 --> D1 & D2 & D5 & D6
    A5 --> D7
    A1 & A2 --> I1
    A3 & A4 --> I4
    A5 --> I3
    I1 --> I2
    I1 --> External_DB[(PostgreSQL)]
    I3 & I4 --> External_API[yfinance]
```

---

## バックエンド詳細依存関係

```mermaid
graph LR
    subgraph "Presentation"
        screener_ctrl[screener_controller]
        market_ctrl[market_controller]
        data_ctrl[data_controller]
        deps[dependencies]
    end

    subgraph "Application"
        screen_uc[ScreenCANSLIMStocksUseCase]
        detail_uc[GetStockDetailUseCase]
        status_uc[GetMarketStatusUseCase]
        indicators_uc[GetMarketIndicatorsUseCase]
        financials_uc[GetFinancialMetricsUseCase]
    end

    subgraph "Domain"
        stock[Stock]
        market_status[MarketStatus]
        canslim[CANSLIMScore]
        analyzer[MarketAnalyzer]
        rs_calc[RSRatingCalculator]
        eps_calc[EPSGrowthCalculator]
        stock_repo_if[StockRepository IF]
        market_repo_if[MarketDataRepository IF]
    end

    subgraph "Infrastructure"
        pg_screener[PostgresScreenerRepository]
        stock_mapper[StockModelMapper]
        yf_gateway[YFinanceGateway]
        yf_market[YFinanceMarketDataGateway]
    end

    %% Presentation → Application
    screener_ctrl --> screen_uc
    screener_ctrl --> detail_uc
    market_ctrl --> status_uc
    market_ctrl --> indicators_uc
    data_ctrl --> financials_uc
    deps --> screen_uc & detail_uc & status_uc & indicators_uc & financials_uc

    %% Application → Domain
    screen_uc --> stock & canslim & rs_calc & stock_repo_if
    detail_uc --> stock & stock_repo_if
    status_uc --> market_status & analyzer & market_repo_if
    indicators_uc --> market_repo_if
    financials_uc --> eps_calc

    %% Infrastructure implements Domain interfaces
    pg_screener -.->|implements| stock_repo_if
    yf_market -.->|implements| market_repo_if

    %% Application → Infrastructure (via DI)
    screen_uc -.->|DI| pg_screener & yf_gateway
    status_uc -.->|DI| yf_market
    financials_uc -.->|DI| yf_gateway

    %% Infrastructure internal dependencies
    pg_screener --> stock_mapper
```

---

## フロントエンド依存関係

```mermaid
graph LR
    subgraph "Pages"
        home[page.tsx /]
        screener[page.tsx /screener]
        stock_detail[page.tsx /stock/symbol]
    end

    subgraph "Components"
        subgraph "market"
            MarketDashboard
            MarketStatus
            IndicatorCard
        end
        subgraph "screener"
            StockTable
            FilterPanel
        end
        subgraph "stock"
            PriceChart
            FundamentalsCard
            CANSLIMScoreCard
        end
    end

    subgraph "Hooks"
        useMarketStatus
        useScreener
        useStockData
    end

    subgraph "Lib"
        api[api.ts]
    end

    %% Pages → Components
    home --> MarketDashboard
    screener --> StockTable & FilterPanel
    stock_detail --> PriceChart & FundamentalsCard & CANSLIMScoreCard

    %% Components → Hooks
    MarketDashboard --> useMarketStatus
    screener --> useScreener
    stock_detail --> useStockData

    %% Hooks → API
    useMarketStatus --> api
    useScreener --> api
    useStockData --> api
```

---

## 依存の方向

| レイヤー | 依存先 | 備考 |
|---------|--------|------|
| Presentation | Application | UseCaseを呼び出す |
| Application | Domain | Entity, VO, Serviceを使用 |
| Application | Infrastructure (via DI) | RepositoryとGatewayの実装を注入 |
| Infrastructure | Domain | Repository IFを実装 |

**依存ルール**: 外側 → 内側（Presentation → Application → Domain ← Infrastructure）
