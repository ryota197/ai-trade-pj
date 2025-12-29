"""銘柄マスター エンティティ"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StockIdentity:
    """
    銘柄マスター

    銘柄の基本情報を表す。更新頻度は稀。
    対応テーブル: stocks
    """

    symbol: str
    name: str | None = None
    industry: str | None = None
