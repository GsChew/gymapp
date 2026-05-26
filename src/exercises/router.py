from fastapi import APIRouter, Query, Depends

from src.schemas.WorkoutSchemas import SExercise
from src.models.WorkoutModels import MuscleTypes, TrainTypes

from src.database import SessionDep
from src.schemas.WorkoutSchemas import SExerciseCreate, SExerciseUpdate
from src.exercises.service import (
    get_exercise_by_id as get_exercise_by_id_service,
    get_exercises as get_exercises_service,
    delete_exercise as delete_exercise_service,
    update_exercise as update_exercise_service,
    create_exercise as create_exercise_service,
)
from src.auth.dependencies import get_current_user, require_roles
from src.models.UserModels import User, UserRole

router = APIRouter(prefix="/exercises", tags=["Exercises"])


@router.get("/", response_model=list[SExercise])
async def get_exercises(
    session: SessionDep,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    muscle: MuscleTypes | None = None,
    train_type: TrainTypes | None = None,
    user: User = Depends(get_current_user),
):
    return await get_exercises_service(
        session=session,
        limit=limit,
        offset=offset,
        muscle=muscle,
        train_type=train_type,
    )


@router.get("/{id}", response_model=SExercise)
async def get_exercise_by_id(
    id: int,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    return await get_exercise_by_id_service(
        session=session,
        id=id,
    )


@router.post("/", response_model=SExercise)
async def create_exercise(
    data: SExerciseCreate,
    session: SessionDep,
    user: User = Depends(require_roles(UserRole.trainer, UserRole.admin)),
):
    return await create_exercise_service(
        session=session,
        data=data,
    )


@router.patch("/{id}", response_model=SExercise)
async def update_exercise(
    id: int,
    data: SExerciseUpdate,
    session: SessionDep,
    user: User = Depends(require_roles(UserRole.trainer, UserRole.admin)),
):
    return await update_exercise_service(
        session=session,
        id=id,
        data=data,
    )


@router.delete("/{id}", response_model=SExercise)
async def delete_exercise(
    id: int,
    session: SessionDep,
    user: User = Depends(require_roles(UserRole.admin)),
):
    return await delete_exercise_service(
        session=session,
        id=id,
    )