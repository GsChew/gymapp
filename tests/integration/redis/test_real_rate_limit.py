from uuid import uuid4

import pytest
from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.rate_limit import limiter
from src.schemas.rate_limit import SRateLimitRule


pytestmark = [
    pytest.mark.integration,
    pytest.mark.redis,
]


@pytest.mark.asyncio
async def test_real_redis_sliding_window_blocks_after_limit(
    test_settings,
    monkeypatch,
) -> None:
    redis = Redis.from_url(test_settings.redis_url, decode_responses=True)
    try:
        await redis.ping()
    except (OSError, RedisError) as error:
        await redis.aclose()
        if test_settings.require_infrastructure:
            pytest.fail(f"Redis test infrastructure is unavailable: {error}")
        pytest.skip(
            "Redis is unavailable. Start docker-compose.test.yml infrastructure."
        )

    monkeypatch.setattr(limiter, "redis_client", redis)
    identifier = f"qa-{uuid4().hex}"
    rule = SRateLimitRule("integration", limit=2, window=60)
    key = f"rate_limit:{rule.scope}:{identifier}"
    try:
        first = await limiter.get_ratelimit_result(identifier, rule)
        second = await limiter.get_ratelimit_result(identifier, rule)
        third = await limiter.get_ratelimit_result(identifier, rule)

        assert first.allowed is True
        assert first.remaining == 1
        assert second.allowed is True
        assert second.remaining == 0
        assert third.allowed is False
        assert third.remaining == 0
        assert third.retry_after >= 1
    finally:
        await redis.delete(key)
        await redis.aclose()
