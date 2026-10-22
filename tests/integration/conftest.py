"""Fixtures for tests that talk to the running docker compose stack.

Override targets with env vars (defaults match docker-compose.yml):
  BASE_URL FRONTEND_URL ADMIN_EMAIL ADMIN_PASSWORD JWT_SECRET
  MIMIR_URL ES_URL ELASTIC_PASSWORD GRAFANA_URL GRAFANA_ADMIN_USER GRAFANA_ADMIN_PASSWORD
  KIBANA_URL MAILPIT_URL POSTGRES_DSN
"""
import os
import time
import uuid

import httpx
import pytest

BASE_URL = os.getenv("BASE_URL", "http://localhost:8085").rstrip("/")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080").rstrip("/")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password123")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-dev-only-jwt-secret-0123456789abcdef")


def _wait_for_api(timeout=90):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if httpx.get(f"{BASE_URL}/health", timeout=3).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(2)
    pytest.exit(f"API not reachable at {BASE_URL} - is `docker compose up -d` running?", returncode=2)


@pytest.fixture(scope="session", autouse=True)
def _stack_is_up():
    _wait_for_api()


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def frontend_url():
    return FRONTEND_URL


@pytest.fixture(scope="session")
def anon():
    with httpx.Client(base_url=BASE_URL, timeout=15) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token(anon):
    r = anon.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"seed admin cannot log in: {r.status_code} {r.text}"
    return r.json()["data"]["access_token"]


@pytest.fixture(scope="session")
def api(admin_token):
    with httpx.Client(base_url=BASE_URL, timeout=15, headers={"Authorization": f"Bearer {admin_token}"}) as c:
        yield c


@pytest.fixture
def todo(api):
    """Creates todos on demand and always deletes them afterwards."""
    created = []

    def make(title=None, description="created by tests", **kw):
        title = title or f"it-{uuid.uuid4().hex[:8]}"
        r = api.post("/todos", json={"title": title, "description": description, **kw})
        assert r.status_code == 201, r.text
        data = r.json()["data"]
        created.append(data["id"])
        return data

    yield make
    for tid in created:
        api.delete(f"/todos/delete/{tid}")
