-- =============================================================================
-- 01-schema.sql  -  creates every table the application needs.
--
-- Executed automatically by the official postgres image the FIRST time the data
-- volume is initialised (mounted at /docker-entrypoint-initdb.d). To re-run:
--     docker compose down -v && docker compose up -d
--
-- Mirrors the Alembic migrations in fastapi-todo-backend/migrations so that
-- `alembic upgrade head` keeps working against a DB created by this script:
--   30c439a3a2b1  initial migration (todos)
--   8b1d2f6c4a90  add users table
-- The script is idempotent (IF NOT EXISTS) so it is safe to run manually too.
-- =============================================================================

\set ON_ERROR_STOP on

BEGIN;

-- ---------------------------------------------------------------------------
-- Shared trigger: keep updated_at fresh even for writes that bypass the ORM.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

-- ---------------------------------------------------------------------------
-- users
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id             SERIAL       NOT NULL,
    email          VARCHAR(255) NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,            -- bcrypt, never plain text
    full_name      VARCHAR(255),
    role           VARCHAR(32)  NOT NULL DEFAULT 'user',
    is_active      BOOLEAN      NOT NULL DEFAULT true,
    last_login_at  TIMESTAMP,
    created_at     TIMESTAMP    NOT NULL DEFAULT now(),
    updated_at     TIMESTAMP    NOT NULL DEFAULT now(),
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT ck_users_email_lowercase CHECK (email = lower(email))
);

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- todos
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS todos (
    id            SERIAL        NOT NULL,
    title         VARCHAR(255)  NOT NULL,
    description   VARCHAR(1000),
    is_completed  BOOLEAN       NOT NULL DEFAULT false,
    created_at    TIMESTAMP     NOT NULL DEFAULT now(),
    updated_at    TIMESTAMP     NOT NULL DEFAULT now(),
    CONSTRAINT todos_pkey PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_todos_created_at   ON todos (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_todos_is_completed ON todos (is_completed);

DROP TRIGGER IF EXISTS trg_todos_updated_at ON todos;
CREATE TRIGGER trg_todos_updated_at
    BEFORE UPDATE ON todos
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- Alembic bookkeeping: stamp the schema as "at head" so the migration tool does
-- not try to re-create the tables above.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Only stamp on a pristine DB: never clobber a revision Alembic already tracks.
INSERT INTO alembic_version (version_num)
SELECT '8b1d2f6c4a90'
WHERE NOT EXISTS (SELECT 1 FROM alembic_version);

COMMIT;
