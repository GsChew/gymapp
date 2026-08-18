from fastapi import APIRouter, Depends
from loguru import logger

from src.database import SessionDep
from src.models.user import User, UserRole
from src.schemas.user import SUser
from src.auth.dependencies import require_roles
from src.users.service import (
    change_user_role as change_user_role_service,
    get_users as get_users_service,
)

router = APIRouter(
    prefix="/admin/users",
    tags=["admin users"],
)


@router.get("/", response_model=list[SUser])
async def get_users(
    session: SessionDep,
    trainer: User = Depends(require_roles(UserRole.trainer, UserRole.admin)),
):
    """Return users visible to trainers and administrators."""
    logger.info("Trainer users list requested trainer_id={}", trainer.id)
    return await get_users_service(session=session)


@router.patch("/{user_id}/role", response_model=SUser)
async def change_user_role(
    user_id: int,
    role: UserRole,
    session: SessionDep,
    admin: User = Depends(require_roles(UserRole.admin)),
):
    """Change a user role when requested by an administrator."""
    logger.info(
        "Changing user role admin_id={} target_user_id={} role={}",
        admin.id,
        user_id,
        role.value,
    )
    return await change_user_role_service(
        session=session,
        user_id=user_id,
        role=role,
    )
