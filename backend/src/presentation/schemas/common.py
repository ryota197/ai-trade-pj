"""共通スキーマ定義"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """エラー詳細"""

    code: str
    message: str


class ApiResponse(BaseModel, Generic[T]):
    """API共通レスポンス"""

    success: bool
    data: T | None = None
    error: ErrorDetail | None = None
