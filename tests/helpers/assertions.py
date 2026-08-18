from collections.abc import Iterable
from typing import Any

from httpx import Response


def assert_has_fields(payload: dict[str, Any], expected: Iterable[str]) -> None:
    missing = set(expected) - payload.keys()
    assert not missing, f"Response is missing fields: {sorted(missing)}"


def assert_error(
    response: Response,
    expected_status: int,
    *,
    detail_contains: str | None = None,
) -> None:
    assert response.status_code == expected_status, response.text
    payload = response.json()
    assert "detail" in payload, payload
    if detail_contains is not None:
        assert detail_contains in str(payload["detail"]), payload
    assert "traceback" not in str(payload).lower(), payload
