"""管理者機能 DTO"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RefreshJobInput:
    """リフレッシュジョブ開始入力"""

    symbols: list[str]
    source: str = "custom"  # "sp500", "nasdaq100", "custom"


@dataclass(frozen=True)
class RefreshJobProgress:
    """リフレッシュジョブ進捗"""

    total: int
    processed: int
    succeeded: int
    failed: int
    percentage: float


@dataclass(frozen=True)
class RefreshJobTiming:
    """リフレッシュジョブタイミング"""

    started_at: datetime | None
    elapsed_seconds: float
    estimated_remaining_seconds: float | None


@dataclass(frozen=True)
class RefreshJobError:
    """リフレッシュジョブエラー"""

    symbol: str
    error: str


@dataclass(frozen=True)
class RefreshJobOutput:
    """リフレッシュジョブ出力"""

    job_id: str
    status: str
    total_symbols: int
    started_at: datetime | None


@dataclass(frozen=True)
class RefreshJobStatusOutput:
    """リフレッシュジョブステータス出力"""

    job_id: str
    status: str
    progress: RefreshJobProgress
    timing: RefreshJobTiming
    errors: list[RefreshJobError]
