from __future__ import annotations

from typing import Any

from src.models.workout import MuscleTypes, TrainTypes
from tests.helpers.generators import unique_suffix


class ExerciseFactory:
    @staticmethod
    def build(**overrides: Any) -> dict[str, Any]:
        payload = {
            "name": overrides.pop(
                "name",
                f"QA exercise {unique_suffix()[:10]}",
            ),
            "description": overrides.pop("description", "Created by automated tests"),
            "train": overrides.pop("train", TrainTypes.strength_train.value),
            "muscle": overrides.pop("muscle", MuscleTypes.quadriceps.value),
        }
        payload.update(overrides)
        return payload
