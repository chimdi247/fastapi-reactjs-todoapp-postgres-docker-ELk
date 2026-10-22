"""Direct DB checks: schema + seed data created by docker/postgres/init/*.sql."""
import os

import pytest

psycopg = pytest.importorskip("psycopg")

pytestmark = pytest.mark.integration

DSN = os.getenv("POSTGRES_DSN") or "postgresql://{u}:{p}@localhost:{port}/{db}".format(
    u=os.getenv("POSTGRES_USER", "postgres"), p=os.getenv("POSTGRES_PASSWORD", "change_me_postgres"),
    port=os.getenv("POSTGRES_PORT", "5432"), db=os.getenv("POSTGRES_DB", "todos"))


@pytest.fixture(scope="module")
def cur():
    try:
        conn = psycopg.connect(DSN, connect_timeout=5)
    except psycopg.OperationalError as e:
        pytest.skip(f"cannot reach postgres on host ({e}); set POSTGRES_DSN")
    with conn, conn.cursor() as c:
        yield c


def test_all_tables_exist(cur):
    cur.execute("select table_name from information_schema.tables where table_schema='public'")
    assert {"users", "todos", "alembic_version"} <= {r[0] for r in cur.fetchall()}


def test_alembic_is_stamped_at_head(cur):
    cur.execute("select version_num from alembic_version")
    assert cur.fetchall() == [("8b1d2f6c4a90",)]


def test_admin_seeded_with_bcrypt_hash_not_plaintext(cur):
    cur.execute("select password_hash, role, is_active from users where email='admin@example.com'")
    h, role, active = cur.fetchone()
    assert h.startswith("$2") and len(h) == 60 and "password123" not in h
    assert role == "admin" and active is True


def test_email_uniqueness_and_lowercase_constraints(cur):
    with pytest.raises(psycopg.errors.CheckViolation):
        cur.execute("insert into users(email,password_hash) values ('Mixed@Case.com','x')")
