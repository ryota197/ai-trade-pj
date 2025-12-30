"""価格スナップショット エンティティ"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PriceSnapshot:
    """
    価格スナップショット

    日次の株価・出来高データ。履歴として蓄積可能。
    対応テーブル: stock_prices
    """

    symbol: str
    price: float | None
    change_percent: float | None
    volume: int | None
    avg_volume_50d: int | None
    market_cap: int | None
    week_52_high: float | None
    week_52_low: float | None
    recorded_at: datetime
