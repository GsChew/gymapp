import time
import uuid

from loguru import logger
from redis.exceptions import RedisError

from src.schemas.rate_limit import SRateLimitRule, SRateLimitResponse
from src.rate_limit.redis import redis_client


async def get_ratelimit_result(
    identifier: str,
    rule: SRateLimitRule,
) -> SRateLimitResponse:
    """Return the current rate-limit decision for a key and rule."""
    redis_key = f"rate_limit:{rule.scope}:{identifier}"

    now_ms = int(time.time() * 1000)
    window_ms = rule.window * 1000
    request_id = f"{now_ms}:{uuid.uuid4()}"
    expire_seconds = rule.window + 5

    try:
        response = await redis_client.eval(
            SLIDING_WINDOW_SCRIPT,
            1,
            redis_key,
            now_ms,
            window_ms,
            rule.limit,
            request_id,
            expire_seconds,
        )

    except RedisError as e:
        logger.exception(
            f"Redis error during rate limit check. "
            f"scope={rule.scope}, "
            f"identifier={identifier}, "
            f"redis_key={redis_key}, "
            f"error={e}"
        )

        return SRateLimitResponse(
            allowed=True,
            limit=rule.limit,
            remaining=rule.limit,
            retry_after=0,
        )

    allowed, limit, remaining, retry_after = response

    return SRateLimitResponse(
        allowed=bool(allowed),
        limit=int(limit),
        remaining=int(remaining),
        retry_after=int(retry_after),
    )


SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]

local now_ms = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local request_id = ARGV[4]
local expire_seconds = tonumber(ARGV[5])

local window_start = now_ms - window_ms

redis.call("ZREMRANGEBYSCORE", key, 0, window_start)

local current_count = redis.call("ZCARD", key)

if current_count >= limit then
    local oldest = redis.call("ZRANGE", key, 0, 0, "WITHSCORES")
    local retry_after = 1

    if oldest[2] then
        local oldest_timestamp = tonumber(oldest[2])
        retry_after = math.ceil((oldest_timestamp + window_ms - now_ms) / 1000)

        if retry_after < 1 then
            retry_after = 1
        end
    end

    return {0, limit, 0, retry_after}
end

redis.call("ZADD", key, now_ms, request_id)
redis.call("EXPIRE", key, expire_seconds)

local remaining = limit - current_count - 1

return {1, limit, remaining, 0}
"""
