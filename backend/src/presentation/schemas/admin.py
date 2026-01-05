"""管理者API スキーマ"""

from datetime import datetime

from pydantic import BaseModel, Field


class RefreshJobRequest(BaseModel):
    """リフレッシュジョブ開始リクエスト"""

    symbols: list[str] = Field(
        default_factory=list,
        description="更新する銘柄シンボルのリスト（空の場合はsourceから取得）",
    )
    source: str = Field(
        "sp500",
        description="データソース: sp500（symbolsが空の場合に使用）",
    )


class RefreshJobResponse(BaseModel):
    """リフレッシュジョブ開始レスポンス"""

    flow_id: str = Field(..., description="フローID")
    status: str = Field(..., description="ステータス")
    message: str = Field(..., description="メッセージ")


class JobExecutionSchema(BaseModel):
    """ジョブ実行スキーマ"""

    job_name: str = Field(..., description="ジョブ名")
    status: str = Field(..., description="ステータス: pending, running, completed, failed, skipped")
    started_at: datetime | None = Field(None, description="開始日時")
    completed_at: datetime | None = Field(None, description="完了日時")
    error_message: str | None = Field(None, description="エラーメッセージ")


class FlowStatusResponse(BaseModel):
    """フローステータスレスポンス"""

    flow_id: str = Field(..., description="フローID")
    flow_name: str = Field(..., description="フロー名")
    status: str = Field(..., description="ステータス: pending, running, completed, failed, cancelled")
    total_jobs: int = Field(..., description="総ジョブ数")
    completed_jobs: int = Field(..., description="完了ジョブ数")
    current_job: str | None = Field(None, description="現在実行中のジョブ名")
    started_at: datetime | None = Field(None, description="開始日時")
    completed_at: datetime | None = Field(None, description="完了日時")
    jobs: list[JobExecutionSchema] = Field(default_factory=list, description="ジョブ一覧")


class CancelJobResponse(BaseModel):
    """キャンセルレスポンス"""

    message: str = Field(..., description="メッセージ")
