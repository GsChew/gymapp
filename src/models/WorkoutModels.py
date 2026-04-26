import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Model

if TYPE_CHECKING:
    from src.models.UserModels import User


class StatusTypes(enum.Enum):
    planned = "запланировано"
    done = "сделано"


class TrainTypes(enum.Enum):
    strength_train = "силовая_тренировка"
    cardio = "кардио"
    stretching = "растяжка"


class MuscleTypes(enum.Enum):
    pectorals = "грудные"
    abdominal_muscles = "пресс"
    lats = "широчайшие"
    traps = "трапециевидные"
    delts = "плечи"
    biceps = "бицепс"
    triceps = "трицепс"
    glutes = "ягодичные"
    quadriceps = "квадрицепс"
    hamstrings = "задняя_часть_бедра"
    gastrocnemius = "икры"


class WorkoutModel(Model):
    __tablename__ = "workouts"

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

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    planned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    status: Mapped[StatusTypes] = mapped_column(
        Enum(StatusTypes, name="workout_status_types"),
        nullable=False,
        default=StatusTypes.planned,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="workouts",
    )

    exercise_links: Mapped[list["workoutExercise"]] = relationship(
        "workoutExercise",
        back_populates="workout",
        cascade="all, delete-orphan",
    )


class ExerciseModel(Model):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    train: Mapped[TrainTypes] = mapped_column(
        Enum(TrainTypes, name="train_types"),
        nullable=False,
    )

    muscle: Mapped[MuscleTypes | None] = mapped_column(
        Enum(MuscleTypes, name="muscle_types"),
        nullable=True,
    )

    workout_links: Mapped[list["workoutExercise"]] = relationship(
        "workoutExercise",
        back_populates="exercise",
        cascade="all, delete-orphan",
    )


class WorkoutExercise(Model):
    __tablename__ = "workout_exercises"

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id"),
        primary_key=True,
    )

    workout_id: Mapped[int] = mapped_column(
        ForeignKey("workouts.id"),
        primary_key=True,
    )

    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    sets: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    reps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    weight: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    status: Mapped[StatusTypes] = mapped_column(
        Enum(StatusTypes, name="status_types"),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    workout: Mapped["WorkoutModel"] = relationship(
        "WorkoutModel",
        back_populates="exercise_links",
    )

    exercise: Mapped["ExerciseModel"] = relationship(
        "ExerciseModel",
        back_populates="workout_links",
    )