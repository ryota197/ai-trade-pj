"""シンボルプロバイダー"""

import aiohttp


class SymbolProvider:
    """
    シンボルプロバイダー（基底クラス）

    S&P500やNASDAQ100のシンボルリストを取得する。
    """

    async def get_symbols(self, source: str) -> list[str]:
        """
        シンボルリストを取得

        Args:
            source: "sp500" | "nasdaq100"

        Returns:
            list[str]: シンボルリスト
        """
        raise NotImplementedError()


class WikipediaSymbolProvider(SymbolProvider):
    """
    Wikipediaからシンボルリストを取得するプロバイダー

    S&P500、NASDAQ100の構成銘柄をWikipediaから取得する。
    """

    # S&P500の代表的な銘柄（フォールバック用）
    SP500_SAMPLE = [
        "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "GOOG", "BRK.B",
        "UNH", "XOM", "LLY", "JPM", "JNJ", "V", "PG", "MA", "AVGO", "HD",
        "CVX", "MRK", "ABBV", "COST", "PEP", "ADBE", "KO", "WMT", "MCD",
        "CSCO", "CRM", "BAC", "PFE", "TMO", "ACN", "NFLX", "AMD", "LIN",
        "ABT", "DHR", "DIS", "ORCL", "CMCSA", "NKE", "TXN", "VZ", "PM",
        "INTC", "WFC", "NEE", "RTX", "UNP",
    ]

    # NASDAQ100の代表的な銘柄（フォールバック用）
    NASDAQ100_SAMPLE = [
        "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "GOOG", "AVGO",
        "TSLA", "ADBE", "COST", "PEP", "CSCO", "NFLX", "AMD", "CMCSA",
        "INTC", "QCOM", "TMUS", "INTU", "TXN", "AMGN", "AMAT", "HON",
        "ISRG", "BKNG", "SBUX", "VRTX", "ADP", "GILD", "MDLZ", "ADI",
        "REGN", "LRCX", "PANW", "MU", "KLAC", "SNPS", "CDNS", "PYPL",
        "MELI", "CSX", "ORLY", "CTAS", "MAR", "NXPI", "ASML", "WDAY",
        "MNST", "PCAR",
    ]

    async def get_symbols(self, source: str) -> list[str]:
        """
        シンボルリストを取得

        Args:
            source: "sp500" | "nasdaq100"

        Returns:
            list[str]: シンボルリスト
        """
        if source == "sp500":
            return await self._fetch_sp500()
        elif source == "nasdaq100":
            return await self._fetch_nasdaq100()
        else:
            raise ValueError(f"Unknown source: {source}")

    async def _fetch_sp500(self) -> list[str]:
        """S&P500銘柄を取得"""
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "parse",
                "page": "List_of_S%26P_500_companies",
                "format": "json",
                "prop": "wikitext",
                "section": "1",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as resp:
                    if resp.status != 200:
                        return self.SP500_SAMPLE

                    data = await resp.json()
                    wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")

                    symbols = self._parse_wikipedia_table(wikitext)
                    return symbols if symbols else self.SP500_SAMPLE

        except Exception:
            return self.SP500_SAMPLE

    async def _fetch_nasdaq100(self) -> list[str]:
        """NASDAQ100銘柄を取得"""
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "parse",
                "page": "Nasdaq-100",
                "format": "json",
                "prop": "wikitext",
                "section": "2",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as resp:
                    if resp.status != 200:
                        return self.NASDAQ100_SAMPLE

                    data = await resp.json()
                    wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")

                    symbols = self._parse_wikipedia_table(wikitext)
                    return symbols if symbols else self.NASDAQ100_SAMPLE

        except Exception:
            return self.NASDAQ100_SAMPLE

    def _parse_wikipedia_table(self, wikitext: str) -> list[str]:
        """Wikipediaテーブルからシンボルを抽出"""
        symbols = []
        lines = wikitext.split("\n")

        for line in lines:
            if "{{nowrap|" in line:
                start = line.find("{{nowrap|") + 9
                end = line.find("}}", start)
                if end > start:
                    symbol = line[start:end].strip()
                    if symbol.isupper() and len(symbol) <= 5:
                        symbols.append(symbol)

        return symbols


class StaticSymbolProvider(SymbolProvider):
    """
    静的シンボルプロバイダー（テスト・開発用）

    固定のシンボルリストを返す。
    """

    SP500 = WikipediaSymbolProvider.SP500_SAMPLE
    NASDAQ100 = WikipediaSymbolProvider.NASDAQ100_SAMPLE

    async def get_symbols(self, source: str) -> list[str]:
        """シンボルリストを取得"""
        if source == "sp500":
            return self.SP500
        elif source == "nasdaq100":
            return self.NASDAQ100
        else:
            raise ValueError(f"Unknown source: {source}")
