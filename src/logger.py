from loguru import logger
from pathlib import Path


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


logger.remove()


logger.add(
    "logs/app.log",
    enqueue=True,
    level="INFO",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    encoding="utf-8",
format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)


logger.add(
    "logs/errors.log",
    enqueue=True,
    level="ERROR",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)