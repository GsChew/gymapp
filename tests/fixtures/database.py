from __future__ import annotations

from collections.abc import AsyncIterator

import psycopg
import pytest
import pytest_asyncio
from psycopg import sql
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import src.models  # noqa: F401
from src.database import Model
from tests.fixtures.config import TestSettings, get_test_settings


def _ensure_database(settings: TestSettings) -> None:
    settings.validate_database_safety()
    url = settings.parsed_database_url
    connect_kwargs = {
        "host": url.host,
        "port": url.port,
        "user": url.username,
        "password": url.password,
        "dbname": "postgres",
        "connect_timeout": 3,
        "autocommit": True,
    }
    with psycopg.connect(**connect_kwargs) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (url.database,),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(url.database)
                    )
                )


@pytest.fixture(scope="session")
def test_settings() -> TestSettings:
    return get_test_settings()


@pytest_asyncio.fixture(scope="session")
async def db_engine(test_settings: TestSettings) -> AsyncIterator[AsyncEngine]:
    try:
        _ensure_database(test_settings)
        engine = create_async_engine(
            test_settings.database_url,
            pool_pre_ping=True,
        )
        async with engine.begin() as connection:
            await connection.run_sync(Model.metadata.drop_all)
            await connection.run_sync(Model.metadata.create_all)
    except (OSError, psycopg.OperationalError) as error:
        if test_settings.require_infrastructure:
            pytest.fail(f"PostgreSQL test infrastructure is unavailable: {error}")
        pytest.skip(
            "PostgreSQL is unavailable. Run "
            "`docker compose -f docker-compose.test.yml up -d "
            "test-db test-redis test-rabbitmq`."
        )

    try:
        yield engine
    finally:
        async with engine.begin() as connection:
            await connection.run_sync(Model.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def clean_database(db_engine: AsyncEngine) -> AsyncIterator[None]:
    table_names = [table.name for table in Model.metadata.sorted_tables]
    quoted = ", ".join(f'"{name}"' for name in table_names)
    async with db_engine.begin() as connection:
        await connection.execute(
            text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE")
        )
    yield
    async with db_engine.begin() as connection:
        await connection.execute(
            text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE")
        )


@pytest_asyncio.fixture
async def db_session(
    db_engine: AsyncEngine,
    clean_database: None,
) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def db_session_factory(db_engine: AsyncEngine):
    return async_sessionmaker(db_engine, expire_on_commit=False)
