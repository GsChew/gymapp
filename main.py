from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from src.auth.router import router as auth_router
from src.workouts.router import router as workout_router
from src.exercises.router import router as exercise_router
from src.goals.router import router as goals_router
from src.workout_exercises.router import router as workout_exercise_router
from src.notifications.router import router as notification_router
from src.progress.router import router as progress_router
from src.templates.router import router as template_router
from src.users.router import router as user_router
from src.logging_config import configure_logging, setup_app_logging
from loguru import logger

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Gym Planner API", version="1.0.0")
configure_logging()
setup_app_logging(app)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Convert application ValueError exceptions into HTTP JSON responses."""
    detail = str(exc)
    normalized = detail.lower()

    if "не найден" in normalized or "не принадлежит" in normalized:
        status_code = 404
    elif "уже существует" in normalized:
        status_code = 409
    elif "учетные данные" in normalized:
        status_code = 401
    else:
        status_code = 400

    logger.bind(request_id=getattr(request.state, "request_id", "-")).warning(
        "Handled application error path={} status_code={} detail={}",
        request.url.path,
        status_code,
        detail,
    )
    return JSONResponse(status_code=status_code, content={"detail": detail})

app.include_router(auth_router)
app.include_router(workout_router)
app.include_router(exercise_router)
app.include_router(goals_router)
app.include_router(workout_exercise_router)
app.include_router(notification_router)
app.include_router(progress_router)
app.include_router(template_router)

app.include_router(user_router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Return a lightweight health-check response."""
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def frontend() -> FileResponse:
    """Serve the single-page application entrypoint."""
    return FileResponse(STATIC_DIR / "index.html")
