from datetime import UTC, datetime
from typing import TYPE_CHECKING
from enum import Enum as PyEnum

from sqlalchemy import Enum as SqlEnum

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Model

if TYPE_CHECKING:
    from src.models.notification import NotificationModel
    from src.models.workout import WorkoutModel

class UserRole(str, PyEnum):
    user = "user"
    trainer = "trainer"
    admin = "admin"

class User(Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    username: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    workouts: Mapped[list["WorkoutModel"]] = relationship(
        "WorkoutModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    notifications: Mapped[list["NotificationModel"]] = relationship(
        "NotificationModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole),
        default=UserRole.user,
        nullable=False,
    )
