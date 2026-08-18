from fastapi import APIRouter, Depends

from src.workout_exercises.service import (
    create_workout_exercise as create_workout_exercise_service,
    get_workout_exercises as get_workout_exercises_service,
    get_workout_exercise_by_ids as get_workout_exercise_by_ids_service,
    get_workout_exercises_by_status as get_workout_exercises_by_status_service,
    update_workout_exercise as update_workout_exercise_service,
    delete_workout_exercise as delete_workout_exercise_service,
)
from src.auth.dependencies import get_current_user
from src.database import SessionDep
from src.models.workout import StatusTypes
from src.models.user import User
from src.schemas.workout import (
    SWorkoutExercise,
    SWorkoutExerciseCreate,
    SWorkoutExerciseUpdate,
)

router = APIRouter(prefix="/workout-exercises", tags=["Workout exercises"])


@router.post("/", response_model=SWorkoutExercise)
async def create_workout_exercise(
    data: SWorkoutExerciseCreate,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    """Add an exercise to a workout owned by the user."""
    return await create_workout_exercise_service(
        session=session,
        user_id=user.id,
        data=data,
    )


@router.get("/", response_model=list[SWorkoutExercise])
async def get_workout_exercises(
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    """Return workout exercise links for the current user."""
    return await get_workout_exercises_service(
        session=session,
        user_id=user.id,
    )


@router.get("/status/{status}", response_model=list[SWorkoutExercise])
async def get_workout_exercises_by_status(
    status: StatusTypes,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    """Return workout exercise links with the requested status."""
    return await get_workout_exercises_by_status_service(
        session=session,
        user_id=user.id,
        status=status,
    )


@router.get("/{workout_id}/{exercise_id}", response_model=SWorkoutExercise)
async def get_workout_exercise_by_ids(
    workout_id: int,
    exercise_id: int,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    """Return one workout exercise link by workout and exercise ids."""
    return await get_workout_exercise_by_ids_service(
        session=session,
        user_id=user.id,
        workout_id=workout_id,
        exercise_id=exercise_id,
    )


@router.patch("/{workout_id}/{exercise_id}", response_model=SWorkoutExercise)
async def update_workout_exercise(
    workout_id: int,
    exercise_id: int,
    data: SWorkoutExerciseUpdate,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    """Update an exercise link in a workout owned by the user."""
    return await update_workout_exercise_service(
        session=session,
        user_id=user.id,
        workout_id=workout_id,
        exercise_id=exercise_id,
        data=data,
    )


@router.delete("/{workout_id}/{exercise_id}", response_model=SWorkoutExercise)
async def delete_workout_exercise(
    workout_id: int,
    exercise_id: int,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    """Delete an exercise link from a workout owned by the user."""
    return await delete_workout_exercise_service(
        session=session,
        workout_id=workout_id,
        exercise_id=exercise_id,
        user_id=user.id,
    )
