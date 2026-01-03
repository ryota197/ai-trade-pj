"""yfinance データ取得ゲートウェイ（統合版）"""

from datetime import datetime

import yfinance as yf

from src.application.interfaces.financial_data_gateway import (
    FinancialDataGateway,
    FinancialMetrics,
    HistoricalBar,
    QuoteData,
    RawFinancialData,
)
from src.domain.models import HistoricalPrice, Quote
from src.domain.services.eps_growth_calculator import EPSData, EPSGrowthCalculator


class YFinanceGateway(FinancialDataGateway):
    """
    yfinance を使用した財務データゲートウェイ（統合版）

    FinancialDataGateway インターフェースを実装し、
    株価・財務データを一元的に取得する。

    Note:
        - 当初 YFinanceGateway（汎用）と YFinancePriceGateway（スクリーナー用）が
          別々に存在したが、機能重複を解消するため統合。
        - 非同期メソッドで統一（async def）
        - Application層のDTO（QuoteData等）を返す
    """

    # S&P500 ETFのシンボル
    SP500_SYMBOL = "SPY"

    # ========================================
    # FinancialDataGateway インターフェース実装
    # ========================================

    async def get_quote(self, symbol: str) -> QuoteData | None:
        """
        現在の株価データを取得

        Args:
            symbol: ティッカーシンボル

        Returns:
            QuoteData: 株価データ、取得失敗時はNone
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info or info.get("regularMarketPrice") is None:
                return None

            price = info.get("regularMarketPrice", 0)
            previous_close = info.get("previousClose", price)
            change = price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0

            return QuoteData(
                symbol=symbol.upper(),
                price=price,
                change=round(change, 2),
                change_percent=round(change_percent, 2),
                volume=info.get("regularMarketVolume", 0),
                avg_volume=info.get("averageVolume", 0),
                market_cap=info.get("marketCap"),
                pe_ratio=info.get("trailingPE"),
                week_52_high=info.get("fiftyTwoWeekHigh", 0),
                week_52_low=info.get("fiftyTwoWeekLow", 0),
                timestamp=datetime.now(),
            )
        except Exception:
            return None

    async def get_quotes(self, symbols: list[str]) -> dict[str, QuoteData]:
        """
        複数銘柄の株価データを一括取得

        Args:
            symbols: ティッカーシンボルのリスト

        Returns:
            dict[str, QuoteData]: シンボル -> 株価データのマップ
        """
        result: dict[str, QuoteData] = {}

        for symbol in symbols:
            quote = await self.get_quote(symbol)
            if quote is not None:
                result[symbol] = quote

        return result

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
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)

            if hist.empty:
                return []

            result: list[HistoricalBar] = []
            for date, row in hist.iterrows():
                result.append(
                    HistoricalBar(
                        date=date.to_pydatetime(),
                        open=round(row["Open"], 4),
                        high=round(row["High"], 4),
                        low=round(row["Low"], 4),
                        close=round(row["Close"], 4),
                        volume=int(row["Volume"]),
                    )
                )

            return result
        except Exception:
            return []

    async def get_raw_financials(self, symbol: str) -> RawFinancialData | None:
        """
        財務生データを取得

        EPS計算などのビジネスロジックは含まず、
        yfinance から取得した生データのみを返す。

        Args:
            symbol: ティッカーシンボル

        Returns:
            RawFinancialData: 財務生データ、取得失敗時はNone
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info:
                return None

            # 四半期EPSデータを取得
            quarterly_eps = self._extract_quarterly_eps(ticker)

            # 年間EPSデータを取得
            annual_eps = self._extract_annual_eps(ticker)

            return RawFinancialData(
                symbol=symbol.upper(),
                quarterly_eps=quarterly_eps,
                annual_eps=annual_eps,
                eps_ttm=info.get("trailingEps"),
                revenue_growth=self._to_percent(info.get("revenueGrowth")),
                profit_margin=self._to_percent(info.get("profitMargins")),
                roe=self._to_percent(info.get("returnOnEquity")),
                debt_to_equity=info.get("debtToEquity"),
                institutional_ownership=self._to_percent(
                    info.get("heldPercentInstitutions")
                ),
            )
        except Exception:
            return None

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
        # 生データを取得
        raw = await self.get_raw_financials(symbol)
        if raw is None:
            return None

        # Domain層のCalculatorでEPS成長率を計算
        eps_data = EPSData(
            quarterly_eps=raw.quarterly_eps,
            annual_eps=raw.annual_eps,
        )
        eps_result = EPSGrowthCalculator.calculate(eps_data)

        return FinancialMetrics(
            symbol=raw.symbol,
            eps_ttm=raw.eps_ttm,
            eps_growth_quarterly=eps_result.quarterly_growth,
            eps_growth_annual=eps_result.annual_growth,
            revenue_growth=raw.revenue_growth,
            profit_margin=raw.profit_margin,
            roe=raw.roe,
            debt_to_equity=raw.debt_to_equity,
            institutional_ownership=raw.institutional_ownership,
        )

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
        return await self.get_price_history(self.SP500_SYMBOL, period, interval)

    # ========================================
    # レガシーメソッド（後方互換性のため維持）
    # ========================================

    def get_quote_sync(self, symbol: str) -> Quote:
        """
        現在の株価データを取得（同期版・レガシー）

        Args:
            symbol: ティッカーシンボル（例: "AAPL"）

        Returns:
            Quote: 株価エンティティ

        Raises:
            ValueError: シンボルが無効な場合

        Deprecated:
            新規コードでは get_quote() を使用してください
        """
        ticker = yf.Ticker(symbol)
        info = ticker.info

        if not info or info.get("regularMarketPrice") is None:
            raise ValueError(f"Invalid symbol: {symbol}")

        price = info.get("regularMarketPrice", 0)
        previous_close = info.get("previousClose", price)
        change = price - previous_close
        change_percent = (change / previous_close * 100) if previous_close else 0

        return Quote(
            symbol=symbol.upper(),
            price=price,
            change=round(change, 2),
            change_percent=round(change_percent, 2),
            volume=info.get("regularMarketVolume", 0),
            market_cap=info.get("marketCap"),
            pe_ratio=info.get("trailingPE"),
            week_52_high=info.get("fiftyTwoWeekHigh"),
            week_52_low=info.get("fiftyTwoWeekLow"),
            timestamp=datetime.now(),
        )

    def get_history_sync(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d",
    ) -> list[HistoricalPrice]:
        """
        過去の株価データを取得（同期版・レガシー）

        Args:
            symbol: ティッカーシンボル
            period: 期間
            interval: 間隔

        Returns:
            list[HistoricalPrice]: 過去の株価データリスト

        Raises:
            ValueError: シンボルが無効またはデータがない場合

        Deprecated:
            新規コードでは get_price_history() を使用してください
        """
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)

        if hist.empty:
            raise ValueError(f"No history data for symbol: {symbol}")

        result = []
        for date, row in hist.iterrows():
            result.append(
                HistoricalPrice(
                    date=date.to_pydatetime(),
                    open=round(row["Open"], 2),
                    high=round(row["High"], 2),
                    low=round(row["Low"], 2),
                    close=round(row["Close"], 2),
                    volume=int(row["Volume"]),
                )
            )

        return result

    # ========================================
    # プライベートメソッド
    # ========================================

    def _extract_quarterly_eps(self, ticker: yf.Ticker) -> list[float]:
        """
        四半期EPSデータを抽出

        Args:
            ticker: yfinance Tickerオブジェクト

        Returns:
            list[float]: 四半期EPS（新しい順）
        """
        try:
            quarterly = ticker.quarterly_earnings
            if quarterly is None or len(quarterly) == 0:
                return []

            # Reported EPS カラムから値を取得（新しい順）
            eps_list = []
            for _, row in quarterly.iterrows():
                eps = row.get("Reported EPS")
                if eps is not None:
                    eps_list.append(float(eps))

            return eps_list
        except Exception:
            return []

    def _extract_annual_eps(self, ticker: yf.Ticker) -> list[float]:
        """
        年間EPSデータを抽出

        Args:
            ticker: yfinance Tickerオブジェクト

        Returns:
            list[float]: 年間EPS（新しい順）
        """
        try:
            annual = ticker.earnings
            if annual is None or len(annual) == 0:
                return []

            # Earnings カラムから値を取得（古い順でデータが来るので逆順にする）
            eps_list = []
            for _, row in annual.iterrows():
                earnings = row.get("Earnings")
                if earnings is not None:
                    eps_list.append(float(earnings))

            # 新しい順に並べ替え
            return list(reversed(eps_list))
        except Exception:
            return []

    @staticmethod
    def _to_percent(value: float | None) -> float | None:
        """小数を%に変換"""
        if value is None:
            return None
        return round(value * 100, 2)
