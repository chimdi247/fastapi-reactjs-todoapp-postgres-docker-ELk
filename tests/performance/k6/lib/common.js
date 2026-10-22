import http from 'k6/http';
import { check, fail } from 'k6';
import { Counter } from 'k6/metrics';

export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8085';
const EMAIL = __ENV.ADMIN_EMAIL || 'admin@example.com';
const PASSWORD = __ENV.ADMIN_PASSWORD || 'password123';
const JSON_HEADERS = { 'Content-Type': 'application/json' };

export const businessErrors = new Counter('business_errors');

// Only 2xx/3xx count as "expected"; anything else lands in http_req_failed.
http.setResponseCallback(http.expectedStatuses({ min: 200, max: 399 }));

/** Default SLO thresholds, aligned with the Grafana dashboard (p95 < 250 ms, < 1 % errors). */
export function thresholds(overrides = {}) {
  return Object.assign({
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<250', 'p(99)<800'],
    checks: ['rate>0.99'],
  }, overrides);
}

export function login() {
  const res = http.post(`${BASE_URL}/auth/login`,
    JSON.stringify({ email: EMAIL, password: PASSWORD }), { headers: JSON_HEADERS, tags: { name: 'POST /auth/login' } });
  if (!check(res, { 'login 200': (r) => r.status === 200 })) fail(`login failed: ${res.status} ${res.body}`);
  return res.json('data.access_token');
}

// One login per VU, refreshed every 45 min (tokens live 60 min) so soak tests keep working.
let token = null;
let tokenAt = 0;
export function authHeaders() {
  if (!token || Date.now() - tokenAt > 45 * 60 * 1000) { token = login(); tokenAt = Date.now(); }
  return { headers: { ...JSON_HEADERS, Authorization: `Bearer ${token}` } };
}

/** Realistic user journey. `weights` approximate a read-heavy todo app. */
export function userJourney() {
  const p = authHeaders();
  const r = Math.random();

  if (r < 0.60) {
    const res = http.get(`${BASE_URL}/todos`, { ...p, tags: { name: 'GET /todos' } });
    check(res, { 'list 200': (x) => x.status === 200 }) || businessErrors.add(1);
    return;
  }

  const created = http.post(`${BASE_URL}/todos`, JSON.stringify({ title: `k6-${__VU}-${__ITER}`, description: 'load test' }),
    { ...p, tags: { name: 'POST /todos' } });
  if (!check(created, { 'create 201': (x) => x.status === 201 })) { businessErrors.add(1); return; }
  const id = created.json('data.id');

  if (r < 0.80) http.get(`${BASE_URL}/todos/${id}`, { ...p, tags: { name: 'GET /todos/{id}' } });
  if (r < 0.95) {
    const u = http.put(`${BASE_URL}/todos/update/${id}`, JSON.stringify({ is_completed: true }),
      { ...p, tags: { name: 'PUT /todos/update/{id}' } });
    check(u, { 'update 200': (x) => x.status === 200 }) || businessErrors.add(1);
  }
  const d = http.del(`${BASE_URL}/todos/delete/${id}`, null, { ...p, tags: { name: 'DELETE /todos/delete/{id}' } });   // always clean up
  check(d, { 'delete 200': (x) => x.status === 200 }) || businessErrors.add(1);
}

export function sleepJitter(sleep, min = 0.5, max = 1.5) { sleep(min + Math.random() * (max - min)); }
