// BREAKPOINT / CAPACITY TEST: ramp the *arrival rate* (req/s) until an SLO breaks; the test
// aborts itself at that point and the last rate reached is your capacity. Open model => the
// load keeps coming even when the server slows down (unlike VU-based tests).
import http from 'k6/http';
import { check } from 'k6';
import { BASE_URL, authHeaders } from './lib/common.js';

export const options = {
  scenarios: {
    capacity: {
      executor: 'ramping-arrival-rate',
      startRate: 10, timeUnit: '1s',
      preAllocatedVUs: 100, maxVUs: 2000,
      stages: [{ duration: '10m', target: Number(__ENV.MAX_RPS || 500) }],
    },
  },
  thresholds: {
    http_req_failed: [{ threshold: 'rate<0.02', abortOnFail: true, delayAbortEval: '30s' }],
    http_req_duration: [{ threshold: 'p(95)<1000', abortOnFail: true, delayAbortEval: '30s' }],
  },
};
export default function () {
  const res = http.get(`${BASE_URL}/todos`, { ...authHeaders(), tags: { name: 'GET /todos' } });
  check(res, { 'list 200': (r) => r.status === 200 });
}
