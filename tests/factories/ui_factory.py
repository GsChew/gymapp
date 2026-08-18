from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tests.factories.user_factory import UserFactory
from tests.helpers.dates import future_datetime
from tests.helpers.generators import unique_suffix


@dataclass(frozen=True, slots=True)
class UiUserData:
    username: str
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class UiWorkoutData:
    title: str
    planned_at: str


class UiDataFactory:
    @staticmethod
    def user() -> UiUserData:
        payload = UserFactory.build()
        return UiUserData(
            username=payload["username"],
            email=payload["email"],
            password=payload["password"],
        )

    @staticmethod
    def workout() -> UiWorkoutData:
        planned_at: datetime = future_datetime(days=3)
        return UiWorkoutData(
            title=f"UI workout {unique_suffix()[:10]}",
            planned_at=planned_at.astimezone().strftime("%Y-%m-%dT%H:%M"),
        )
