from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar


T = TypeVar("T")


async def poll_until(
    operation: Callable[[], Awaitable[T]],
    predicate: Callable[[T], bool],
    *,
    timeout: float = 5.0,
    interval: float = 0.05,
) -> T:
    deadline = time.monotonic() + timeout
    last_value: T
    while True:
        last_value = await operation()
        if predicate(last_value):
            return last_value
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Condition was not met within {timeout} seconds")
        await asyncio.sleep(interval)
