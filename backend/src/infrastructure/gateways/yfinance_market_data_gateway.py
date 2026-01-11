"""yfinance マーケットデータゲートウェイ"""

import yfinance as yf


class YFinanceMarketDataGateway:
    """
    yfinance APIを使用したマーケットデータ取得実装

    MarketDataRepositoryインターフェースを実装し、
    VIX、S&P500価格、RSI、200日移動平均、Put/Call Ratioを取得する。
    """

    # ティッカーシンボル
    VIX_SYMBOL = "^VIX"
    SP500_SYMBOL = "^GSPC"

    def get_vix(self) -> float:
        """
        VIX（恐怖指数）を取得

        Returns:
            float: VIX値

        Raises:
            ValueError: データ取得に失敗した場合
        """
        ticker = yf.Ticker(self.VIX_SYMBOL)
        info = ticker.info

        price = info.get("regularMarketPrice")
        if price is None:
            raise ValueError("Failed to fetch VIX data")

        return float(price)

    def get_sp500_price(self) -> float:
        """
        S&P500の現在価格を取得

        Returns:
            float: S&P500価格

        Raises:
            ValueError: データ取得に失敗した場合
        """
        ticker = yf.Ticker(self.SP500_SYMBOL)
        info = ticker.info

        price = info.get("regularMarketPrice")
        if price is None:
            raise ValueError("Failed to fetch S&P500 price")

        return float(price)

    def get_sp500_rsi(self, period: int = 14) -> float:
        """
        S&P500のRSI（相対力指数）を計算

        Args:
            period: RSI計算期間（デフォルト14日）

        Returns:
            float: RSI値（0-100）

        Raises:
            ValueError: データ取得に失敗した場合
        """
        ticker = yf.Ticker(self.SP500_SYMBOL)
        # RSI計算に十分なデータを取得（periodの2倍程度）
        hist = ticker.history(period="3mo", interval="1d")

        if hist.empty or len(hist) < period + 1:
            raise ValueError("Insufficient data to calculate RSI")

        # RSI計算
        close_prices = hist["Close"]
        delta = close_prices.diff()

        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)

        # Wilder's Smoothing Method（指数移動平均）
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(float(rsi.iloc[-1]), 2)

    def get_sp500_ma200(self) -> float:
        """
        S&P500の200日移動平均を取得

        Returns:
            float: 200MA値

        Raises:
            ValueError: データ取得に失敗した場合
        """
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
            yfinanceでは直接Put/Call Ratioを取得できない。
            ^CPCE（CBOE Equity Put/Call Ratio）はYahoo Financeで
            提供されなくなったため、POCではデフォルト値を返す。

            本番環境では以下のデータソースを検討:
            - CBOE公式API（有料）
            - Alpha Vantage
            - Quandl

        Returns:
            float: Put/Call Ratio（POCではデフォルト値 0.85）
        """
        # TODO: 本番環境では別のデータソースから取得
        # POCではデフォルト値（中立）を返す
        return 0.85
