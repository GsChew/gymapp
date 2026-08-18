import pytest

from main import app


pytestmark = [pytest.mark.contract]


EXPECTED_API_OPERATIONS = {
    ("post", "/auth/register"),
    ("post", "/auth/login"),
    ("post", "/auth/refresh"),
    ("get", "/auth/me"),
    ("post", "/workouts/"),
    ("get", "/workouts/"),
    ("get", "/workouts/{workout_id}"),
    ("patch", "/workouts/{workout_id}"),
    ("delete", "/workouts/{workout_id}"),
    ("post", "/workouts/{workout_id}/complete"),
    ("get", "/exercises/"),
    ("post", "/exercises/"),
    ("post", "/workout-exercises/"),
    ("get", "/notifications"),
    ("get", "/goals/"),
    ("post", "/templates/"),
    ("get", "/progress/summary"),
    ("get", "/admin/users/"),
}


def test_openapi_contains_every_critical_operation() -> None:
    schema = app.openapi()
    actual = {
        (method, path)
        for path, operations in schema["paths"].items()
        for method in operations
    }

    assert EXPECTED_API_OPERATIONS <= actual


def test_protected_operations_declare_oauth2_security() -> None:
    schema = app.openapi()

    for method, path in (
        ("get", "/auth/me"),
        ("get", "/workouts/"),
        ("post", "/exercises/"),
        ("get", "/notifications"),
        ("patch", "/admin/users/{user_id}/role"),
    ):
        security = schema["paths"][path][method]["security"]
        assert {"OAuth2PasswordBearer": []} in security


def test_token_and_user_contracts_do_not_expose_password_hash() -> None:
    schemas = app.openapi()["components"]["schemas"]

    assert set(schemas["STokenResponse"]["required"]) == {
        "access_token",
        "refresh_token",
    }
    assert "hashed_password" not in schemas["SUser"]["properties"]
    assert "password" not in schemas["SUser"]["properties"]


def test_real_enum_values_are_documented() -> None:
    schemas = app.openapi()["components"]["schemas"]

    assert schemas["StatusTypes"]["enum"] == [
        "запланировано",
        "сделано",
        "пропущено",
    ]
    assert set(schemas["UserRole"]["enum"]) == {"user", "trainer", "admin"}
