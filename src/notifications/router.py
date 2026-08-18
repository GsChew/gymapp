from fastapi import APIRouter, Depends, Query
from loguru import logger

from src.database import SessionDep
from src.auth.dependencies import get_current_user
from src.notifications.service import (
    get_notifications as get_notifications_service,
    get_notification_by_id as get_notification_by_id_service,
    mark_notification_as_read as mark_notification_as_read_service,
    delete_notification as delete_notification_service,
    get_unread_count_by_user_id as get_unread_count_by_user_id_service,
)
from src.schemas.notification import SNotification
from src.models.user import User


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[SNotification])
async def get_notifications(
    session: SessionDep,
    user: User = Depends(get_current_user),
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    is_read: bool | None = Query(default=None),
):
    """Return notifications for the current user."""
    logger.info(
        "Getting notifications user_id={} limit={} offset={} is_read={}",
        user.id,
        limit,
        offset,
        is_read,
    )
    return await get_notifications_service(
        session=session,
        user_id=user.id,
        limit=limit,
        offset=offset,
        is_read=is_read,
    )


@router.get("/unread-count")
async def get_unread_count_by_user_id(
        session: SessionDep,
        user: User = Depends(get_current_user),
):
    """Return the number of unread notifications for a user."""
    logger.info("Getting unread notification count user_id={}", user.id)
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
    """Return one notification owned by the user."""
    logger.info("Getting notification user_id={} notification_id={}", user.id, id)
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
    """Mark a notification as read for its owner."""
    logger.info("Marking notification as read user_id={} notification_id={}", user.id, id)
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
    """Delete a notification owned by the user."""
    logger.info("Deleting notification user_id={} notification_id={}", user.id, id)
    return await delete_notification_service(
        session=session,
        user_id=user.id,
        id=id,
    )
