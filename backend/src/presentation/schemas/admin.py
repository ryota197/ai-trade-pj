"""管理者API スキーマ"""

from datetime import datetime

from pydantic import BaseModel, Field


class RefreshJobRequest(BaseModel):
    """リフレッシュジョブ開始リクエスト"""

    symbols: list[str] = Field(..., description="更新する銘柄シンボルのリスト")
    source: str = Field("custom", description="データソース: sp500, nasdaq100, custom")


class RefreshJobResponse(BaseModel):
    """リフレッシュジョブ開始レスポンス"""

    job_id: str = Field(..., description="ジョブID")
    status: str = Field(..., description="ステータス")
    total_symbols: int = Field(..., description="対象銘柄数")
    started_at: datetime | None = Field(None, description="開始日時")


class RefreshJobProgressSchema(BaseModel):
    """進捗スキーマ"""

    total: int = Field(..., description="対象銘柄数")
    processed: int = Field(..., description="処理済み銘柄数")
    succeeded: int = Field(..., description="成功銘柄数")
    failed: int = Field(..., description="失敗銘柄数")
    percentage: float = Field(..., description="進捗率（%）")


class RefreshJobTimingSchema(BaseModel):
    """タイミングスキーマ"""

    started_at: datetime | None = Field(None, description="開始日時")
    elapsed_seconds: float = Field(..., description="経過時間（秒）")
    estimated_remaining_seconds: float | None = Field(None, description="推定残り時間（秒）")


class RefreshJobErrorSchema(BaseModel):
    """エラースキーマ"""

    symbol: str = Field(..., description="エラーが発生した銘柄")
    error: str = Field(..., description="エラーメッセージ")


class RefreshJobStatusResponse(BaseModel):
    """リフレッシュジョブステータスレスポンス"""

    job_id: str = Field(..., description="ジョブID")
    status: str = Field(..., description="ステータス: pending, running, completed, failed, cancelled")
    progress: RefreshJobProgressSchema = Field(..., description="進捗")
    timing: RefreshJobTimingSchema = Field(..., description="タイミング")
    errors: list[RefreshJobErrorSchema] = Field(default_factory=list, description="エラーリスト")


class CancelJobResponse(BaseModel):
    """キャンセルレスポンス"""

    message: str = Field(..., description="メッセージ")
