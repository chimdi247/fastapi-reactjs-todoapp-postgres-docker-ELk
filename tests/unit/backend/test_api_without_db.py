"""HTTP-level behaviour that must hold without a database (no lifespan, no DB)."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)  # not used as a context manager => lifespan/DB not started


@pytest.mark.unit
def test_liveness_ok():
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.unit
def test_readiness_503_when_db_unreachable():
    r = client.get("/health/ready")
    assert r.status_code == 503 and r.json()["status"] == "unavailable"


@pytest.mark.unit
@pytest.mark.parametrize("method,path", [
    ("GET", "/todos/"), ("POST", "/todos/"), ("GET", "/todos/1"),
    ("PUT", "/todos/update/1"), ("DELETE", "/todos/delete/1"), ("GET", "/auth/me"),
])
def test_protected_routes_require_token(method, path):
    r = client.request(method, path, json={"title": "x"} if method in {"POST", "PUT"} else None)
    assert r.status_code == 401
    body = r.json()
    assert body["status"] == 401 and body["message"] == body["detail"] == "Not authenticated"
    assert r.headers["www-authenticate"] == "Bearer"


@pytest.mark.unit
def test_garbage_bearer_token_is_401_without_touching_db():
    r = client.get("/todos/", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401 and r.json()["message"] == "Invalid or expired token"


@pytest.mark.unit
def test_login_validates_payload():
    assert client.post("/auth/login", json={"email": "nope", "password": "x"}).status_code == 422
    assert client.post("/auth/login", json={}).status_code == 422


@pytest.mark.unit
def test_openapi_documents_auth_and_todos():
    paths = client.get("/openapi.json").json()["paths"]
    assert "/auth/login" in paths and "/todos/" in paths
