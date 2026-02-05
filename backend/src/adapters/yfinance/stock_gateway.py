"""株価・財務データ取得ゲートウェイ"""

from datetime import datetime

import yfinance as yf

from src.adapters.yfinance.types import (
    FinancialMetrics,
    HistoricalBar,
    QuoteData,
    RawFinancialData,
)


class YFinanceGateway:
    """
    yfinance を使用した財務データゲートウェイ

    株価・財務データを一元的に取得する。
    """

    SP500_SYMBOL = "SPY"

    async def get_quote(self, symbol: str) -> QuoteData | None:
        """現在の株価データを取得"""
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
        """複数銘柄の株価データを一括取得"""
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
        """株価履歴を取得"""
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
        """財務生データを取得"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info:
                return None

            quarterly_eps = self._extract_quarterly_eps(ticker)
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
        """財務指標を取得"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info:
                return None

            return FinancialMetrics(
                symbol=symbol.upper(),
                eps_ttm=info.get("trailingEps"),
                eps_growth_quarterly=self._to_percent(info.get("earningsQuarterlyGrowth")),
                eps_growth_annual=self._to_percent(info.get("earningsGrowth")),
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
        """S&P500の株価履歴を取得（RS Rating計算用）"""
        return await self.get_price_history(self.SP500_SYMBOL, period, interval)

    # === プライベートメソッド ===

    def _extract_quarterly_eps(self, ticker: yf.Ticker) -> list[float]:
        """四半期EPSデータを抽出"""
        try:
            quarterly = ticker.quarterly_earnings
            if quarterly is None or len(quarterly) == 0:
                return []

            eps_list = []
            for _, row in quarterly.iterrows():
                eps = row.get("Reported EPS")
                if eps is not None:
                    eps_list.append(float(eps))

            return eps_list
        except Exception:
            return []

    def _extract_annual_eps(self, ticker: yf.Ticker) -> list[float]:
        """年間EPSデータを抽出"""
        try:
            annual = ticker.earnings
            if annual is None or len(annual) == 0:
                return []

            eps_list = []
            for _, row in annual.iterrows():
                earnings = row.get("Earnings")
                if earnings is not None:
                    eps_list.append(float(earnings))

            return list(reversed(eps_list))
        except Exception:
            return []

    @staticmethod
    def _to_percent(value: float | None) -> float | None:
        """小数を%に変換"""
        if value is None:
            return None
        return round(value * 100, 2)
