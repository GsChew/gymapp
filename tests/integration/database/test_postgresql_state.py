import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from src.auth.security import hash_password
from src.models.notification import NotificationModel
from src.models.user import User
from src.models.workout import ExerciseModel, StatusTypes, WorkoutExercise
from tests.factories.user_factory import UserFactory
from tests.factories.workout_factory import WorkoutExerciseFactory, WorkoutFactory
from tests.helpers.dates import future_datetime


pytestmark = [pytest.mark.integration, pytest.mark.database]


@pytest.mark.asyncio
async def test_postgresql_enforces_unique_username_and_email(db_session) -> None:
    first = UserFactory.build()
    user = User(
        username=first["username"],
        email=first["email"],
        hashed_password=hash_password(first["password"]),
    )
    db_session.add(user)
    await db_session.commit()

    duplicate_username = UserFactory.build(username=first["username"])
    db_session.add(
        User(
            username=duplicate_username["username"],
            email=duplicate_username["email"],
            hashed_password=hash_password(duplicate_username["password"]),
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    duplicate_email = UserFactory.build(email=first["email"])
    db_session.add(
        User(
            username=duplicate_email["username"],
            email=duplicate_email["email"],
            hashed_password=hash_password(duplicate_email["password"]),
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    assert await db_session.scalar(select(func.count()).select_from(User)) == 1


@pytest.mark.asyncio
async def test_postgresql_enforces_workout_exercise_foreign_keys(
    user_account,
    db_session,
) -> None:
    invalid = WorkoutExercise(
        workout_id=999_999,
        exercise_id=999_999,
        order_index=0,
        sets=1,
        reps=1,
        scheduled_at=future_datetime(),
        status=StatusTypes.planned,
    )
    db_session.add(invalid)

    with pytest.raises((IntegrityError, TypeError, ValueError)):
        await db_session.commit()
    await db_session.rollback()

    assert (
        await db_session.scalar(
            select(func.count()).select_from(WorkoutExercise)
        )
        == 0
    )


@pytest.mark.asyncio
async def test_deleting_workout_cascades_links_but_preserves_notification(
    user_account,
    make_exercise,
    make_notification,
    db_session,
) -> None:
    workout_response = await user_account.clients.workouts.create_workout(
        WorkoutFactory.build()
    )
    workout_id = workout_response.json()["id"]
    exercise = await make_exercise()
    link = await user_account.clients.workout_exercises.create_link(
        WorkoutExerciseFactory.build(
            workout_id=workout_id,
            exercise_id=exercise.id,
        )
    )
    assert link.status_code == 200
    notification = await make_notification(
        user_id=user_account.user.id,
        workout_id=workout_id,
    )

    deleted = await user_account.clients.workouts.delete_workout(workout_id)
    assert deleted.status_code == 200, deleted.text

    assert (
        await db_session.get(WorkoutExercise, (exercise.id, workout_id))
        is None
    )
    await db_session.refresh(notification)
    assert notification.workout_id is None


@pytest.mark.asyncio
async def test_deleting_exercise_cascades_workout_link(
    user_account,
    admin_account,
    make_exercise,
    db_session,
) -> None:
    workout = await user_account.clients.workouts.create_workout(
        WorkoutFactory.build()
    )
    exercise = await make_exercise()
    link = await user_account.clients.workout_exercises.create_link(
        WorkoutExerciseFactory.build(
            workout_id=workout.json()["id"],
            exercise_id=exercise.id,
        )
    )
    assert link.status_code == 200

    deleted = await admin_account.clients.exercises.delete_exercise(exercise.id)
    assert deleted.status_code == 200, deleted.text
    assert await db_session.get(ExerciseModel, exercise.id) is None
    assert (
        await db_session.get(
            WorkoutExercise,
            (exercise.id, workout.json()["id"]),
        )
        is None
    )


@pytest.mark.asyncio
async def test_notification_unique_constraint_prevents_duplicate_workout_reminder(
    user_account,
    make_workout,
    make_notification,
    db_session,
) -> None:
    workout = await make_workout(user_id=user_account.user.id)
    workout_id = workout.id
    await make_notification(
        user_id=user_account.user.id,
        workout_id=workout_id,
    )
    duplicate = NotificationModel(
        user_id=user_account.user.id,
        workout_id=workout_id,
        title="Duplicate",
        message="Duplicate",
    )
    db_session.add(duplicate)

    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    count = await db_session.scalar(
        select(func.count())
        .select_from(NotificationModel)
        .where(NotificationModel.workout_id == workout_id)
    )
    assert count == 1
