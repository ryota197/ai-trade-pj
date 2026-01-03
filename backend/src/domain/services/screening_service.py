"""スクリーニングサービス"""

from datetime import date

from src.domain.models.canslim_stock import CANSLIMStock
from src.domain.models.screening_criteria import ScreeningCriteria
from src.domain.repositories.canslim_stock_repository import CANSLIMStockRepository


class ScreeningService:
    """スクリーニングサービス

    スクリーニング条件に基づいて銘柄をフィルタリングし、結果を返す。

    なぜドメインサービスか:
    - リポジトリへのアクセスが必要
    - 複数の集約を横断する操作
    """

    def __init__(self, repository: CANSLIMStockRepository) -> None:
        self._repository = repository

    def screen(
        self,
        target_date: date,
        criteria: ScreeningCriteria,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CANSLIMStock]:
        """条件に合致する銘柄をスクリーニング

        Args:
            target_date: 対象日
            criteria: スクリーニング条件
            limit: 取得上限
            offset: オフセット

        Returns:
            条件を満たす銘柄リスト（スコア順）
        """
        return self._repository.find_by_criteria(
            target_date=target_date,
            criteria=criteria,
            limit=limit,
            offset=offset,
        )
