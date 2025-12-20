"""yfinance データ取得ゲートウェイ（統合版）"""

from datetime import datetime

import yfinance as yf

from src.application.interfaces.financial_data_gateway import (
    FinancialDataGateway,
    FinancialMetrics,
    HistoricalBar,
    QuoteData,
)
from src.domain.entities.quote import HistoricalPrice, Quote


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

    async def get_financial_metrics(self, symbol: str) -> FinancialMetrics | None:
        """
        財務指標を取得

        Args:
            symbol: ティッカーシンボル

        Returns:
            FinancialMetrics: 財務指標、取得失敗時はNone
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info:
                return None

            # EPS成長率の計算
            eps_growth_quarterly = self._calculate_eps_growth_quarterly(ticker)
            eps_growth_annual = self._calculate_eps_growth_annual(ticker)

            return FinancialMetrics(
                symbol=symbol.upper(),
                eps_ttm=info.get("trailingEps"),
                eps_growth_quarterly=eps_growth_quarterly,
                eps_growth_annual=eps_growth_annual,
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

    def _calculate_eps_growth_quarterly(self, ticker: yf.Ticker) -> float | None:
        """四半期EPS成長率を計算"""
        try:
            quarterly = ticker.quarterly_earnings
            if quarterly is None or len(quarterly) < 2:
                return None

            # 最新四半期と前年同期を比較
            current = quarterly.iloc[0]["Reported EPS"]
            previous = (
                quarterly.iloc[-1]["Reported EPS"]
                if len(quarterly) >= 4
                else quarterly.iloc[1]["Reported EPS"]
            )

            if previous == 0:
                return None

            return round(((current - previous) / abs(previous)) * 100, 2)
        except Exception:
            return None

    def _calculate_eps_growth_annual(self, ticker: yf.Ticker) -> float | None:
        """年間EPS成長率を計算"""
        try:
            annual = ticker.earnings
            if annual is None or len(annual) < 2:
                return None

            # 最新年度と前年度を比較
            current = annual.iloc[-1]["Earnings"]
            previous = annual.iloc[-2]["Earnings"]

            if previous == 0:
                return None

            return round(((current - previous) / abs(previous)) * 100, 2)
        except Exception:
            return None

    @staticmethod
    def _to_percent(value: float | None) -> float | None:
        """小数を%に変換"""
        if value is None:
            return None
        return round(value * 100, 2)
