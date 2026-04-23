from fastapi import APIRouter

from src.schemas.WorkoutSchemas import SExercise

from src.database import SessionDep
from src.models.WorkoutModels import ExerciseModel
from src.schemas.WorkoutSchemas import SExerciseCreate, SExerciseUpdate
from src.exercises.service import (
    get_exercise_by_id as get_exercise_by_id_service,
    get_exercises as get_exercises_service,
    delete_exercise as delete_exercise_service,
    update_exercise as update_exercise_service,
    create_exercise as create_exercise_service,
)

router = APIRouter(prefix="/exercises", tags=["Exercises"])


@router.get("/", response_model=list[SExercise])
async def get_exercises(
    session: SessionDep,
):
    return await get_exercises_service(session=session)


@router.get("/{id}", response_model=SExercise)
async def get_exercise_by_id(
    id: int,
    session: SessionDep,
):
    return await get_exercise_by_id_service(
        session=session,
        id=id,
    )


@router.post("/", response_model=SExercise)
async def create_exercise(
    data: SExerciseCreate,
    session: SessionDep,
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
):
    return await delete_exercise_service(
        session=session,
        id=id,
    )