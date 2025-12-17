"""ヘルスチェック用スキーマ"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """ヘルスチェックレスポンス"""

    status: str
    database: str
