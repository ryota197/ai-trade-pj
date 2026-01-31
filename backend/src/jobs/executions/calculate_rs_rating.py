"""RS Rating 計算ジョブ (Job 2)"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from src.queries import CANSLIMStockQuery
from src.services import RSRatingCalculator
from src.jobs.executions.base import Job


@dataclass
class CalculateRSRatingInput:
    """RS Rating 計算入力"""

    target_date: date | None = None  # None の場合は当日


@dataclass
class CalculateRSRatingOutput:
    """RS Rating 計算出力"""

    total_stocks: int
    updated_count: int
    errors: list[dict] = field(default_factory=list)


class CalculateRSRatingJob(Job[CalculateRSRatingInput, CalculateRSRatingOutput]):
    """
    RS Rating 計算ジョブ (Job 2)

    DB内の全銘柄の relative_strength からパーセンタイルランキングを計算し、
    rs_rating (1-99) を一括更新する。

    責務:
        - DB内の全銘柄の最新 relative_strength を取得
        - パーセンタイル計算（RSRatingCalculator に委譲）
        - canslim_stocks.rs_rating を一括更新

    注意:
        - 外部API呼び出しなし
        - Job 1 完了後に実行
        - 500銘柄でも数秒で完了
    """

    name = "calculate_rs_rating"

    def __init__(
        self,
        stock_query: CANSLIMStockQuery,
        rs_rating_calculator: RSRatingCalculator | None = None,
    ) -> None:
        self._stock_query = stock_query
        self._calculator = rs_rating_calculator or RSRatingCalculator()

    async def execute(
        self, input_: CalculateRSRatingInput | None = None
    ) -> CalculateRSRatingOutput:
        """ジョブ実行"""
        # 対象日を決定
        target_date = input_.target_date if input_ else None
        if target_date is None:
            target_date = date.today()

        # 1. relative_strength 計算済みの全銘柄を取得
        stocks = self._stock_query.find_all_with_relative_strength(target_date)

        if not stocks:
            return CalculateRSRatingOutput(
                total_stocks=0,
                updated_count=0,
                errors=[{"error": "No stocks with relative_strength found"}],
            )

        # 2. relative_strength を辞書に変換
        relative_strengths: dict[str, Decimal] = {
            stock.symbol: stock.relative_strength
            for stock in stocks
            if stock.relative_strength is not None
        }

        # 3. RSRatingCalculator で RS Rating を計算
        rs_ratings = self._calculator.calculate_ratings(relative_strengths)

        # 4. 一括更新
        self._stock_query.update_rs_ratings(target_date, rs_ratings)

        return CalculateRSRatingOutput(
            total_stocks=len(stocks),
            updated_count=len(rs_ratings),
            errors=[],
        )
