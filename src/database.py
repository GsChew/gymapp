from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.config import settings


DATABASE_URL = settings.database_url

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

new_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def get_db():
    """Yield an asynchronous database session for request handling."""
    async with new_session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]


class Model(DeclarativeBase):
    pass
