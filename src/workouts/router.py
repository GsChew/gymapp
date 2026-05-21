from fastapi import APIRouter, Depends, Query

from models.WorkoutModels import StatusTypes
from src.auth.dependencies import get_current_user
from src.models.UserModels import User
from src.models.WorkoutModels import WorkoutModel
from src.database import SessionDep
from src.schemas.WorkoutSchemas import SWorkoutCreate, SWorkoutUpdate
from src.workouts.service import (
    get_workouts as get_workouts_service,
    get_workout_by_id as get_workout_by_id_service,
    get_workout_by_name as get_workout_by_name_service,
    create_workout as create_workout_service,
    update_workout as update_workout_service,
    delete_workout as delete_workout_service,
)

router = APIRouter(prefix="/workouts", tags=["Workouts"])


@router.get("/", response_model=list[SWorkout])
async def get_workouts(
    session: SessionDep,
    user: User = Depends(get_current_user),
    limit: int = Query(default=15, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: StatusTypes | None = None,
):
    return await get_workouts_service(
        session=session,
        user_id=user.id,
        limit=limit,
        offset=offset,
        status=status,
    )


@router.get("/{workout_id}")
async def get_workout_by_id(
    workout_id: int,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    return await get_workout_by_id_service(
        session=session,
        id=workout_id,
        user_id=user.id,
    )


@router.get("/by-name/{workout_name}")
async def get_workout_by_name(
    workout_name: str,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    return await get_workout_by_name_service(
        session=session,
        name=workout_name,
        user_id=user.id,
    )


@router.post("/", response_model=None)
async def create_workout(
    workout: SWorkoutCreate,
    session: SessionDep,
    user: User = Depends(get_current_user),
) -> WorkoutModel:
    return await create_workout_service(
        session=session,
        data=workout,
        user_id=user.id,
    )


@router.patch("/{id}", response_model=None)
async def update_workout(
    id: int,
    workout: SWorkoutUpdate,
    session: SessionDep,
    user: User = Depends(get_current_user),
) -> WorkoutModel:
    return await update_workout_service(
        session=session,
        data=workout,
        id=id,
        user_id=user.id,
    )


@router.delete("/{id}", response_model=None)
async def delete_workout(
    id: int,
    session: SessionDep,
    user: User = Depends(get_current_user),
) -> WorkoutModel:
    return await delete_workout_service(
        session=session,
        id=id,
        user_id=user.id,
    )