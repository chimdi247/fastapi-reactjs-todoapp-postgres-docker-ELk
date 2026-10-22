# Todo app: FastAPI + React + PostgreSQL, fully containerised with observability

```bash
docker compose up -d --build        # or: make up
```
First start pulls many images and takes a few minutes (Elasticsearch/Kibana are the slow ones).

| URL | What | Login |
|---|---|---|
| http://localhost:8080 | React app (nginx; proxies `/api`, `/otlp`) | **admin@example.com / password123** |
| http://localhost:8085/docs | FastAPI docs | |
| http://localhost:3000 | Grafana (dashboard *Todo App - SLOs...*, alerts) | admin / `GRAFANA_ADMIN_PASSWORD` |
| http://localhost:5601 | Kibana (logs `Todo App - Logs`, traces) | elastic / `ELASTIC_PASSWORD` |
| http://localhost:8025 | Mailpit (alert e-mails) | |
| http://localhost:9001 | MinIO console (S3 buckets) | `MINIO_ROOT_*` |

Defaults live in compose; copy `.env.example` to `.env` to override. **All default secrets are dev-only.**

## Layout
```
docker-compose.yml
docker/postgres/init/   01-schema.sql (all tables)  02-seed-admin.sql (admin user, bcrypt hash)
docker/nginx/           frontend server config
fastapi-todo-backend/   API (+ Dockerfile, auth, OpenTelemetry)
fastapi-todo-react-frontend/ SPA (+ Dockerfile, login, OTel web tracing)
observability/          collector, Mimir, ELK, Grafana (see its README)
tests/                  unit, integration, smoke, e2e (Playwright), Selenium, k6 perf (see its README)
```

## Notes
* SQL in `docker/postgres/init` runs only on an **empty** data volume: `make reset` re-initialises. The schema
  also stamps Alembic at head (`8b1d2f6c4a90`), so `alembic upgrade head` keeps working.
* The original app had no authentication. Added: `users` table, `POST /auth/login` (bcrypt + JWT), `GET /auth/me`,
  React login page + protected routes; all `/todos` endpoints now require a bearer token.
* Dependencies were added to `requirements.txt` / `pyproject.toml` / `package.json`: refresh locks
  (`uv lock`, `npm install`) and then switch the frontend Dockerfile to `npm ci`.
* Change the admin password: generate a new bcrypt hash (see comments in `02-seed-admin.sql`) before first start,
  or `UPDATE users SET password_hash=... WHERE email='admin@example.com'`.
