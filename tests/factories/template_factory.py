from __future__ import annotations

from typing import Any

from tests.helpers.generators import unique_suffix


class TemplateFactory:
    @staticmethod
    def build(
        *,
        exercise_id: int | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        exercises = []
        if exercise_id is not None:
            exercises.append(
                {
                    "exercise_id": exercise_id,
                    "order_index": 0,
                    "sets": 3,
                    "reps": 10,
                    "weight": 20,
                }
            )
        payload = {
            "title": overrides.pop(
                "title",
                f"QA template {unique_suffix()[:10]}",
            ),
            "description": overrides.pop("description", "Reusable QA template"),
            "exercises": overrides.pop("exercises", exercises),
        }
        payload.update(overrides)
        return payload
