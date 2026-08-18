from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy.engine import URL, make_url


@dataclass(frozen=True, slots=True)
class TestSettings:
    database_url: str
    alembic_database_url: str
    redis_url: str
    rabbitmq_url: str
    api_timeout: float
    require_infrastructure: bool

    @property
    def parsed_database_url(self) -> URL:
        return make_url(self.database_url)

    def validate_database_safety(self) -> None:
        url = self.parsed_database_url
        database_name = url.database or ""
        if not database_name.endswith("_test"):
            raise RuntimeError(
                "TEST_DATABASE_URL must use a database ending with '_test'; "
                f"refusing destructive setup for {database_name!r}"
            )
        if database_name in {"gymapp", "postgres", "template0", "template1"}:
            raise RuntimeError(
                f"Refusing destructive setup for protected database {database_name!r}"
            )


@lru_cache(maxsize=1)
def get_test_settings() -> TestSettings:
    return TestSettings(
        database_url=os.getenv(
            "TEST_DATABASE_URL",
            "postgresql+asyncpg://gym_test:gym_test@127.0.0.1:55432/gymapp_test",
        ),
        alembic_database_url=os.getenv(
            "TEST_ALEMBIC_DATABASE_URL",
            "postgresql+psycopg://gym_test:gym_test@127.0.0.1:55432/gymapp_test",
        ),
        redis_url=os.getenv("TEST_REDIS_URL", "redis://127.0.0.1:56379/0"),
        rabbitmq_url=os.getenv(
            "TEST_RABBITMQ_URL",
            "amqp://guest:guest@127.0.0.1:55672//",
        ),
        api_timeout=float(os.getenv("TEST_API_TIMEOUT", "5")),
        require_infrastructure=os.getenv("REQUIRE_TEST_INFRA") == "1",
    )
