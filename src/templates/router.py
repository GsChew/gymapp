from fastapi import APIRouter, Depends

from src.auth.dependencies import get_current_user
from src.database import SessionDep
from src.models.user import User
from src.templates.service import (
    create_template as create_template_service,
    create_workout_from_template as create_workout_from_template_service,
    delete_template as delete_template_service,
    get_templates as get_templates_service,
)
from src.schemas.workout import SWorkout, SWorkoutFromTemplate, SWorkoutTemplate, SWorkoutTemplateCreate

router = APIRouter(prefix="/templates", tags=["Templates"])


@router.get("/", response_model=list[SWorkoutTemplate])
async def get_templates(session: SessionDep, user: User = Depends(get_current_user)):
    """Return workout templates owned by the current user."""
    return await get_templates_service(session=session, user_id=user.id)


@router.post("/", response_model=SWorkoutTemplate)
async def create_template(
    data: SWorkoutTemplateCreate,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    """Create a reusable workout template."""
    return await create_template_service(session=session, user_id=user.id, data=data)


@router.post("/{template_id}/workouts", response_model=SWorkout)
async def create_workout_from_template(
    template_id: int,
    data: SWorkoutFromTemplate,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    """Schedule a new workout using a template's exercises."""
    return await create_workout_from_template_service(
        session=session,
        user_id=user.id,
        template_id=template_id,
        data=data,
    )


@router.delete("/{template_id}", response_model=SWorkoutTemplate)
async def delete_template(
    template_id: int,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    """Delete a workout template owned by the current user."""
    return await delete_template_service(
        session=session,
        user_id=user.id,
        template_id=template_id,
    )
