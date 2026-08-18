from __future__ import annotations

from typing import Any

from tests.helpers.generators import unique_suffix


class GoalFactory:
    @staticmethod
    def build(**overrides: Any) -> dict[str, Any]:
        payload = {
            "title": overrides.pop("title", f"QA goal {unique_suffix()[:10]}"),
            "metric": overrides.pop("metric", "kg"),
            "target_value": overrides.pop("target_value", 100.0),
            "current_value": overrides.pop("current_value", 0.0),
        }
        payload.update(overrides)
        return payload
