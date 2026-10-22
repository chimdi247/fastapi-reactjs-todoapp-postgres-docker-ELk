import httpx
import pytest

from conftest import FRONTEND_URL

pytestmark = [pytest.mark.integration, pytest.mark.security]

PROTECTED = [("GET", "/todos"), ("POST", "/todos"), ("GET", "/todos/1"),
             ("PUT", "/todos/update/1"), ("DELETE", "/todos/delete/1"), ("GET", "/auth/me")]


@pytest.mark.parametrize("method,path", PROTECTED)
def test_endpoints_reject_anonymous(anon, method, path):
    r = anon.request(method, path, json={"title": "x"} if method in {"POST", "PUT"} else None)
    assert r.status_code == 401


@pytest.mark.parametrize("payload", [
    "' OR '1'='1", "admin@example.com'--", "\"; DROP TABLE users;--", "admin@example.com' OR 1=1 --@x.com",
])
def test_sql_injection_in_login_is_not_a_bypass_or_a_500(anon, payload):
    r = anon.post("/auth/login", json={"email": payload, "password": payload})
    assert r.status_code in (401, 422)


def test_sql_injection_in_todo_fields_is_stored_literally(api, todo):
    evil = "x'); DROP TABLE todos;--"
    t = todo(title=evil)
    assert api.get(f"/todos/{t['id']}").json()["data"]["title"] == evil
    assert api.get("/todos").status_code == 200          # table still exists


def test_html_is_returned_verbatim_not_executed_server_side(api, todo):
    t = todo(title="<script>alert(1)</script>")
    r = api.get(f"/todos/{t['id']}")
    assert r.headers["content-type"].startswith("application/json")
    assert r.json()["data"]["title"] == "<script>alert(1)</script>"   # React escapes on render


def test_oversized_title_rejected_or_truncated_not_500(api):
    r = api.post("/todos", json={"title": "x" * 5000})
    assert r.status_code != 500


def test_auth_header_scheme_must_be_bearer(anon, admin_token):
    assert anon.get("/auth/me", headers={"Authorization": f"Basic {admin_token}"}).status_code == 401
    assert anon.get("/auth/me", headers={"Authorization": admin_token}).status_code == 401


def test_frontend_sends_security_headers():
    r = httpx.get(FRONTEND_URL + "/", timeout=10)
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "server" not in r.headers or "/" not in r.headers["server"]   # nginx version hidden


def test_frontend_proxies_api_and_spa_fallback():
    assert httpx.get(FRONTEND_URL + "/api/health", timeout=10).json() == {"status": "ok"}
    spa = httpx.get(FRONTEND_URL + "/todos/123/edit", timeout=10)          # deep link
    assert spa.status_code == 200 and "<div id=\"root\">" in spa.text


def test_otlp_proxy_only_accepts_post():
    assert httpx.get(FRONTEND_URL + "/otlp/v1/traces", timeout=10).status_code in (403, 405)
