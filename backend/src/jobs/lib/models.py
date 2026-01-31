"""フロー・ジョブ実行ステータス定義（レガシー互換）"""

from enum import Enum


class FlowStatus(str, Enum):
    """フロー実行状態"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStatus(str, Enum):
    """ジョブ実行状態"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
