from fastapi import APIRouter, Depends

from src.workoutExercise.service import (
    create_workoutexercise as create_workoutexercise_service,
    get_workoutexercises as get_workoutexercises_service,
    get_workoutexercise_by_ids as get_workoutexercise_by_ids_service,
    get_workoutexercises_by_status as get_workoutexercises_by_status_service,
    update_workoutexercise as update_workoutexercise_service,
    delete_workoutexercise as delete_workoutexercise_service,
)
from src.auth.dependencies import get_current_user
from src.database import SessionDep
from src.models.WorkoutModels import StatusTypes
from src.models.UserModels import User
from src.schemas.WorkoutSchemas import (
    SWorkoutExercise,
    SWorkoutExerciseCreate,
    SWorkoutExerciseUpdate,
)

router = APIRouter(prefix="/workout-exercises", tags=["Workout exercises"])


@router.post("/", response_model=SWorkoutExercise)
async def create_workoutexercise(
    data: SWorkoutExerciseCreate,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    return await create_workoutexercise_service(
        session=session,
        user_id=user.id,
        data=data,
    )


@router.get("/", response_model=list[SWorkoutExercise])
async def get_workoutexercises(
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    return await get_workoutexercises_service(
        session=session,
        user_id=user.id,
    )


@router.get("/status/{status}", response_model=list[SWorkoutExercise])
async def get_workoutexercises_by_status(
    status: StatusTypes,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    return await get_workoutexercises_by_status_service(
        session=session,
        user_id=user.id,
        status=status,
    )


@router.get("/{workout_id}/{exercise_id}", response_model=SWorkoutExercise)
async def get_workoutexercise_by_ids(
    workout_id: int,
    exercise_id: int,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    return await get_workoutexercise_by_ids_service(
        session=session,
        user_id=user.id,
        workout_id=workout_id,
        exercise_id=exercise_id,
    )


@router.patch("/{workout_id}/{exercise_id}", response_model=SWorkoutExercise)
async def update_workoutexercise(
    workout_id: int,
    exercise_id: int,
    data: SWorkoutExerciseUpdate,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    return await update_workoutexercise_service(
        session=session,
        user_id=user.id,
        workout_id=workout_id,
        exercise_id=exercise_id,
        data=data,
    )


@router.delete("/{workout_id}/{exercise_id}", response_model=SWorkoutExercise)
async def delete_workoutexercise(
    workout_id: int,
    exercise_id: int,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    return await delete_workoutexercise_service(
        session=session,
        workout_id=workout_id,
        exercise_id=exercise_id,
        user_id=user.id,
    )