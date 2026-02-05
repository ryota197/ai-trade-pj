"""ファンダメンタル指標取得ゲートウェイ"""

import yfinance as yf

from src.adapters.yfinance.types import FundamentalIndicators


class FundamentalsGateway:
    """
    ファンダメンタル指標取得ゲートウェイ

    銘柄詳細画面で表示するファンダメンタル指標を取得する。
    """

    async def get_indicators(self, symbol: str) -> FundamentalIndicators | None:
        """ファンダメンタル指標を取得"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info:
                return None

            return FundamentalIndicators(
                symbol=symbol.upper(),
                forward_pe=info.get("forwardPE"),
                peg_ratio=info.get("pegRatio"),
                roe=self._to_percent(info.get("returnOnEquity")),
                operating_margin=self._to_percent(info.get("operatingMargins")),
                revenue_growth=self._to_percent(info.get("revenueGrowth")),
                beta=info.get("beta"),
            )
        except Exception:
            return None

    @staticmethod
    def _to_percent(value: float | None) -> float | None:
        """小数を%に変換"""
        if value is None:
            return None
        return round(value * 100, 2)
