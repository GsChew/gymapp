from celery import Celery

from src.config import settings


celery_app = Celery(
    "gymapp",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.tasks.workout_notifications",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "check-workout-notifications-every-minute": {
            "task": "check_workout_notifications",
            "schedule": 60.0,
        },
    },
)