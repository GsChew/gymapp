from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from httpx import Response

from tests.clients.base_client import BaseClient


class AuthClient:
    def __init__(self, client: BaseClient) -> None:
        self.client = client

    async def register(self, payload: dict[str, Any]) -> Response:
        return await self.client.post("/auth/register", json=payload)

    async def login(self, payload: dict[str, Any]) -> Response:
        return await self.client.post("/auth/login", json=payload)

    async def refresh(self, refresh_token: str) -> Response:
        return await self.client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )

    async def me(self, **kwargs: Any) -> Response:
        return await self.client.get("/auth/me", **kwargs)


class UsersClient:
    def __init__(self, client: BaseClient) -> None:
        self.client = client

    async def list_users(self) -> Response:
        return await self.client.get("/admin/users/")

    async def change_role(self, user_id: int, role: str) -> Response:
        return await self.client.patch(
            f"/admin/users/{user_id}/role",
            params={"role": role},
        )


class WorkoutsClient:
    def __init__(self, client: BaseClient) -> None:
        self.client = client

    async def create_workout(self, payload: dict[str, Any]) -> Response:
        return await self.client.post("/workouts/", json=payload)

    async def create_starter_plan(self) -> Response:
        return await self.client.post("/workouts/starter-plan")

    async def list_workouts(self, **params: Any) -> Response:
        return await self.client.get("/workouts/", params=params or None)

    async def get_workout(self, workout_id: int | str) -> Response:
        return await self.client.get(f"/workouts/{workout_id}")

    async def get_by_name(self, title: str) -> Response:
        return await self.client.get(f"/workouts/by-name/{title}")

    async def update_workout(
        self,
        workout_id: int,
        payload: dict[str, Any],
    ) -> Response:
        return await self.client.patch(f"/workouts/{workout_id}", json=payload)

    async def complete_workout(
        self,
        workout_id: int,
        payload: dict[str, Any],
    ) -> Response:
        return await self.client.post(
            f"/workouts/{workout_id}/complete",
            json=payload,
        )

    async def delete_workout(self, workout_id: int) -> Response:
        return await self.client.delete(f"/workouts/{workout_id}")


class ExercisesClient:
    def __init__(self, client: BaseClient) -> None:
        self.client = client

    async def create_exercise(self, payload: dict[str, Any]) -> Response:
        return await self.client.post("/exercises/", json=payload)

    async def list_exercises(self, **params: Any) -> Response:
        return await self.client.get("/exercises/", params=params or None)

    async def get_exercise(self, exercise_id: int | str) -> Response:
        return await self.client.get(f"/exercises/{exercise_id}")

    async def update_exercise(
        self,
        exercise_id: int,
        payload: dict[str, Any],
    ) -> Response:
        return await self.client.patch(f"/exercises/{exercise_id}", json=payload)

    async def delete_exercise(self, exercise_id: int) -> Response:
        return await self.client.delete(f"/exercises/{exercise_id}")


class WorkoutExercisesClient:
    def __init__(self, client: BaseClient) -> None:
        self.client = client

    async def create_link(self, payload: dict[str, Any]) -> Response:
        return await self.client.post("/workout-exercises/", json=payload)

    async def list_links(self) -> Response:
        return await self.client.get("/workout-exercises/")

    async def list_by_status(self, status: str) -> Response:
        return await self.client.get(f"/workout-exercises/status/{status}")

    async def get_link(self, workout_id: int, exercise_id: int) -> Response:
        return await self.client.get(
            f"/workout-exercises/{workout_id}/{exercise_id}"
        )

    async def update_link(
        self,
        workout_id: int,
        exercise_id: int,
        payload: dict[str, Any],
    ) -> Response:
        return await self.client.patch(
            f"/workout-exercises/{workout_id}/{exercise_id}",
            json=payload,
        )

    async def delete_link(self, workout_id: int, exercise_id: int) -> Response:
        return await self.client.delete(
            f"/workout-exercises/{workout_id}/{exercise_id}"
        )


class NotificationsClient:
    def __init__(self, client: BaseClient) -> None:
        self.client = client

    async def list_notifications(self, **params: Any) -> Response:
        return await self.client.get("/notifications", params=params or None)

    async def unread_count(self) -> Response:
        return await self.client.get("/notifications/unread-count")

    async def get_notification(self, notification_id: int) -> Response:
        return await self.client.get(f"/notifications/{notification_id}")

    async def mark_read(self, notification_id: int) -> Response:
        return await self.client.patch(f"/notifications/{notification_id}/read")

    async def delete_notification(self, notification_id: int) -> Response:
        return await self.client.delete(f"/notifications/{notification_id}")


class GoalsClient:
    def __init__(self, client: BaseClient) -> None:
        self.client = client

    async def create_goal(self, payload: dict[str, Any]) -> Response:
        return await self.client.post("/goals/", json=payload)

    async def list_goals(self) -> Response:
        return await self.client.get("/goals/")

    async def update_goal(self, goal_id: int, payload: dict[str, Any]) -> Response:
        return await self.client.patch(f"/goals/{goal_id}", json=payload)

    async def delete_goal(self, goal_id: int) -> Response:
        return await self.client.delete(f"/goals/{goal_id}")


class TemplatesClient:
    def __init__(self, client: BaseClient) -> None:
        self.client = client

    async def create_template(self, payload: dict[str, Any]) -> Response:
        return await self.client.post("/templates/", json=payload)

    async def list_templates(self) -> Response:
        return await self.client.get("/templates/")

    async def create_workout(
        self,
        template_id: int,
        payload: dict[str, Any],
    ) -> Response:
        return await self.client.post(
            f"/templates/{template_id}/workouts",
            json=payload,
        )

    async def delete_template(self, template_id: int) -> Response:
        return await self.client.delete(f"/templates/{template_id}")


class ProgressClient:
    def __init__(self, client: BaseClient) -> None:
        self.client = client

    async def summary(self) -> Response:
        return await self.client.get("/progress/summary")

    async def weekly_volume(self) -> Response:
        return await self.client.get("/progress/weekly-volume")

    async def exercise_record(self, exercise_id: int) -> Response:
        return await self.client.get(f"/progress/exercises/{exercise_id}")

    async def exercise_history(self, exercise_id: int) -> Response:
        return await self.client.get(
            f"/progress/exercises/{exercise_id}/history"
        )


@dataclass(slots=True)
class ApiClients:
    base: BaseClient
    auth: AuthClient
    users: UsersClient
    workouts: WorkoutsClient
    exercises: ExercisesClient
    workout_exercises: WorkoutExercisesClient
    notifications: NotificationsClient
    goals: GoalsClient
    templates: TemplatesClient
    progress: ProgressClient

    @classmethod
    def build(cls, base: BaseClient) -> "ApiClients":
        return cls(
            base=base,
            auth=AuthClient(base),
            users=UsersClient(base),
            workouts=WorkoutsClient(base),
            exercises=ExercisesClient(base),
            workout_exercises=WorkoutExercisesClient(base),
            notifications=NotificationsClient(base),
            goals=GoalsClient(base),
            templates=TemplatesClient(base),
            progress=ProgressClient(base),
        )
