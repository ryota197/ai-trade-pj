"""yfinance データ取得アダプター"""

from dataclasses import dataclass
from datetime import datetime

import yfinance as yf


# ========================================
# データクラス
# ========================================


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
    """財務生データ"""

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
    eps_ttm: float | None
    eps_growth_quarterly: float | None
    eps_growth_annual: float | None
    revenue_growth: float | None
    profit_margin: float | None
    roe: float | None
    debt_to_equity: float | None
    institutional_ownership: float | None


# ========================================
# YFinance Gateway
# ========================================


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


# ========================================
# YFinance Market Data Gateway
# ========================================


class YFinanceMarketDataGateway:
    """
    マーケットデータ取得ゲートウェイ

    VIX、S&P500価格、RSI、200日移動平均、Put/Call Ratioを取得する。
    """

    VIX_SYMBOL = "^VIX"
    SP500_SYMBOL = "^GSPC"

    def get_vix(self) -> float:
        """VIX（恐怖指数）を取得"""
        ticker = yf.Ticker(self.VIX_SYMBOL)
        info = ticker.info

        price = info.get("regularMarketPrice")
        if price is None:
            raise ValueError("Failed to fetch VIX data")

        return float(price)

    def get_sp500_price(self) -> float:
        """S&P500の現在価格を取得"""
        ticker = yf.Ticker(self.SP500_SYMBOL)
        info = ticker.info

        price = info.get("regularMarketPrice")
        if price is None:
            raise ValueError("Failed to fetch S&P500 price")

        return float(price)

    def get_sp500_rsi(self, period: int = 14) -> float:
        """S&P500のRSI（相対力指数）を計算"""
        ticker = yf.Ticker(self.SP500_SYMBOL)
        hist = ticker.history(period="3mo", interval="1d")

        if hist.empty or len(hist) < period + 1:
            raise ValueError("Insufficient data to calculate RSI")

        close_prices = hist["Close"]
        delta = close_prices.diff()

        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)

        avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(float(rsi.iloc[-1]), 2)

    def get_sp500_ma200(self) -> float:
        """S&P500の200日移動平均を取得"""
        ticker = yf.Ticker(self.SP500_SYMBOL)
        hist = ticker.history(period="1y", interval="1d")

        if hist.empty or len(hist) < 200:
            raise ValueError("Insufficient data to calculate 200MA")

        ma200 = hist["Close"].rolling(window=200).mean().iloc[-1]

        return round(float(ma200), 2)

    def get_put_call_ratio(self) -> float:
        """
        Put/Call Ratioを取得

        Note:
            yfinanceでは直接取得できないため、POCではデフォルト値を返す。
        """
        return 0.85
