from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

from src.models import NotificationModel
from src.repository.notifications import NotificationsRepository
from src.schemas.NotificationSchemas import SNotificationCreate


async def create_notification(
    session: AsyncSession,
    data: SNotificationCreate,
) -> NotificationModel:

    logger.info(
        f"Creating notification "
        f"user_id={data.user_id}"
    )

    try:

        notification = await NotificationsRepository.create_notification(
            session=session,
            data=data,
        )

    except SQLAlchemyError as e:

        await session.rollback()

        logger.exception(
            f"Database error while creating notification "
            f"user_id={data.user_id}"
        )

        raise ValueError("Не удалось создать уведомление") from e

    logger.info(
        f"Notification created successfully "
        f"notification_id={notification.id} "
        f"user_id={notification.user_id}"
    )

    return notification

async def get_notifications(
    session: AsyncSession,
    user_id: int,
    limit: int,
    offset: int,
    is_read: bool | None,
) -> list[NotificationModel]:

    logger.info(
        f"Getting notifications "
        f"user_id={user_id} "
        f"limit={limit} "
        f"offset={offset} "
        f"is_read={is_read}"
    )

    try:
        notifications = await NotificationsRepository.get_notifications(
            session=session,
            user_id=user_id,
            limit=limit,
            offset=offset,
            is_read=is_read,
        )

    except SQLAlchemyError as e:
        logger.exception(
            f"Database error while getting notifications "
            f"user_id={user_id}"
        )

        raise ValueError("Не удалось получить список уведомлений") from e

    logger.info(
        f"Notifications retrieved successfully "
        f"user_id={user_id} "
        f"count={len(notifications)}"
    )

    return notifications


async def get_notification_by_id(
    session: AsyncSession,
    user_id: int,
    id: int,
) -> NotificationModel:
    logger.info(
        f"Getting notification "
        f"user_id={user_id} "
        f"notification_id={id}"
    )

    try:
        notification = await NotificationsRepository.get_notification_by_id(
            session=session,
            user_id=user_id,
            id=id,
        )

    except SQLAlchemyError as e:
        logger.exception(
            f"Database error while getting notification "
            f"user_id={user_id} "
            f"notification_id={id}"
        )
        raise ValueError("Не удалось получить уведомление") from e

    if notification is None:
        logger.warning(
            f"Notification not found "
            f"user_id={user_id} "
            f"notification_id={id}"
        )
        raise ValueError("Уведомление не найдено")

    logger.info(
        f"Notification retrieved successfully "
        f"user_id={user_id} "
        f"notification_id={notification.id}"
    )

    return notification


async def mark_notification_as_read(
    session: AsyncSession,
    user_id: int,
    id: int,
) -> NotificationModel:

    logger.info(
        f"Marking notification as read "
        f"user_id={user_id} "
        f"notification_id={id}"
    )

    try:

        updated_notification = await NotificationsRepository.mark_notification_as_read(
            session=session,
            user_id=user_id,
            id=id,
        )

    except SQLAlchemyError as e:

        await session.rollback()

        logger.exception(
            f"Database error while updating notification "
            f"user_id={user_id} "
            f"notification_id={id}"
        )

        raise ValueError("Не удалось обновить уведомление") from e

    if updated_notification is None:

        logger.warning(
            f"Notification not found "
            f"user_id={user_id} "
            f"notification_id={id}"
        )

        raise ValueError("Уведомление не найдено")

    logger.info(
        f"Notification marked as read successfully "
        f"user_id={user_id} "
        f"notification_id={id}"
    )

    return updated_notification


async def delete_notification(
    session: AsyncSession,
    user_id: int,
    id: int,
) -> NotificationModel:
    logger.info(
        f"Deleting notification "
        f"user_id={user_id} "
        f"notification_id={id}"
    )

    try:
        deleted_notification = await NotificationsRepository.delete_notification(
            session=session,
            user_id=user_id,
            id=id,
        )

    except SQLAlchemyError as e:
        await session.rollback()

        logger.exception(
            f"Database error while deleting notification "
            f"user_id={user_id} "
            f"notification_id={id}"
        )

        raise ValueError("Не удалось удалить уведомление") from e

    if deleted_notification is None:
        logger.warning(
            f"Notification not found "
            f"user_id={user_id} "
            f"notification_id={id}"
        )
        raise ValueError("Уведомление не найдено")

    logger.info(
        f"Notification deleted successfully "
        f"user_id={user_id} "
        f"notification_id={id}"
    )

    return deleted_notification


async def get_unread_count_by_user_id(
    session: AsyncSession,
    user_id: int,
) -> int:
    logger.info(
        f"Getting unread notifications count "
        f"user_id={user_id}"
    )

    try:
        count = await NotificationsRepository.get_unread_count_by_user_id(
            session=session,
            user_id=user_id,
        )

    except SQLAlchemyError as e:
        logger.exception(
            f"Database error while getting unread notifications count "
            f"user_id={user_id}"
        )

        raise ValueError("Не удалось получить количество уведомлений") from e

    logger.info(
        f"Unread notifications count retrieved successfully "
        f"user_id={user_id} "
        f"count={count}"
    )

    return count