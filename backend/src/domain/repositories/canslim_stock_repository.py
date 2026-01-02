"""CANSLIMStockRepository - CAN-SLIM銘柄リポジトリインターフェース"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from src.domain.models.canslim_stock import CANSLIMStock
from src.domain.models.screening_criteria import ScreeningCriteria


class CANSLIMStockRepository(ABC):
    """CAN-SLIM銘柄リポジトリ

    設計方針:
    - 段階的更新対応: Job 1 → Job 2 → Job 3 の各フェーズで部分更新が可能
    - 一括操作優先: パフォーマンスのため、一括取得・一括更新メソッドを提供
    - UPSERT: 存在すれば更新、なければ挿入
    """

    # === 取得系 ===

    @abstractmethod
    def find_by_symbol_and_date(
        self, symbol: str, target_date: date
    ) -> CANSLIMStock | None:
        """シンボルと日付で取得

        Args:
            symbol: ティッカーシンボル
            target_date: 対象日

        Returns:
            CANSLIMStock または None
        """
        pass

    @abstractmethod
    def find_all_by_date(self, target_date: date) -> list[CANSLIMStock]:
        """指定日の全銘柄を取得

        Args:
            target_date: 対象日

        Returns:
            CANSLIMStock のリスト
        """
        pass

    @abstractmethod
    def find_by_criteria(
        self,
        target_date: date,
        criteria: ScreeningCriteria,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CANSLIMStock]:
        """条件でスクリーニング（計算完了銘柄のみ）

        Args:
            target_date: 対象日
            criteria: スクリーニング条件
            limit: 取得件数上限
            offset: オフセット

        Returns:
            条件を満たす CANSLIMStock のリスト（canslim_score 降順）
        """
        pass

    @abstractmethod
    def find_all_with_relative_strength(
        self, target_date: date
    ) -> list[CANSLIMStock]:
        """relative_strength が計算済みの全銘柄を取得（Job 2 用）

        Args:
            target_date: 対象日

        Returns:
            relative_strength が設定されている CANSLIMStock のリスト
        """
        pass

    @abstractmethod
    def get_all_symbols(self) -> list[str]:
        """全シンボル一覧を取得

        Returns:
            シンボルのリスト
        """
        pass

    # === 保存系（全フィールド） ===

    @abstractmethod
    def save(self, stock: CANSLIMStock) -> None:
        """保存（UPSERT）

        Args:
            stock: 保存する CANSLIMStock
        """
        pass

    @abstractmethod
    def save_all(self, stocks: list[CANSLIMStock]) -> None:
        """一括保存

        Args:
            stocks: 保存する CANSLIMStock のリスト
        """
        pass

    # === 部分更新系（段階的計算用） ===

    @abstractmethod
    def update_rs_ratings(
        self,
        target_date: date,
        rs_ratings: dict[str, int],
    ) -> None:
        """RS Rating を一括更新（Job 2 用）

        Args:
            target_date: 対象日
            rs_ratings: {symbol: rs_rating} の辞書
        """
        pass

    @abstractmethod
    def update_canslim_scores(
        self,
        target_date: date,
        scores: dict[str, dict[str, Any]],
    ) -> None:
        """CAN-SLIM スコアを一括更新（Job 3 用）

        Args:
            target_date: 対象日
            scores: {symbol: {canslim_score, score_c, score_a, ...}} の辞書
        """
        pass
