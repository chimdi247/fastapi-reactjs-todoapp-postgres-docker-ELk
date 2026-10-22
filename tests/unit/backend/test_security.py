import re
from pathlib import Path

import pytest

from app.core import security

SEED_SQL = Path(__file__).resolve().parents[3] / "docker" / "postgres" / "init" / "02-seed-admin.sql"


@pytest.mark.unit
def test_hash_and_verify_roundtrip():
    hashed = security.hash_password("s3cret-Passw0rd")
    assert hashed.startswith("$2") and hashed != "s3cret-Passw0rd"
    assert security.verify_password("s3cret-Passw0rd", hashed) is True
    assert security.verify_password("wrong", hashed) is False


@pytest.mark.unit
def test_hashes_are_salted():
    assert security.hash_password("same") != security.hash_password("same")


@pytest.mark.unit
def test_unknown_user_never_authenticates_even_with_dummy_password():
    # the timing-equalising dummy hash is the hash of "password123": it must NOT log anyone in
    assert security.verify_password("password123", None) is False


@pytest.mark.unit
@pytest.mark.parametrize("bad_hash", ["", "not-a-hash", "$2y$12$short"])
def test_malformed_hash_returns_false_not_exception(bad_hash):
    assert security.verify_password("x", bad_hash) is False


@pytest.mark.unit
def test_overlong_password_does_not_raise():
    assert security.verify_password("a" * 200, security.hash_password("a")) in (True, False)


@pytest.mark.unit
def test_seed_sql_hash_matches_documented_admin_password():
    """The hash committed in docker/postgres/init/02-seed-admin.sql must be password123."""
    sql = SEED_SQL.read_text()
    m = re.search(r"'(\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53})'", sql)
    assert m, "bcrypt hash not found in seed SQL"
    assert security.verify_password("password123", m.group(1))
    assert not security.verify_password("password124", m.group(1))
    assert "admin@example.com" in sql
