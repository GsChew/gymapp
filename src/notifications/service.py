from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.models import NotificationModel
from src.repository.notifications import NotificationsRepository
from src.schemas.NotificationSchemas import SNotificationCreate


async def create_notification(
        session: AsyncSession,
        data: SNotificationCreate,
) -> NotificationModel:
    try:
        return await NotificationsRepository.create_notification(
            session=session,
            data=data,
        )

    except SQLAlchemyError as e:
        await session.rollback()
        raise ValueError("Не удалось создать уведомление") from e


async def get_notifications(
        session: AsyncSession,
        user_id: int,
) -> list[NotificationModel]:
    try:
        return await NotificationsRepository.get_notifications(
            session=session,
            user_id=user_id,
        )

    except SQLAlchemyError as e:
        raise ValueError("Не удалось получить список уведомлений") from e


async def get_notification_by_id(
        session: AsyncSession,
        user_id: int,
        id: int,
) -> NotificationModel | None:
    try:
        return await NotificationsRepository.get_notification_by_id(
            session=session,
            user_id=user_id,
            id=id,
        )

    except SQLAlchemyError as e:
        raise ValueError("Не удалось получить уведомление") from e


async def mark_notification_as_read(
        session: AsyncSession,
        user_id: int,
        id: int,
) -> NotificationModel:
    try:
        updated_notification = await NotificationsRepository.mark_notification_as_read(
            session=session,
            user_id=user_id,
            id=id,
        )

    except SQLAlchemyError as e:
        await session.rollback()
        raise ValueError("Не удалось обновить уведомление") from e

    if updated_notification is None:
        raise ValueError("Уведомление не найдено")

    return updated_notification


async def delete_notification(
        session: AsyncSession,
        user_id: int,
        id: int,
) -> NotificationModel:
    try:
        deleted_notification = await NotificationsRepository.delete_notification(
            session=session,
            user_id=user_id,
            id=id,
        )

    except SQLAlchemyError as e:
        await session.rollback()
        raise ValueError("Не удалось удалить уведомление") from e

    if deleted_notification is None:
        raise ValueError("Уведомление не найдено")

    return deleted_notification


async def get_unread_count_by_user_id(
        session: AsyncSession,
        user_id: int,
) -> int:
    try:
        return await NotificationsRepository.get_unread_count_by_user_id(
            session=session,
            user_id=user_id,
        )

    except SQLAlchemyError as e:
        raise ValueError("Не удалось получить количество уведомлений") from e