from fastapi import APIRouter, Depends, Query
from loguru import logger

from src.auth.dependencies import get_current_user
from src.database import SessionDep
from src.models.UserModels import User
from src.models.WorkoutModels import StatusTypes, WorkoutModel
from src.rate_limit.config import WORKOUTS_CREATE_USER, WORKOUTS_LIST_USER
from src.rate_limit.dependencies import limit_by_user
from src.schemas.WorkoutSchemas import SWorkoutCreate, SWorkoutUpdate, SWorkout
from src.workouts.service import (
    get_workouts as get_workouts_service,
    get_workout_by_id as get_workout_by_id_service,
    get_workout_by_name as get_workout_by_name_service,
    create_workout as create_workout_service,
    update_workout as update_workout_service,
    delete_workout as delete_workout_service,
)

router = APIRouter(prefix="/workouts", tags=["Workouts"])


@router.get(
    "/",
    response_model=list[SWorkout],
    dependencies=[Depends(limit_by_user(WORKOUTS_LIST_USER))],
)
async def get_workouts(
    session: SessionDep,
    user: User = Depends(get_current_user),
    limit: int = Query(default=15, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: StatusTypes | None = None,
):
    logger.info(
        f"Getting workouts user_id={user.id}, limit={limit}, offset={offset}, status={status}"
    )

    try:
        workouts = await get_workouts_service(
            session=session,
            user_id=user.id,
            limit=limit,
            offset=offset,
            status=status,
        )

        logger.info(f"Workouts received user_id={user.id}, count={len(workouts)}")
        return workouts

    except Exception as e:
        logger.exception(f"Failed to get workouts user_id={user.id}: {e}")
        raise


@router.get("/{workout_id}", response_model=SWorkout)
async def get_workout_by_id(
    workout_id: int,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    logger.info(f"Getting workout by id user_id={user.id}, workout_id={workout_id}")

    try:
        workout = await get_workout_by_id_service(
            session=session,
            id=workout_id,
            user_id=user.id,
        )

        logger.info(f"Workout received user_id={user.id}, workout_id={workout_id}")
        return workout

    except Exception as e:
        logger.exception(
            f"Failed to get workout by id user_id={user.id}, workout_id={workout_id}: {e}"
        )
        raise


@router.get("/by-name/{workout_name}", response_model=SWorkout)
async def get_workout_by_name(
    workout_name: str,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    logger.info(f"Getting workout by name user_id={user.id}, workout_name={workout_name}")

    try:
        workout = await get_workout_by_name_service(
            session=session,
            name=workout_name,
            user_id=user.id,
        )

        logger.info(
            f"Workout received by name user_id={user.id}, workout_name={workout_name}"
        )
        return workout

    except Exception as e:
        logger.exception(
            f"Failed to get workout by name user_id={user.id}, workout_name={workout_name}: {e}"
        )
        raise


@router.post(
    "/",
    response_model=SWorkout,
    dependencies=[Depends(limit_by_user(WORKOUTS_CREATE_USER))],
)
async def create_workout(
    workout: SWorkoutCreate,
    session: SessionDep,
    user: User = Depends(get_current_user),
) -> WorkoutModel:
    logger.info(f"Creating workout user_id={user.id}, title={workout.title}")

    try:
        created_workout = await create_workout_service(
            session=session,
            data=workout,
            user_id=user.id,
        )

        logger.info(
            f"Workout created user_id={user.id}, workout_id={created_workout.id}"
        )
        return created_workout

    except Exception as e:
        logger.exception(f"Failed to create workout user_id={user.id}: {e}")
        raise


@router.patch("/{workout_id}", response_model=SWorkout)
async def update_workout(
    workout_id: int,
    workout: SWorkoutUpdate,
    session: SessionDep,
    user: User = Depends(get_current_user),
) -> WorkoutModel:
    logger.info(f"Updating workout user_id={user.id}, workout_id={workout_id}")

    try:
        updated_workout = await update_workout_service(
            session=session,
            data=workout,
            id=workout_id,
            user_id=user.id,
        )

        logger.info(f"Workout updated user_id={user.id}, workout_id={workout_id}")
        return updated_workout

    except Exception as e:
        logger.exception(
            f"Failed to update workout user_id={user.id}, workout_id={workout_id}: {e}"
        )
        raise


@router.delete("/{workout_id}", response_model=SWorkout)
async def delete_workout(
    workout_id: int,
    session: SessionDep,
    user: User = Depends(get_current_user),
) -> WorkoutModel:
    logger.info(f"Deleting workout user_id={user.id}, workout_id={workout_id}")

    try:
        deleted_workout = await delete_workout_service(
            session=session,
            id=workout_id,
            user_id=user.id,
        )

        logger.info(f"Workout deleted user_id={user.id}, workout_id={workout_id}")
        return deleted_workout

    except Exception as e:
        logger.exception(
            f"Failed to delete workout user_id={user.id}, workout_id={workout_id}: {e}"
        )
        raise