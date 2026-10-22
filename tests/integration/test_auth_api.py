import time

import httpx
import jwt
import pytest

from conftest import ADMIN_EMAIL, ADMIN_PASSWORD, JWT_SECRET

pytestmark = pytest.mark.integration


def test_seeded_admin_can_log_in(anon):
    r = anon.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["token_type"] == "bearer" and data["expires_in"] > 0
    assert data["user"]["email"] == ADMIN_EMAIL and data["user"]["role"] == "admin"
    assert "password" not in str(data).lower().replace("password_hash", "")  # nothing sensitive leaks
    assert "password_hash" not in data["user"]


def test_login_is_case_and_whitespace_insensitive_for_email(anon):
    r = anon.post("/auth/login", json={"email": f"  {ADMIN_EMAIL.upper()} ", "password": ADMIN_PASSWORD})
    assert r.status_code == 200


@pytest.mark.parametrize("email,password", [
    ("admin@example.com", "wrong-password"),
    ("nobody@example.com", "password123"),
])
def test_bad_credentials_return_identical_401(anon, email, password):
    r = anon.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 401
    assert r.json()["message"] == "Invalid email or password"   # no user enumeration
    assert r.headers["www-authenticate"] == "Bearer"


def test_me_returns_current_user(api):
    r = api.get("/auth/me")
    assert r.status_code == 200 and r.json()["data"]["email"] == ADMIN_EMAIL


def test_last_login_is_recorded(anon, api):
    anon.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert api.get("/auth/me").json()["data"]["last_login_at"] is not None


def test_token_with_wrong_signature_rejected(anon):
    forged = jwt.encode({"sub": "1", "exp": int(time.time()) + 600}, "x" * 40, algorithm="HS256")
    assert anon.get("/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_expired_token_rejected(anon):
    expired = jwt.encode({"sub": "1", "exp": int(time.time()) - 10}, JWT_SECRET, algorithm="HS256")
    r = anon.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401


def test_token_for_nonexistent_user_rejected(anon):
    t = jwt.encode({"sub": "99999999", "exp": int(time.time()) + 600}, JWT_SECRET, algorithm="HS256")
    r = anon.get("/auth/me", headers={"Authorization": f"Bearer {t}"})
    # only meaningful when the test's JWT_SECRET matches the stack's; otherwise still 401
    assert r.status_code == 401
