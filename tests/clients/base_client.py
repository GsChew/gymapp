from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from httpx import AsyncClient, Response
from loguru import logger

from tests.helpers.safe_logging import redact


@dataclass(slots=True)
class HttpExchange:
    request: dict[str, Any]
    response: dict[str, Any]


class BaseClient:
    """Thin HTTP transport wrapper without test-specific assertions."""

    def __init__(
        self,
        transport: AsyncClient,
        *,
        token: str | None = None,
        timeout: float = 5.0,
    ) -> None:
        self._transport = transport
        self._token = token
        self._timeout = timeout
        self.exchanges: list[HttpExchange] = []

    async def request(self, method: str, path: str, **kwargs: Any) -> Response:
        headers = dict(kwargs.pop("headers", {}))
        if self._token and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {self._token}"

        logger.debug(
            "Test HTTP request method={} path={} payload={}",
            method,
            path,
            redact(kwargs.get("json")),
        )
        response = await self._transport.request(
            method,
            path,
            headers=headers,
            timeout=kwargs.pop("timeout", self._timeout),
            **kwargs,
        )
        self.exchanges.append(
            HttpExchange(
                request={
                    "method": method.upper(),
                    "url": str(response.request.url),
                    "headers": redact(dict(response.request.headers)),
                    "body": redact(kwargs.get("json")),
                },
                response={
                    "status_code": response.status_code,
                    "headers": redact(dict(response.headers)),
                    "body": self._response_body(response),
                },
            )
        )
        logger.debug(
            "Test HTTP response method={} path={} status_code={}",
            method,
            path,
            response.status_code,
        )
        return response

    async def get(self, path: str, **kwargs: Any) -> Response:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> Response:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> Response:
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs: Any) -> Response:
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> Response:
        return await self.request("DELETE", path, **kwargs)

    def dump_exchanges(self) -> str:
        return json.dumps(
            [asdict(exchange) for exchange in self.exchanges],
            ensure_ascii=False,
            indent=2,
            default=str,
        )

    @staticmethod
    def _response_body(response: Response) -> Any:
        try:
            return redact(response.json())
        except ValueError:
            return response.text[:4000]
