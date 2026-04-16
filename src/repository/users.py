from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.UserModels import User
from src.schemas.UserSchemas import SUserUpdate

class UserRepository:

    @classmethod
    async def get_user(
        cls,
        user_id: int,
        session: AsyncSession,
    ) -> User | None:
        return await session.get(User, user_id)

    @classmethod
    async def get_user_by_username(
        cls,
        username: str,
        session: AsyncSession,
    ) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def create_user(
        cls,
        user_data: dict,
        session: AsyncSession,
    ) -> User:
        user = User(**user_data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @classmethod
    async def update_user(
        cls,
        user_id: int,
        data: SUserUpdate,
        session: AsyncSession,
    ) -> User | None:
        user = await cls.get_user(user_id, session)

        if user is None:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(user, field, value)

        await session.commit()
        await session.refresh(user)
        return user

    @classmethod
    async def delete_user(
        cls,
        user_id: int,
        session: AsyncSession,
    ) -> User | None:
        user = await cls.get_user(user_id, session)

        if user is None:
            return None

        await session.delete(user)
        await session.commit()
        return user