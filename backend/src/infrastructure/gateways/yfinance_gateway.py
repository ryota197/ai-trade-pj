"""yfinance データ取得ゲートウェイ"""

from datetime import datetime

import yfinance as yf

from src.domain.entities.quote import HistoricalPrice, Quote


class YFinanceGateway:
    """yfinance APIラッパー"""

    def get_quote(self, symbol: str) -> Quote:
        """
        現在の株価データを取得

        Args:
            symbol: ティッカーシンボル（例: "AAPL"）

        Returns:
            Quote: 株価エンティティ

        Raises:
            ValueError: シンボルが無効な場合
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

    def get_history(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d",
    ) -> list[HistoricalPrice]:
        """
        過去の株価データを取得

        Args:
            symbol: ティッカーシンボル（例: "AAPL"）
            period: 期間（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）
            interval: 間隔（1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo）

        Returns:
            list[HistoricalPrice]: 過去の株価データリスト

        Raises:
            ValueError: シンボルが無効またはデータがない場合
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
