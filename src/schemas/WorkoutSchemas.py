from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.models.WorkoutModels import StatusTypes, MuscleTypes, TrainTypes


class SWorkoutCreate(BaseModel):
    title: str
    planned_at: datetime
    status: StatusTypes = StatusTypes.planned


class SWorkout(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    planned_at: datetime
    status: StatusTypes

    model_config = ConfigDict(from_attributes=True)


class SWorkoutUpdate(BaseModel):
    title: str | None = None
    planned_at: datetime | None = None
    status: StatusTypes | None = None


class SExerciseCreate(BaseModel):
    name: str
    description: str | None = None
    train: TrainTypes
    muscle: MuscleTypes | None = None


class SExercise(BaseModel):
    id: int
    name: str
    description: str | None = None
    train: TrainTypes
    muscle: MuscleTypes | None = None

    model_config = ConfigDict(from_attributes=True)


class SExerciseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    train: TrainTypes | None = None
    muscle: MuscleTypes | None = None


class SWorkoutExerciseCreate(BaseModel):
    exercise_id: int
    order_index: int
    sets: int
    reps: int
    weight: float | None = None
    notes: str | None = None
    scheduled_at: datetime
    status: StatusTypes = StatusTypes.planned
    completed_at: datetime | None = None


class SWorkoutExercise(BaseModel):
    exercise_id: int
    workout_id: int
    order_index: int
    sets: int
    reps: int
    weight: float | None = None
    notes: str | None = None
    scheduled_at: datetime
    status: StatusTypes
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SWorkoutExerciseUpdate(BaseModel):
    order_index: int | None = None
    sets: int | None = None
    reps: int | None = None
    weight: float | None = None
    notes: str | None = None
    scheduled_at: datetime | None = None
    status: StatusTypes | None = None
    completed_at: datetime | None = None