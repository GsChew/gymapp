from dataclasses import dataclass
from pydantic import BaseModel

@dataclass(frozen=True)
class SRateLimitRule:
    scope: str
    limit: int
    window: int


class SRateLimitResponse(BaseModel):
    allowed: bool
    limit: int
    remaining: int
    retry_after: int

