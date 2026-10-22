import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.auth import LoginRequest
from app.schemas.todo import TodoUpdate


@pytest.mark.unit
def test_login_email_is_trimmed_and_lowercased():
    assert LoginRequest(email="  Admin@Example.COM ", password="x").email == "admin@example.com"


@pytest.mark.unit
@pytest.mark.parametrize("email", ["nope", "@x.com", "x@", ""])
def test_login_rejects_bad_email(email):
    with pytest.raises(ValidationError):
        LoginRequest(email=email, password="x")


@pytest.mark.unit
def test_login_rejects_empty_and_huge_password():
    with pytest.raises(ValidationError):
        LoginRequest(email="a@b.c", password="")
    with pytest.raises(ValidationError):
        LoginRequest(email="a@b.c", password="x" * 129)


@pytest.mark.unit
def test_todo_update_accepts_snake_and_camel_case_and_tracks_unset():
    a = TodoUpdate.model_validate({"is_completed": True})
    b = TodoUpdate.model_validate({"isCompleted": True})
    assert a.is_completed is True and b.is_completed is True
    assert a.model_dump(exclude_unset=True) == {"is_completed": True}


@pytest.mark.unit
def test_settings_reject_short_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(DATABASE_URL="postgresql+asyncpg://x", JWT_SECRET="short", _env_file=None)


@pytest.mark.unit
def test_cors_origins_parsing():
    s = Settings(DATABASE_URL="postgresql+asyncpg://x", JWT_SECRET="x" * 32,
                 CORS_ORIGINS="http://a.com, http://b.com ,", _env_file=None)
    assert s.cors_origins_list == ["http://a.com", "http://b.com"]
