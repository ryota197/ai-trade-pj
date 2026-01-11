"""財務データゲートウェイ インターフェース"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class QuoteData:
    """株価データ"""

    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    avg_volume: int
    market_cap: float | None
    pe_ratio: float | None
    week_52_high: float
    week_52_low: float
    timestamp: datetime


@dataclass(frozen=True)
class HistoricalBar:
    """過去の株価バー"""

    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True)
class RawFinancialData:
    """
    財務生データ

    Gatewayから取得した加工前の財務データ。
    EPS成長率などの計算はDomain層のCalculatorで行う。
    """

    symbol: str
    quarterly_eps: list[float]  # 四半期EPS（新しい順）
    annual_eps: list[float]  # 年間EPS（新しい順）
    eps_ttm: float | None  # 直近12ヶ月EPS
    revenue_growth: float | None  # 売上成長率（%）
    profit_margin: float | None  # 利益率（%）
    roe: float | None  # 自己資本利益率（%）
    debt_to_equity: float | None  # 負債資本比率
    institutional_ownership: float | None  # 機関投資家保有率（%）


@dataclass(frozen=True)
class FinancialMetrics:
    """財務指標（計算済み）"""

    symbol: str
    eps_ttm: float | None  # 直近12ヶ月EPS
    eps_growth_quarterly: float | None  # 四半期EPS成長率
    eps_growth_annual: float | None  # 年間EPS成長率
    revenue_growth: float | None  # 売上成長率
    profit_margin: float | None  # 利益率
    roe: float | None  # 自己資本利益率
    debt_to_equity: float | None  # 負債資本比率
    institutional_ownership: float | None  # 機関投資家保有率


class FinancialDataGateway(ABC):
    """
    財務データゲートウェイの抽象インターフェース

    外部データソース（yfinance, FMP等）からの財務・株価データ取得を抽象化する。
    Infrastructure層で具体的な実装を提供する。
    """

    @abstractmethod
    async def get_quote(self, symbol: str) -> QuoteData | None:
        """
        現在の株価データを取得

        Args:
            symbol: ティッカーシンボル

        Returns:
            QuoteData: 株価データ、取得失敗時はNone
        """
        pass

    @abstractmethod
    async def get_quotes(self, symbols: list[str]) -> dict[str, QuoteData]:
        """
        複数銘柄の株価データを一括取得

        Args:
            symbols: ティッカーシンボルのリスト

        Returns:
            dict[str, QuoteData]: シンボル -> 株価データのマップ
        """
        pass

    @abstractmethod
    async def get_price_history(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
    ) -> list[HistoricalBar]:
        """
        株価履歴を取得

        Args:
            symbol: ティッカーシンボル
            period: 期間（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max）
            interval: 間隔（1m, 5m, 15m, 1h, 1d, 1wk, 1mo）

        Returns:
            list[HistoricalBar]: 株価バーのリスト
        """
        pass

    @abstractmethod
    async def get_raw_financials(self, symbol: str) -> RawFinancialData | None:
        """
        財務生データを取得

        EPS計算などのビジネスロジックは含まず、
        外部APIから取得した生データのみを返す。

        Args:
            symbol: ティッカーシンボル

        Returns:
            RawFinancialData: 財務生データ、取得失敗時はNone
        """
        pass

    @abstractmethod
    async def get_financial_metrics(self, symbol: str) -> FinancialMetrics | None:
        """
        財務指標を取得（計算済み）

        Args:
            symbol: ティッカーシンボル

        Returns:
            FinancialMetrics: 財務指標、取得失敗時はNone

        Deprecated:
            このメソッドはInfrastructure層でEPS計算を行うため非推奨。
            get_raw_financials() + EPSGrowthCalculator を使用してください。
        """
        pass

    @abstractmethod
    async def get_sp500_history(
        self,
        period: str = "1y",
        interval: str = "1d",
    ) -> list[HistoricalBar]:
        """
        S&P500の株価履歴を取得（RS Rating計算用）

        Args:
            period: 期間
            interval: 間隔

        Returns:
            list[HistoricalBar]: 株価バーのリスト
        """
        pass
