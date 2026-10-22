-- =============================================================================
-- 02-seed-admin.sql  -  creates the initial administrator account.
--
--   email    : admin@example.com
--   password : password123
--
-- Only the bcrypt hash (cost 12, "$2y$" variant - accepted by Python's `bcrypt`)
-- is stored; the plain-text password never touches the database.
--
-- !! Change this password immediately outside of local development. !!
--
-- Regenerate the hash for another password with any bcrypt implementation, e.g.
--   python -c "import bcrypt; print(bcrypt.hashpw(b'NEW_PASSWORD', bcrypt.gensalt(12)).decode())"
-- or, inside psql with pgcrypto:
--   CREATE EXTENSION IF NOT EXISTS pgcrypto;
--   SELECT crypt('NEW_PASSWORD', gen_salt('bf', 12));
--
-- Idempotent: re-running never overwrites an existing account.
-- =============================================================================

\set ON_ERROR_STOP on

INSERT INTO users (email, password_hash, full_name, role, is_active)
VALUES (
    'admin@example.com',
    '$2y$12$lz2pomi4cBo6.DYDlTGFdeLUN3PO4WsNnFd745QnkMowmOjul9RBa',
    'Administrator',
    'admin',
    true
)
ON CONFLICT (email) DO NOTHING;
