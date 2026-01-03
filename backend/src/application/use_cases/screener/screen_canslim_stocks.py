"""CAN-SLIMスクリーニング ユースケース"""

from datetime import date, datetime
from decimal import Decimal

from src.application.dto.screener_dto import (
    ScreenerFilterInput,
    ScreenerResultOutput,
    StockSummaryOutput,
)
from src.domain.models.canslim_stock import CANSLIMStock
from src.domain.models.screening_criteria import ScreeningCriteria
from src.domain.repositories.canslim_stock_repository import CANSLIMStockRepository


class ScreenCANSLIMStocksUseCase:
    """
    CAN-SLIMスクリーニング ユースケース

    CAN-SLIM条件に基づいて銘柄をスクリーニングし、
    投資候補を抽出する。
    """

    def __init__(self, canslim_stock_repository: CANSLIMStockRepository) -> None:
        self._stock_repo = canslim_stock_repository

    def execute(
        self,
        filter_input: ScreenerFilterInput,
        target_date: date | None = None,
    ) -> ScreenerResultOutput:
        """
        CAN-SLIM条件でスクリーニングを実行

        Args:
            filter_input: スクリーニング条件
            target_date: 対象日（デフォルトは今日）

        Returns:
            ScreenerResultOutput: スクリーニング結果
        """
        if target_date is None:
            target_date = date.today()

        # 入力DTOからドメインの ScreeningCriteria に変換
        criteria = ScreeningCriteria(
            min_rs_rating=filter_input.min_rs_rating,
            min_canslim_score=filter_input.min_canslim_score,
            min_eps_growth_quarterly=Decimal(str(filter_input.min_eps_growth_quarterly)),
            min_eps_growth_annual=Decimal(str(filter_input.min_eps_growth_annual)),
            max_distance_from_high=Decimal(str(filter_input.max_distance_from_52w_high)),
            min_volume_ratio=Decimal(str(filter_input.min_volume_ratio)),
        )

        # リポジトリからスクリーニング結果を取得
        stocks = self._stock_repo.find_by_criteria(
            target_date=target_date,
            criteria=criteria,
            limit=filter_input.limit,
            offset=filter_input.offset,
        )

        # 出力DTOに変換
        stock_outputs = [self._to_summary(stock) for stock in stocks]

        return ScreenerResultOutput(
            total_count=len(stock_outputs),
            stocks=stock_outputs,
            filter_applied=filter_input,
            screened_at=datetime.now(),
        )

    def _to_summary(self, stock: CANSLIMStock) -> StockSummaryOutput:
        """CANSLIMStockをサマリーDTOに変換"""
        return StockSummaryOutput(
            symbol=stock.symbol,
            name=stock.name or stock.symbol,
            price=float(stock.price) if stock.price else 0.0,
            change_percent=float(stock.change_percent) if stock.change_percent else 0.0,
            rs_rating=stock.rs_rating or 0,
            canslim_score=stock.canslim_score or 0,
            volume_ratio=float(stock.volume_ratio()) if stock.volume_ratio() else 0.0,
            distance_from_52w_high=(
                float(stock.distance_from_52week_high())
                if stock.distance_from_52week_high()
                else 0.0
            ),
        )
