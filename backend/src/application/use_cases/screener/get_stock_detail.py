"""銘柄詳細取得 ユースケース"""

from src.application.dto.screener_dto import (
    CANSLIMCriteriaOutput,
    CANSLIMScoreOutput,
    StockDetailInput,
    StockDetailOutput,
)
from src.domain.repositories.stock_repository import StockRepository


class GetStockDetailUseCase:
    """
    銘柄詳細取得 ユースケース

    個別銘柄の詳細情報（株価、財務指標、CAN-SLIMスコア）を取得する。
    """

    def __init__(
        self,
        stock_repository: StockRepository,
    ) -> None:
        self._stock_repo = stock_repository

    async def execute(
        self,
        input_dto: StockDetailInput,
    ) -> StockDetailOutput | None:
        """
        銘柄詳細を取得

        Args:
            input_dto: 入力DTO（シンボル）

        Returns:
            StockDetailOutput: 銘柄詳細、見つからない場合はNone
        """
        stock = await self._stock_repo.get_by_symbol(input_dto.symbol)

        if stock is None:
            return None

        # CAN-SLIMスコアを出力DTOに変換
        canslim_output = None
        if stock.canslim_score is not None:
            cs = stock.canslim_score
            canslim_output = CANSLIMScoreOutput(
                total_score=cs.total_score,
                overall_grade=cs.overall_grade.value,
                passing_count=cs.passing_criteria_count,
                c_score=CANSLIMCriteriaOutput(
                    name="C - Current Quarterly Earnings",
                    score=cs.c_score.score,
                    grade=cs.c_score.grade.value,
                    value=cs.c_score.value,
                    threshold=cs.c_score.threshold,
                    description=cs.c_score.description,
                ),
                a_score=CANSLIMCriteriaOutput(
                    name="A - Annual Earnings",
                    score=cs.a_score.score,
                    grade=cs.a_score.grade.value,
                    value=cs.a_score.value,
                    threshold=cs.a_score.threshold,
                    description=cs.a_score.description,
                ),
                n_score=CANSLIMCriteriaOutput(
                    name="N - New High",
                    score=cs.n_score.score,
                    grade=cs.n_score.grade.value,
                    value=cs.n_score.value,
                    threshold=cs.n_score.threshold,
                    description=cs.n_score.description,
                ),
                s_score=CANSLIMCriteriaOutput(
                    name="S - Supply and Demand",
                    score=cs.s_score.score,
                    grade=cs.s_score.grade.value,
                    value=cs.s_score.value,
                    threshold=cs.s_score.threshold,
                    description=cs.s_score.description,
                ),
                l_score=CANSLIMCriteriaOutput(
                    name="L - Leader",
                    score=cs.l_score.score,
                    grade=cs.l_score.grade.value,
                    value=cs.l_score.value,
                    threshold=cs.l_score.threshold,
                    description=cs.l_score.description,
                ),
                i_score=CANSLIMCriteriaOutput(
                    name="I - Institutional Sponsorship",
                    score=cs.i_score.score,
                    grade=cs.i_score.grade.value,
                    value=cs.i_score.value,
                    threshold=cs.i_score.threshold,
                    description=cs.i_score.description,
                ),
            )

        # 出力DTOを構築
        return StockDetailOutput(
            symbol=stock.symbol,
            name=stock.name,
            price=stock.price,
            change=stock.price * stock.change_percent / 100,
            change_percent=stock.change_percent,
            volume=stock.volume,
            avg_volume=stock.avg_volume,
            market_cap=stock.market_cap,
            pe_ratio=stock.pe_ratio,
            week_52_high=stock.week_52_high,
            week_52_low=stock.week_52_low,
            eps_growth_quarterly=stock.eps_growth_quarterly,
            eps_growth_annual=stock.eps_growth_annual,
            rs_rating=stock.rs_rating,
            institutional_ownership=stock.institutional_ownership,
            canslim_score=canslim_output,
            updated_at=stock.updated_at,
        )
