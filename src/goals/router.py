from fastapi import APIRouter, Depends

from src.auth.dependencies import get_current_user
from src.database import SessionDep
from src.models.user import User
from src.goals.service import (
    create_goal as create_goal_service,
    delete_goal as delete_goal_service,
    get_goals as get_goals_service,
    update_goal as update_goal_service,
)
from src.schemas.workout import SUserGoal, SUserGoalCreate, SUserGoalUpdate

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.get("/", response_model=list[SUserGoal])
async def get_goals(session: SessionDep, user: User = Depends(get_current_user)):
    """Return goals owned by the current user."""
    return await get_goals_service(session=session, user_id=user.id)


@router.post("/", response_model=SUserGoal)
async def create_goal(
    data: SUserGoalCreate,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    """Create a user goal."""
    return await create_goal_service(session=session, user_id=user.id, data=data)


@router.patch("/{goal_id}", response_model=SUserGoal)
async def update_goal(
    goal_id: int,
    data: SUserGoalUpdate,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    """Update a user goal."""
    return await update_goal_service(
        session=session,
        user_id=user.id,
        goal_id=goal_id,
        data=data,
    )


@router.delete("/{goal_id}", response_model=SUserGoal)
async def delete_goal(
    goal_id: int,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    """Delete a user goal."""
    return await delete_goal_service(
        session=session,
        user_id=user.id,
        goal_id=goal_id,
    )
