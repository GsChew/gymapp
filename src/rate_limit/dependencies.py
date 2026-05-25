from fastapi import HTTPException, Request, Depends

from src.auth.dependencies import get_current_user
from src.models.UserModels import User
from src.schemas.RateLimit import SRateLimitRule, SRateLimitResponse
from src.rate_limit.limiter import get_ratelimit_result


def check_result(result: SRateLimitResponse) -> None:
    if not result.allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Try again later.",
            headers={
                "Retry-After": str(result.retry_after),
            },
        )


def limit_by_ip(rule: SRateLimitRule):
    async def dependency(request: Request) -> None:
        identifier = request.client.host if request.client else None

        if not identifier:
            raise HTTPException(
                status_code=400,
                detail="Could not determine client IP",
            )

        result = await get_ratelimit_result(
            identifier=identifier,
            rule=rule,
        )

        check_result(result)

    return dependency


def limit_by_user(rule: SRateLimitRule):
    async def dependency(
        user: User = Depends(get_current_user),
    ) -> None:
        identifier = str(user.id)

        result = await get_ratelimit_result(
            identifier=identifier,
            rule=rule,
        )

        check_result(result)

    return dependency