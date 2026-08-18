from fastapi import HTTPException, Request, Depends
from loguru import logger

from src.auth.dependencies import get_current_user
from src.models.user import User
from src.schemas.rate_limit import SRateLimitRule, SRateLimitResponse
from src.rate_limit.limiter import get_ratelimit_result


def check_result(
    result: SRateLimitResponse,
    rule: SRateLimitRule,
    identifier: str,
) -> None:
    """Raise an HTTP error when a rate-limit result denies the request."""
    if not result.allowed:
        logger.warning(
            f"Rate limit exceeded "
            f"scope={rule.scope}, "
            f"identifier={identifier}, "
            f"limit={result.limit}, "
            f"remaining={result.remaining}, "
            f"retry_after={result.retry_after}"
        )

        raise HTTPException(
            status_code=429,
            detail="Too many requests. Try again later.",
            headers={
                "Retry-After": str(result.retry_after),
            },
        )


def limit_by_ip(rule: SRateLimitRule):
    """Create a dependency that rate-limits requests by client IP address."""
    async def dependency(request: Request) -> None:
        """Evaluate the configured rate-limit rule for the request."""
        identifier = request.client.host if request.client else None

        if not identifier:
            logger.warning(
                f"Could not determine client IP for rate limit scope={rule.scope}"
            )

            raise HTTPException(
                status_code=400,
                detail="Could not determine client IP",
            )

        result = await get_ratelimit_result(
            identifier=identifier,
            rule=rule,
        )

        check_result(
            result=result,
            rule=rule,
            identifier=identifier,
        )

    return dependency


def limit_by_user(rule: SRateLimitRule):
    """Create a dependency that rate-limits requests by authenticated user."""
    async def dependency(
        user: User = Depends(get_current_user),
    ) -> None:
        """Evaluate the configured rate-limit rule for the request."""
        identifier = str(user.id)

        result = await get_ratelimit_result(
            identifier=identifier,
            rule=rule,
        )

        check_result(
            result=result,
            rule=rule,
            identifier=identifier,
        )

    return dependency
