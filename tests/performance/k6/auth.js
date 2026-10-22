// AUTH CAPACITY: bcrypt makes login deliberately CPU-expensive (~250 ms). This finds how many
// logins/s the backend sustains before p95 explodes - important for brute-force resilience.
import http from 'k6/http';
import { check } from 'k6';
import { BASE_URL } from './lib/common.js';

export const options = {
  scenarios: {
    logins: { executor: 'constant-arrival-rate', rate: Number(__ENV.RATE || 5), timeUnit: '1s',
              duration: '2m', preAllocatedVUs: 20, maxVUs: 200 },
  },
  thresholds: { http_req_failed: ['rate<0.01'], 'http_req_duration{name:login}': ['p(95)<1500'] },
};
export default function () {
  const res = http.post(`${BASE_URL}/auth/login`,
    JSON.stringify({ email: __ENV.ADMIN_EMAIL || 'admin@example.com', password: __ENV.ADMIN_PASSWORD || 'password123' }),
    { headers: { 'Content-Type': 'application/json' }, tags: { name: 'login' } });
  check(res, { 'login 200': (r) => r.status === 200 });
}
