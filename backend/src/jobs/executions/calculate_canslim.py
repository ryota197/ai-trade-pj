"""CAN-SLIMスコア計算ジョブ (Job 3)"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from src.queries import CANSLIMStockQuery, MarketSnapshotQuery
from src.services import CANSLIMScorer
from src.services._lib import MarketCondition
from src.jobs.executions.base import Job


@dataclass
class CalculateCANSLIMInput:
    """CAN-SLIMスコア計算入力"""

    target_date: date | None = None  # None の場合は当日
    market_condition: MarketCondition | None = None  # None の場合はリポジトリから取得


@dataclass
class CalculateCANSLIMOutput:
    """CAN-SLIMスコア計算出力"""

    total_stocks: int
    updated_count: int
    market_condition: str  # JSONシリアライズのため文字列で保持
    errors: list[dict] = field(default_factory=list)


class CalculateCANSLIMJob(Job[CalculateCANSLIMInput, CalculateCANSLIMOutput]):
    """
    CAN-SLIMスコア計算ジョブ (Job 3)

    DB内の全銘柄データからCAN-SLIMスコアを計算し、
    canslim_stocks.canslim_score を一括更新する。

    責務:
        - DB内の当日分の全銘柄データを取得（rs_rating が設定済み）
        - CAN-SLIMスコア計算（CANSLIMScorer に委譲）
        - canslim_stocks の各スコアを一括更新

    注意:
        - 外部API呼び出しなし
        - Job 2 完了後に実行（rs_rating が必要）
        - 500銘柄でも数秒で完了
    """

    name = "calculate_canslim"

    def __init__(
        self,
        stock_query: CANSLIMStockQuery,
        market_query: MarketSnapshotQuery | None = None,
        canslim_scorer: CANSLIMScorer | None = None,
    ) -> None:
        self._stock_query = stock_query
        self._market_query = market_query
        self._scorer = canslim_scorer or CANSLIMScorer()

    async def execute(
        self, input_: CalculateCANSLIMInput | None = None
    ) -> CalculateCANSLIMOutput:
        """ジョブ実行"""
        errors: list[dict] = []

        # 対象日を決定
        target_date = input_.target_date if input_ else None
        if target_date is None:
            target_date = date.today()

        # 市場状態を決定
        market_condition = self._get_market_condition(input_)

        # 1. 当日分の全銘柄データを取得（rs_rating が設定済みのもの）
        stocks = self._stock_query.find_all_by_date(target_date)
        stocks_with_rs = [s for s in stocks if s.rs_rating is not None]

        if not stocks_with_rs:
            return CalculateCANSLIMOutput(
                total_stocks=0,
                updated_count=0,
                market_condition=market_condition,
                errors=[{"error": "No stocks with rs_rating found"}],
            )

        # 2. 各銘柄のCAN-SLIMスコアを計算
        scores: dict[str, dict[str, Any]] = {}
        for stock in stocks_with_rs:
            try:
                result = self._scorer.score(stock, market_condition)
                scores[stock.symbol] = {
                    "canslim_score": result.total,
                    "score_c": result.c,
                    "score_a": result.a,
                    "score_n": result.n,
                    "score_s": result.s,
                    "score_l": result.l,
                    "score_i": result.i,
                    "score_m": result.m,
                }
            except Exception as e:
                errors.append({"symbol": stock.symbol, "error": str(e)})

        # 3. 一括更新
        if scores:
            self._stock_query.update_canslim_scores(target_date, scores)

        return CalculateCANSLIMOutput(
            total_stocks=len(stocks_with_rs),
            updated_count=len(scores),
            market_condition=market_condition.value,  # enum → string
            errors=errors,
        )

    def _get_market_condition(
        self, input_: CalculateCANSLIMInput | None
    ) -> MarketCondition:
        """市場状態を取得"""
        # 入力で指定されていればそれを使用
        if input_ and input_.market_condition:
            return input_.market_condition

        # クエリから取得
        if self._market_query:
            snapshot = self._market_query.find_latest()
            if snapshot:
                return MarketCondition(snapshot.condition)

        # デフォルトはNEUTRAL
        return MarketCondition.NEUTRAL
