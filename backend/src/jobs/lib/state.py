"""ジョブ実行状態"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class JobState:
    """
    ジョブ実行状態

    ジョブ実行中の進捗状態を保持する。
    """

    job_id: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # 進捗管理（オプション）
    total: int = 0
    processed: int = 0

    def update_progress(self, processed: int) -> None:
        """進捗を更新"""
        self.processed = processed

    @property
    def elapsed_seconds(self) -> float:
        """経過時間（秒）"""
        now = datetime.now(timezone.utc)
        return (now - self.started_at).total_seconds()
