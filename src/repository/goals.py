from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.workout import UserGoal
from src.schemas.workout import SUserGoalCreate, SUserGoalUpdate


class GoalRepository:
    @classmethod
    async def get_goals(cls, session: AsyncSession, user_id: int) -> list[UserGoal]:
        """Return goals owned by a user."""
        result = await session.execute(
            select(UserGoal)
            .where(UserGoal.user_id == user_id)
            .order_by(UserGoal.created_at.desc())
        )
        return list(result.scalars().all())

    @classmethod
    async def get_goal(
        cls,
        session: AsyncSession,
        user_id: int,
        goal_id: int,
    ) -> UserGoal | None:
        """Return one goal owned by a user."""
        result = await session.execute(
            select(UserGoal).where(
                UserGoal.id == goal_id,
                UserGoal.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    @classmethod
    async def create_goal(
        cls,
        session: AsyncSession,
        user_id: int,
        data: SUserGoalCreate,
    ) -> UserGoal:
        """Create a goal for a user."""
        goal = UserGoal(user_id=user_id, **data.model_dump())
        session.add(goal)
        await session.commit()
        await session.refresh(goal)
        return goal

    @classmethod
    async def update_goal(
        cls,
        session: AsyncSession,
        user_id: int,
        goal_id: int,
        data: SUserGoalUpdate,
    ) -> UserGoal | None:
        """Update one goal owned by a user."""
        goal = await cls.get_goal(session=session, user_id=user_id, goal_id=goal_id)
        if goal is None:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(goal, field, value)

        await session.commit()
        await session.refresh(goal)
        return goal

    @classmethod
    async def delete_goal(
        cls,
        session: AsyncSession,
        user_id: int,
        goal_id: int,
    ) -> UserGoal | None:
        """Delete one goal owned by a user."""
        goal = await cls.get_goal(session=session, user_id=user_id, goal_id=goal_id)
        if goal is None:
            return None

        await session.delete(goal)
        await session.commit()
        return goal
