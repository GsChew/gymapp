import asyncio
from datetime import UTC, datetime

from src.celery_app import celery_app
from src.database import new_session
from src.repository.notifications import NotificationsRepository
from src.repository.workouts import WorkoutRepository
from src.schemas.NotificationSchemas import SNotificationCreate


@celery_app.task(name="check_workout_notifications")
def check_workout_notifications():
    asyncio.run(_check_workout_notifications())


async def _check_workout_notifications():
    now = datetime.now(UTC)

    async with new_session() as session:
        workouts = await WorkoutRepository.get_workouts_for_notifications(
            session=session,
            now=now,
        )

        if not workouts:
            return

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
            workout_ids=[workout.id for workout in workouts],
        )

        await session.commit()