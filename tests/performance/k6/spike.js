// SPIKE TEST: sudden surge (flash crowd), then back to baseline. Checks autoscaling-like
// behaviour, connection pool exhaustion and how fast the service recovers.
import { sleep } from 'k6';
import { thresholds, userJourney } from './lib/common.js';

export const options = {
  stages: [
    { duration: '1m',  target: 10 },    // baseline
    { duration: '10s', target: 300 },   // spike!
    { duration: '2m',  target: 300 },   // sustained peak
    { duration: '10s', target: 10 },    // drop
    { duration: '3m',  target: 10 },    // recovery - watch p95 / 5xx return to normal in Grafana
    { duration: '30s', target: 0 },
  ],
  thresholds: thresholds({ http_req_failed: ['rate<0.05'], http_req_duration: ['p(95)<1500'] }),
};
export default function () { userJourney(); sleep(Math.random() * 0.5 + 0.2); }
