"""銘柄詳細取得 ユースケース"""

from datetime import date, datetime

from src.application.dto.screener_dto import (
    CANSLIMCriteriaOutput,
    CANSLIMScoreOutput,
    StockDetailInput,
    StockDetailOutput,
)
from src.domain.models.canslim_stock import CANSLIMStock
from src.domain.repositories.canslim_stock_repository import CANSLIMStockRepository


class GetStockDetailUseCase:
    """
    銘柄詳細取得 ユースケース

    個別銘柄の詳細情報（株価、財務指標、CAN-SLIMスコア）を取得する。
    """

    def __init__(
        self,
        canslim_stock_repository: CANSLIMStockRepository,
    ) -> None:
        self._stock_repo = canslim_stock_repository

    def execute(
        self,
        input_dto: StockDetailInput,
        target_date: date | None = None,
    ) -> StockDetailOutput | None:
        """
        銘柄詳細を取得

        Args:
            input_dto: 入力DTO（シンボル）
            target_date: 対象日（デフォルトは今日）

        Returns:
            StockDetailOutput: 銘柄詳細、見つからない場合はNone
        """
        if target_date is None:
            target_date = date.today()

        stock = self._stock_repo.find_by_symbol_and_date(
            symbol=input_dto.symbol.upper(),
            target_date=target_date,
        )

        if stock is None:
            return None

        return self._to_output(stock)

    def _to_output(self, stock: CANSLIMStock) -> StockDetailOutput:
        """CANSLIMStockを出力DTOに変換"""
        # CAN-SLIMスコアを出力DTOに変換
        canslim_output = None
        if stock.canslim_score is not None:
            canslim_output = CANSLIMScoreOutput(
                total_score=stock.canslim_score,
                overall_grade=self._score_to_grade(stock.canslim_score),
                passing_count=self._count_passing(stock),
                c_score=self._create_criteria("C - Current Quarterly Earnings", stock.score_c),
                a_score=self._create_criteria("A - Annual Earnings", stock.score_a),
                n_score=self._create_criteria("N - New High", stock.score_n),
                s_score=self._create_criteria("S - Supply and Demand", stock.score_s),
                l_score=self._create_criteria("L - Leader", stock.score_l),
                i_score=self._create_criteria("I - Institutional Sponsorship", stock.score_i),
            )

        price = float(stock.price) if stock.price else 0.0
        change_percent = float(stock.change_percent) if stock.change_percent else 0.0

        return StockDetailOutput(
            symbol=stock.symbol,
            name=stock.name or stock.symbol,
            price=price,
            change=price * change_percent / 100,
            change_percent=change_percent,
            volume=stock.volume or 0,
            avg_volume=stock.avg_volume_50d or 0,
            market_cap=float(stock.market_cap) if stock.market_cap else None,
            pe_ratio=None,  # PE比率はCANSLIMStockに含まれない
            week_52_high=float(stock.week_52_high) if stock.week_52_high else 0.0,
            week_52_low=float(stock.week_52_low) if stock.week_52_low else 0.0,
            eps_growth_quarterly=(
                float(stock.eps_growth_quarterly) if stock.eps_growth_quarterly else None
            ),
            eps_growth_annual=(
                float(stock.eps_growth_annual) if stock.eps_growth_annual else None
            ),
            rs_rating=stock.rs_rating or 0,
            institutional_ownership=(
                float(stock.institutional_ownership) if stock.institutional_ownership else None
            ),
            canslim_score=canslim_output,
            updated_at=stock.updated_at or datetime.now(),
        )

    def _score_to_grade(self, score: int) -> str:
        """スコアをグレードに変換"""
        if score >= 80:
            return "A"
        elif score >= 60:
            return "B"
        elif score >= 40:
            return "C"
        elif score >= 20:
            return "D"
        return "F"

    def _count_passing(self, stock: CANSLIMStock) -> int:
        """合格項目数をカウント"""
        passing = 0
        for score in [stock.score_c, stock.score_a, stock.score_n,
                      stock.score_s, stock.score_l, stock.score_i]:
            if score is not None and score >= 10:  # 基準：10点以上で合格
                passing += 1
        return passing

    def _create_criteria(self, name: str, score: int | None) -> CANSLIMCriteriaOutput:
        """スコアからCriteriaOutputを作成"""
        score_val = score or 0
        return CANSLIMCriteriaOutput(
            name=name,
            score=score_val,
            grade=self._score_to_grade(score_val),
            value=None,  # 詳細値はフラット構造では保持しない
            threshold=0.0,
            description="",
        )
