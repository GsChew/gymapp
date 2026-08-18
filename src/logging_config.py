import logging
import sys
import time
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.config import settings


LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | "
    "request_id={extra[request_id]} | {name}:{function}:{line} | {message}"
)


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        """Forward a standard logging record to Loguru."""
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 0
        while frame:
            module_name = frame.f_globals.get("__name__", "")
            filename = frame.f_code.co_filename
            if not module_name.startswith("logging") and filename != __file__:
                break
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def configure_logging() -> None:
    """Configure Loguru sinks and intercept standard logging records."""
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.configure(extra={"request_id": "-"})
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=LOG_FORMAT,
        colorize=True,
        backtrace=False,
        diagnose=False,
    )
    logger.add(
        log_dir / "app.log",
        enqueue=True,
        level=settings.log_level,
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        encoding="utf-8",
        serialize=settings.log_json,
        format=LOG_FORMAT,
        backtrace=False,
        diagnose=False,
    )
    logger.add(
        log_dir / "errors.log",
        enqueue=True,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        serialize=settings.log_json,
        format=LOG_FORMAT,
        backtrace=False,
        diagnose=False,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging.getLogger(logger_name).handlers = [InterceptHandler()]
        logging.getLogger(logger_name).propagate = False


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        """Log request completion details and attach a request id."""
        request_id = request.headers.get("x-request-id") or str(uuid4())
        request.state.request_id = request_id
        started_at = time.perf_counter()
        bound_logger = logger.bind(request_id=request_id)

        with logger.contextualize(request_id=request_id):
            try:
                response = await call_next(request)
            except Exception:
                elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
                bound_logger.exception(
                    "HTTP request failed method={} path={} elapsed_ms={}",
                    request.method,
                    request.url.path,
                    elapsed_ms,
                )
                raise

            elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
            response.headers["x-request-id"] = request_id
            bound_logger.info(
                "HTTP request completed method={} path={} status_code={} elapsed_ms={}",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
            )
            return response


def setup_app_logging(app: FastAPI) -> None:
    """Attach request logging middleware to the FastAPI app."""
    app.add_middleware(RequestLoggingMiddleware)
