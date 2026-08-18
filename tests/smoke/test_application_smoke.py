from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import STATIC_DIR, app


pytestmark = [pytest.mark.smoke]


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_health_check_reports_ready(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-request-id"]


def test_frontend_and_static_assets_are_served(client: TestClient) -> None:
    frontend = client.get("/")
    script = client.get("/static/app.js")
    stylesheet = client.get("/static/styles.css")

    assert frontend.status_code == 200
    assert "text/html" in frontend.headers["content-type"]
    assert script.status_code == 200
    assert "javascript" in script.headers["content-type"]
    assert stylesheet.status_code == 200
    assert "text/css" in stylesheet.headers["content-type"]
    assert (Path(STATIC_DIR) / "index.html").is_file()


def test_openapi_is_available_and_has_oauth2(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    document = response.json()
    assert document["info"] == {
        "title": "Gym Planner API",
        "version": "1.0.0",
    }
    assert "OAuth2PasswordBearer" in document["components"]["securitySchemes"]


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/auth/me"),
        ("GET", "/workouts/"),
        ("GET", "/exercises/"),
        ("GET", "/notifications"),
        ("GET", "/goals/"),
        ("GET", "/templates/"),
        ("GET", "/progress/summary"),
        ("GET", "/admin/users/"),
    ],
)
def test_critical_routes_reject_anonymous_requests(
    client: TestClient,
    method: str,
    path: str,
) -> None:
    response = client.request(method, path)

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_unknown_route_has_standard_error_without_traceback(
    client: TestClient,
) -> None:
    response = client.get("/route-that-does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
    assert "traceback" not in response.text.lower()
    assert response.headers["x-request-id"]
