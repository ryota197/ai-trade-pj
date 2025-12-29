"""PostgreSQL StockIdentity リポジトリ"""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.domain.entities import StockIdentity
from src.domain.repositories import StockIdentityRepository
from src.infrastructure.database.models import StockModel


class PostgresStockIdentityRepository(StockIdentityRepository):
    """銘柄マスターリポジトリ実装"""

    def __init__(self, session: Session) -> None:
        self._session = session

    async def save(self, identity: StockIdentity) -> None:
        """保存（UPSERT）"""
        stmt = select(StockModel).where(StockModel.symbol == identity.symbol.upper())
        existing = self._session.scalars(stmt).first()

        if existing:
            existing.name = identity.name
            existing.industry = identity.industry
        else:
            model = StockModel(
                symbol=identity.symbol.upper(),
                name=identity.name,
                industry=identity.industry,
            )
            self._session.add(model)

        self._session.commit()

    async def get(self, symbol: str) -> StockIdentity | None:
        """取得"""
        stmt = select(StockModel).where(StockModel.symbol == symbol.upper())
        model = self._session.scalars(stmt).first()

        if model is None:
            return None

        return StockIdentity(
            symbol=model.symbol,
            name=model.name,
            industry=model.industry,
        )

    async def get_all_symbols(self) -> list[str]:
        """全シンボル取得"""
        stmt = select(StockModel.symbol)
        return list(self._session.scalars(stmt).all())

    async def delete(self, symbol: str) -> bool:
        """削除"""
        stmt = delete(StockModel).where(StockModel.symbol == symbol.upper())
        result = self._session.execute(stmt)
        self._session.commit()
        return result.rowcount > 0
