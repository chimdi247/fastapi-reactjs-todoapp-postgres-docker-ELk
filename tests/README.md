# Tests

All suites except `unit` run against the live stack: `docker compose up -d --build` first.
Targets are configurable by env vars (`BASE_URL`, `FRONTEND_URL`, `ADMIN_EMAIL`, ...), defaults match compose.

| Suite | Folder | Tool | Run |
|---|---|---|---|
| Unit (backend) | `unit/backend` | pytest | `make test-unit` |
| Unit (frontend) | `unit/frontend` | vitest | `make test-unit` |
| Smoke | `smoke/smoke.sh` | bash + curl | `make smoke` |
| Integration + security | `integration` | pytest + httpx (+psycopg) | `make test-integration` |
| Observability pipeline | `integration/test_observability_pipeline.py` | pytest | `make test-observability` |
| End-to-end + front-end perf budget | `e2e` | Playwright | `make test-e2e` |
| Browser (Selenium) | `selenium` | pytest + selenium | `make test-selenium` |
| Performance smoke / load / stress / spike / soak / breakpoint / login capacity | `performance/k6` | k6 | `make k6-smoke load stress spike soak breakpoint` |

Python deps: `python -m venv .venv && . .venv/bin/activate && pip install -r tests/requirements.txt`

Notes
* Unit tests import the real backend code and cross-check that the bcrypt hash in
  `docker/postgres/init/02-seed-admin.sql` really is `password123`.
* k6 runs inside docker (`--profile perf`) and remote-writes its metrics to Mimir, so load tests are
  visible next to the app dashboard in Grafana. Locally: `k6 run tests/performance/k6/load.js`.
  Tunables: `VUS`, `DURATION`, `SOAK_DURATION`, `MAX_RPS`, `RATE`.
* Observability tests poll for up to ~2.5 min per check (batching + scrape intervals).
* Run perf tests against a disposable environment: they create (and delete) todos.
