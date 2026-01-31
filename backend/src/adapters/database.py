"""データベース接続設定"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from src.config import get_settings

settings = get_settings()

# SQLAlchemy Engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # SQLログ出力（デバッグ用）
    pool_pre_ping=True,  # 接続の有効性を事前確認
)

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    DBセッションを取得するDependency

    Usage:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
