from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from redis.exceptions import RedisError

from src.rate_limit.dependencies import check_result
from src.rate_limit.limiter import get_ratelimit_result
from src.schemas.rate_limit import SRateLimitResponse, SRateLimitRule


pytestmark = [pytest.mark.unit]


def test_allowed_rate_limit_result_does_not_raise() -> None:
    rule = SRateLimitRule("test", 2, 60)
    result = SRateLimitResponse(
        allowed=True,
        limit=2,
        remaining=1,
        retry_after=0,
    )

    check_result(result, rule, "user-1")


def test_denied_rate_limit_result_has_retry_after() -> None:
    rule = SRateLimitRule("test", 2, 60)
    result = SRateLimitResponse(
        allowed=False,
        limit=2,
        remaining=0,
        retry_after=17,
    )

    with pytest.raises(HTTPException) as error:
        check_result(result, rule, "user-1")

    assert error.value.status_code == 429
    assert error.value.headers == {"Retry-After": "17"}


@pytest.mark.asyncio
async def test_limiter_translates_redis_script_response(monkeypatch) -> None:
    redis = AsyncMock()
    redis.eval.return_value = [1, 3, 2, 0]
    monkeypatch.setattr("src.rate_limit.limiter.redis_client", redis)

    result = await get_ratelimit_result(
        "client",
        SRateLimitRule("scope", 3, 60),
    )

    assert result == SRateLimitResponse(
        allowed=True,
        limit=3,
        remaining=2,
        retry_after=0,
    )


@pytest.mark.asyncio
async def test_limiter_fails_open_when_redis_is_unavailable(monkeypatch) -> None:
    redis = AsyncMock()
    redis.eval.side_effect = RedisError("offline")
    monkeypatch.setattr("src.rate_limit.limiter.redis_client", redis)

    result = await get_ratelimit_result(
        "client",
        SRateLimitRule("scope", 3, 60),
    )

    assert result.allowed is True
    assert result.remaining == 3
