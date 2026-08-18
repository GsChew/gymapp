from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.models.workout import GoalStatus, StatusTypes, MuscleTypes, TrainTypes


class SWorkoutCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    planned_at: datetime
    status: StatusTypes = StatusTypes.planned
    remind_at: datetime | None = None


class SWorkout(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    planned_at: datetime
    status: StatusTypes
    remind_at: datetime | None = None
    notification_sent: bool
    wellness_energy: int | None = None
    wellness_sleep: int | None = None
    wellness_soreness: int | None = None
    completion_notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SWorkoutUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    planned_at: datetime | None = None
    status: StatusTypes | None = None
    remind_at: datetime | None = None
    wellness_energy: int | None = Field(default=None, ge=1, le=5)
    wellness_sleep: int | None = Field(default=None, ge=1, le=5)
    wellness_soreness: int | None = Field(default=None, ge=1, le=5)
    completion_notes: str | None = Field(default=None, max_length=1000)


class SExerciseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    train: TrainTypes
    muscle: MuscleTypes | None = None
    video_url: str | None = None
    muscle_image_url: str | None = None


class SExercise(BaseModel):
    id: int
    name: str
    description: str | None = None
    train: TrainTypes
    muscle: MuscleTypes | None = None
    video_url: str | None = None
    muscle_image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SExerciseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    train: TrainTypes | None = None
    muscle: MuscleTypes | None = None
    video_url: str | None = None
    muscle_image_url: str | None = None


class SWorkoutExerciseCreate(BaseModel):
    workout_id: int
    exercise_id: int
    order_index: int = Field(ge=0)
    sets: int = Field(ge=1)
    reps: int = Field(ge=1)
    weight: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)
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
    order_index: int | None = Field(default=None, ge=0)
    sets: int | None = Field(default=None, ge=1)
    reps: int | None = Field(default=None, ge=1)
    weight: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)
    scheduled_at: datetime | None = None
    status: StatusTypes | None = None
    completed_at: datetime | None = None


class SWorkoutExerciseComplete(BaseModel):
    exercise_id: int
    sets: int | None = Field(default=None, ge=1)
    reps: int | None = Field(default=None, ge=1)
    weight: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)


class SWorkoutComplete(BaseModel):
    completed_at: datetime | None = None
    exercises: list[SWorkoutExerciseComplete] = Field(default_factory=list)
    wellness_energy: int | None = Field(default=None, ge=1, le=5)
    wellness_sleep: int | None = Field(default=None, ge=1, le=5)
    wellness_soreness: int | None = Field(default=None, ge=1, le=5)
    completion_notes: str | None = Field(default=None, max_length=1000)


class STemplateExercise(BaseModel):
    exercise_id: int
    order_index: int = Field(ge=0)
    sets: int = Field(ge=1)
    reps: int = Field(ge=1)
    weight: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)


class SWorkoutTemplateCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    exercises: list[STemplateExercise] = Field(default_factory=list)


class SWorkoutTemplate(BaseModel):
    id: int
    user_id: int
    title: str
    description: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SWorkoutFromTemplate(BaseModel):
    planned_at: datetime
    remind_at: datetime | None = None


class SUserGoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    metric: str = Field(min_length=1, max_length=80)
    target_value: float = Field(gt=0)
    current_value: float = Field(default=0, ge=0)
    deadline_at: datetime | None = None


class SUserGoalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    metric: str | None = Field(default=None, min_length=1, max_length=80)
    target_value: float | None = Field(default=None, gt=0)
    current_value: float | None = Field(default=None, ge=0)
    status: GoalStatus | None = None
    deadline_at: datetime | None = None


class SUserGoal(BaseModel):
    id: int
    user_id: int
    title: str
    metric: str
    target_value: float
    current_value: float
    status: GoalStatus
    deadline_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
