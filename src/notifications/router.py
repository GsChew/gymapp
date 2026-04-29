from fastapi import APIRouter, Depends

from src.database import SessionDep
from src.auth.dependencies import get_current_user
from src.notifications.service import (
    get_notifications as get_notifications_service,
    get_notification_by_id as get_notification_by_id_service,
    mark_notification_as_read as mark_notification_as_read_service,
    delete_notification as delete_notification_service,
    get_unread_count_by_user_id as get_unread_count_by_user_id_service,
)
from src.schemas.NotificationSchemas import SNotification
from src.models.UserModels import User


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[SNotification])
async def get_notifications(
        session: SessionDep,
        user: User = Depends(get_current_user),
):
    return await get_notifications_service(
        session=session,
        user_id=user.id,
    )


@router.get("/unread-count")
async def get_unread_count_by_user_id(
        session: SessionDep,
        user: User = Depends(get_current_user),
):
    unread_count = await get_unread_count_by_user_id_service(
        session=session,
        user_id=user.id,
    )

    return {"unread_count": unread_count}


@router.get("/{id}", response_model=SNotification)
async def get_notification_by_id(
        id: int,
        session: SessionDep,
        user: User = Depends(get_current_user),
):
    return await get_notification_by_id_service(
        session=session,
        user_id=user.id,
        id=id,
    )


@router.patch("/{id}/read", response_model=SNotification)
async def mark_notification_as_read(
        id: int,
        session: SessionDep,
        user: User = Depends(get_current_user),
):
    return await mark_notification_as_read_service(
        session=session,
        user_id=user.id,
        id=id,
    )


@router.delete("/{id}", response_model=SNotification)
async def delete_notification(
        id: int,
        session: SessionDep,
        user: User = Depends(get_current_user),
):
    return await delete_notification_service(
        session=session,
        user_id=user.id,
        id=id,
    )