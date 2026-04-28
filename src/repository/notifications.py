from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.models import NotificationModel
from src.schemas.NotificationSchemas import SNotificationCreate


class NotificationsRepository:

    @classmethod
    async def create_notification(
            cls,
            session: AsyncSession,
            data: SNotificationCreate,
    ) -> NotificationModel:
        notification = NotificationModel(**data.model_dump())

        session.add(notification)
        await session.commit()
        await session.refresh(notification)

        return notification

    @classmethod
    async def get_notifications(
            cls,
            session: AsyncSession,
            user_id: int,
    ) -> list[NotificationModel]:
        stmt = (
            select(NotificationModel)
            .where(NotificationModel.user_id == user_id)
            .order_by(NotificationModel.created_at.desc())
        )

        result = await session.execute(stmt)

        return list(result.scalars().all())

    @classmethod
    async def get_notification_by_id(
            cls,
            session: AsyncSession,
            user_id: int,
            id: int,
    ) -> NotificationModel | None:
        stmt = select(NotificationModel).where(
            NotificationModel.user_id == user_id,
            NotificationModel.id == id,
        )

        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @classmethod
    async def mark_notification_as_read(
            cls,
            session: AsyncSession,
            user_id: int,
            id: int,
    ) -> NotificationModel | None:
        notification = await cls.get_notification_by_id(
            session=session,
            user_id=user_id,
            id=id,
        )

        if notification is None:
            return None

        notification.is_read = True

        await session.commit()
        await session.refresh(notification)

        return notification

    @classmethod
    async def delete_notification(
            cls,
            session: AsyncSession,
            user_id: int,
            id: int,
    ) -> NotificationModel | None:
        notification = await cls.get_notification_by_id(
            session=session,
            user_id=user_id,
            id=id,
        )

        if notification is None:
            return None

        await session.delete(notification)
        await session.commit()

        return notification

    @classmethod
    async def get_unread_count_by_user_id(
            cls,
            session: AsyncSession,
            user_id: int,
    ) -> int:
        stmt = select(func.count()).where(
            NotificationModel.user_id == user_id,
            NotificationModel.is_read == False,
        )

        result = await session.execute(stmt)

        return result.scalar_one()