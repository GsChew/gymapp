import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Model

if TYPE_CHECKING:
    from src.models.notification import NotificationModel
    from src.models.user import User


class StatusTypes(enum.Enum):
    planned = "запланировано"
    done = "сделано"
    missed = "пропущено"


class GoalStatus(enum.Enum):
    active = "активна"
    done = "достигнута"
    archived = "архив"


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

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)

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
        default=StatusTypes.planned,
        nullable=False,
    )

    remind_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    notification_task_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    notification_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    wellness_energy: Mapped[int | None] = mapped_column(Integer, nullable=True)
    wellness_sleep: Mapped[int | None] = mapped_column(Integer, nullable=True)
    wellness_soreness: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="workouts",
    )

    exercise_links: Mapped[list["WorkoutExercise"]] = relationship(
        "WorkoutExercise",
        back_populates="workout",
        cascade="all, delete-orphan",
    )

    notifications: Mapped[list["NotificationModel"]] = relationship(
        "NotificationModel",
        back_populates="workout",
    )


class WorkoutTemplate(Model):
    __tablename__ = "workout_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    exercises: Mapped[list["WorkoutTemplateExercise"]] = relationship(
        "WorkoutTemplateExercise",
        back_populates="template",
        cascade="all, delete-orphan",
    )


class WorkoutTemplateExercise(Model):
    __tablename__ = "workout_template_exercises"

    template_id: Mapped[int] = mapped_column(
        ForeignKey("workout_templates.id"),
        primary_key=True,
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id"),
        primary_key=True,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    template: Mapped["WorkoutTemplate"] = relationship(
        "WorkoutTemplate",
        back_populates="exercises",
    )
    exercise: Mapped["ExerciseModel"] = relationship("ExerciseModel")


class UserGoal(Model):
    __tablename__ = "user_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    metric: Mapped[str] = mapped_column(String(80), nullable=False)
    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    current_value: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    status: Mapped[GoalStatus] = mapped_column(
        Enum(GoalStatus, name="goal_status_types"),
        default=GoalStatus.active,
        nullable=False,
    )
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
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

    workout_links: Mapped[list["WorkoutExercise"]] = relationship(
        "WorkoutExercise",
        back_populates="exercise",
        cascade="all, delete-orphan",
    )

    video_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    muscle_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
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
