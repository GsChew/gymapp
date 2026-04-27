from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Integer,
    ForeignKey,
    String,
    Boolean,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Model

if TYPE_CHECKING:
    from src.models.UserModels import User
    from src.models.WorkoutModels import WorkoutModel


class NotificationModel(Model):
    __tablename__ = "notifications"

    __table_args__ = (
        UniqueConstraint("user_id", "workout_id", name="uq_notification_user_workout"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )

    workout_id: Mapped[int | None] = mapped_column(
        ForeignKey("workouts.id"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="notifications",
    )

    workout: Mapped["WorkoutModel | None"] = relationship(
        "WorkoutModel",
        back_populates="notifications",
    )