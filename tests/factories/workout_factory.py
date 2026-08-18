from __future__ import annotations

from typing import Any

from src.models.workout import StatusTypes
from tests.helpers.dates import future_datetime, to_api_datetime
from tests.helpers.generators import unique_suffix


class WorkoutFactory:
    @staticmethod
    def build(**overrides: Any) -> dict[str, Any]:
        planned_at = overrides.pop("planned_at", future_datetime(days=7))
        payload = {
            "title": overrides.pop(
                "title",
                f"QA workout {unique_suffix()[:10]}",
            ),
            "planned_at": (
                to_api_datetime(planned_at)
                if hasattr(planned_at, "astimezone")
                else planned_at
            ),
            "status": overrides.pop("status", StatusTypes.planned.value),
        }
        payload.update(overrides)
        return payload


class WorkoutExerciseFactory:
    @staticmethod
    def build(
        *,
        workout_id: int,
        exercise_id: int,
        **overrides: Any,
    ) -> dict[str, Any]:
        scheduled_at = overrides.pop("scheduled_at", future_datetime(days=7))
        payload = {
            "workout_id": workout_id,
            "exercise_id": exercise_id,
            "order_index": overrides.pop("order_index", 0),
            "sets": overrides.pop("sets", 3),
            "reps": overrides.pop("reps", 10),
            "weight": overrides.pop("weight", 20.0),
            "scheduled_at": (
                to_api_datetime(scheduled_at)
                if hasattr(scheduled_at, "astimezone")
                else scheduled_at
            ),
            "status": overrides.pop("status", StatusTypes.planned.value),
        }
        payload.update(overrides)
        return payload
