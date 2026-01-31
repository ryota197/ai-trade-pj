"""マーケットデータ収集ジョブ"""

from dataclasses import dataclass
from decimal import Decimal

from src.adapters.yfinance import YFinanceMarketDataGateway
from src.queries import MarketSnapshotQuery
from src.services import MarketAnalyzer
from src.jobs.executions.base import Job


@dataclass
class CollectMarketInput:
    """マーケットデータ収集入力（現状は空）"""

    pass


@dataclass
class CollectMarketOutput:
    """マーケットデータ収集出力"""

    vix: float
    sp500_price: float
    sp500_rsi: float
    sp500_ma200: float
    put_call_ratio: float
    condition: str  # risk_on / neutral / risk_off
    score: int  # -5 ~ +5


class CollectMarketDataJob(Job[CollectMarketInput, CollectMarketOutput]):
    """
    マーケットデータ収集ジョブ

    責務:
        - yfinanceからマーケット指標を取得（VIX, S&P500価格, RSI, MA200, P/C Ratio）
        - MarketAnalyzerでスコア・状態を計算
        - market_snapshotsテーブルに保存
    """

    name = "collect_market_data"

    def __init__(
        self,
        market_query: MarketSnapshotQuery,
        gateway: YFinanceMarketDataGateway | None = None,
        analyzer: MarketAnalyzer | None = None,
    ) -> None:
        self._query = market_query
        self._gateway = gateway or YFinanceMarketDataGateway()
        self._analyzer = analyzer or MarketAnalyzer()

    async def execute(
        self, input_: CollectMarketInput | None = None
    ) -> CollectMarketOutput:
        """ジョブ実行"""
        # 1. yfinanceからデータ取得
        vix = self._gateway.get_vix()
        sp500_price = self._gateway.get_sp500_price()
        sp500_rsi = self._gateway.get_sp500_rsi()
        sp500_ma200 = self._gateway.get_sp500_ma200()
        put_call_ratio = self._gateway.get_put_call_ratio()

        # 2. スコア計算
        result = self._analyzer.analyze(
            vix=Decimal(str(vix)),
            sp500_price=Decimal(str(sp500_price)),
            sp500_rsi=Decimal(str(sp500_rsi)),
            sp500_ma200=Decimal(str(sp500_ma200)),
            put_call_ratio=Decimal(str(put_call_ratio)),
        )

        # 3. DBに保存（MarketAnalysisResult を渡す）
        self._query.save(result)

        return CollectMarketOutput(
            vix=vix,
            sp500_price=sp500_price,
            sp500_rsi=sp500_rsi,
            sp500_ma200=sp500_ma200,
            put_call_ratio=put_call_ratio,
            condition=result.condition.value,
            score=result.score,
        )
