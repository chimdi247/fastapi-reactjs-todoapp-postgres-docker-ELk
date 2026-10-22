import pytest

pytestmark = pytest.mark.integration


def test_full_crud_lifecycle(api, todo):
    created = todo(title="write integration tests", description="cover CRUD")
    tid = created["id"]
    assert created["is_completed"] is False and created["created_at"]

    got = api.get(f"/todos/{tid}")
    assert got.status_code == 200 and got.json()["data"]["title"] == "write integration tests"

    upd = api.put(f"/todos/update/{tid}", json={"title": "renamed", "is_completed": True})
    assert upd.status_code == 200
    data = upd.json()["data"]
    assert data["title"] == "renamed" and data["is_completed"] is True
    assert data["description"] == "cover CRUD"              # untouched field preserved
    assert data["updated_at"] >= created["updated_at"]

    listing = api.get("/todos").json()["data"]
    assert tid in [t["id"] for t in listing]

    assert api.delete(f"/todos/delete/{tid}").status_code == 200
    assert api.get(f"/todos/{tid}").status_code == 404


def test_list_is_newest_first(api, todo):
    first, second = todo(), todo()
    ids = [t["id"] for t in api.get("/todos").json()["data"]]
    assert ids.index(second["id"]) < ids.index(first["id"])


def test_missing_todo_is_404_with_envelope(api):
    r = api.get("/todos/987654321")
    assert r.status_code == 404
    assert r.json()["message"] == "Todo not found"


@pytest.mark.parametrize("payload", [{}, {"description": "no title"}, {"title": None}])
def test_create_validation_errors_are_422(api, payload):
    assert api.post("/todos", json=payload).status_code == 422


def test_non_integer_id_is_422(api):
    assert api.get("/todos/abc").status_code == 422


def test_update_accepts_camel_case_alias(api, todo):
    t = todo()
    r = api.put(f"/todos/update/{t['id']}", json={"isCompleted": True})
    assert r.status_code == 200 and r.json()["data"]["is_completed"] is True


def test_unicode_and_long_text_round_trip(api, todo):
    t = todo(title="✅ café – 日本語", description="x" * 1000)
    assert api.get(f"/todos/{t['id']}").json()["data"]["title"] == "✅ café – 日本語"
