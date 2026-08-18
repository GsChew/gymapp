from datetime import date, datetime

from pydantic import BaseModel


class SProgressSummary(BaseModel):
    completed_workouts: int
    completed_this_week: int
    planned_workouts: int
    total_volume: float
    weekly_volume: float
    current_streak_weeks: int
    best_exercise_name: str | None = None
    best_exercise_volume: float = 0


class SWeeklyVolume(BaseModel):
    week_start: date
    volume: float
    completed_workouts: int


class SExerciseRecord(BaseModel):
    exercise_id: int
    exercise_name: str
    max_weight: float | None = None
    max_weight_at: datetime | None = None
    max_volume: float
    max_volume_at: datetime | None = None
    best_set_reps: int | None = None
    best_set_weight: float | None = None
    last_completed_at: datetime | None = None


class SExerciseHistoryItem(BaseModel):
    workout_id: int
    workout_title: str
    completed_at: datetime
    sets: int
    reps: int
    weight: float | None = None
    volume: float
