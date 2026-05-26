from fastapi import APIRouter, Depends

from src.database import SessionDep
from src.models.UserModels import User, UserRole
from src.auth.dependencies import require_roles
from src.users.service import change_user_role as change_user_role_service

router = APIRouter(
    prefix="/admin/users",
    tags=["admin users"],
)


@router.patch("/{user_id}/role")
async def change_user_role(
    user_id: int,
    role: UserRole,
    session: SessionDep,
    admin: User = Depends(require_roles(UserRole.admin)),
):
    return await change_user_role_service(
        session=session,
        user_id=user_id,
        role=role,
    )