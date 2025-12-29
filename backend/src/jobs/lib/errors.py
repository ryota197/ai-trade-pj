"""ジョブ固有エラー"""


class JobError(Exception):
    """ジョブ実行エラー基底クラス"""

    pass


class JobExecutionError(JobError):
    """ジョブ実行中のエラー"""

    def __init__(self, job_name: str, message: str) -> None:
        self.job_name = job_name
        super().__init__(f"[{job_name}] {message}")


class JobSkippedError(JobError):
    """ジョブがスキップされた"""

    pass
