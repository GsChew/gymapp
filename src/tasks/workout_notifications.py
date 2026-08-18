import asyncio
from datetime import UTC, datetime
from loguru import logger

from src.celery_app import celery_app
from src.database import new_session
from src.repository.notifications import NotificationsRepository
from src.repository.workouts import WorkoutRepository
from src.schemas.notification import SNotificationCreate


@celery_app.task(name="check_workout_notifications")
def check_workout_notifications():
    """Run the scheduled workout notification task."""
    logger.info("Celery task started: check_workout_notifications")

    try:
        asyncio.run(_check_workout_notifications())

    except Exception:
        logger.exception("Celery task failed: check_workout_notifications")
        raise

    logger.info("Celery task finished: check_workout_notifications")


async def _check_workout_notifications():
    """Create due workout notifications and mark them as sent."""
    now = datetime.now(UTC)

    logger.info(f"Checking workout notifications now={now}")

    async with new_session() as session:
        try:
            workouts = await WorkoutRepository.get_workouts_for_notifications(
                session=session,
                now=now,
            )

            if not workouts:
                logger.info("No workouts found for notifications")
                return

            workout_ids = [workout.id for workout in workouts]

            logger.info(
                f"Workouts found for notifications "
                f"count={len(workouts)} "
                f"workout_ids={workout_ids}"
            )

            notifications_data = [
                SNotificationCreate(
                    user_id=workout.user_id,
                    workout_id=workout.id,
                    title="Скоро тренировка",
                    message=f"У вас запланирована тренировка: {workout.title}",
                )
                for workout in workouts
            ]

            await NotificationsRepository.bulk_create_notifications(
                session=session,
                notifications_data=notifications_data,
            )

            await WorkoutRepository.mark_notifications_sent(
                session=session,
                workout_ids=workout_ids,
            )

            await session.commit()

            logger.info(
                f"Workout notifications sent successfully "
                f"count={len(notifications_data)} "
                f"workout_ids={workout_ids}"
            )

        except Exception:
            await session.rollback()

            logger.exception(
                "Error while checking workout notifications"
            )

            raise
