"""マーケットデータリポジトリ インターフェース"""

from abc import ABC, abstractmethod


class MarketDataRepository(ABC):
    """
    マーケットデータリポジトリの抽象インターフェース

    外部データソース（yfinance等）からの市場データ取得を抽象化する。
    Infrastructure層で具体的な実装を提供する。
    """

    @abstractmethod
    def get_vix(self) -> float:
        """
        VIX（恐怖指数）を取得

        Returns:
            float: VIX値
        """
        pass

    @abstractmethod
    def get_sp500_price(self) -> float:
        """
        S&P500の現在価格を取得

        Returns:
            float: S&P500価格
        """
        pass

    @abstractmethod
    def get_sp500_rsi(self, period: int = 14) -> float:
        """
        S&P500のRSIを取得

        Args:
            period: RSI計算期間（デフォルト14日）

        Returns:
            float: RSI値（0-100）
        """
        pass

    @abstractmethod
    def get_sp500_ma200(self) -> float:
        """
        S&P500の200日移動平均を取得

        Returns:
            float: 200MA値
        """
        pass

    @abstractmethod
    def get_put_call_ratio(self) -> float:
        """
        Put/Call Ratioを取得

        Returns:
            float: Put/Call Ratio
        """
        pass
