.PHONY: up down reset logs ps smoke test-unit test-integration test-observability test-e2e test-selenium \
        load stress spike soak breakpoint k6-smoke
COMPOSE ?= docker compose
K6 = $(COMPOSE) --profile perf run --rm --entrypoint k6 k6 run -o experimental-prometheus-rw

up:            ## build and start everything
	$(COMPOSE) up -d --build
down:          ## stop (data kept)
	$(COMPOSE) down
reset:         ## stop and DELETE all data volumes (re-runs the SQL init scripts)
	$(COMPOSE) down -v
logs:
	$(COMPOSE) logs -f --tail=100
ps:
	$(COMPOSE) ps

smoke:
	bash tests/smoke/smoke.sh
test-unit:
	cd tests && pytest -m unit unit/backend
	cd tests/unit/frontend && npm install --no-audit --no-fund && npm test
test-integration:
	cd tests && pytest -m "integration and not observability" integration
test-observability:
	cd tests && pytest -m observability integration
test-e2e:
	cd tests/e2e && npm install --no-audit --no-fund && npx playwright install chromium firefox && npx playwright test
test-selenium:
	cd tests && pytest -m selenium selenium

# performance (k6 runs in docker and remote-writes its metrics to Mimir -> Grafana)
k6-smoke:
	$(K6) /tests/performance/k6/smoke.js
load:
	$(K6) /tests/performance/k6/load.js
stress:
	$(K6) /tests/performance/k6/stress.js
spike:
	$(K6) /tests/performance/k6/spike.js
soak:
	$(K6) /tests/performance/k6/soak.js
breakpoint:
	$(K6) /tests/performance/k6/breakpoint.js
