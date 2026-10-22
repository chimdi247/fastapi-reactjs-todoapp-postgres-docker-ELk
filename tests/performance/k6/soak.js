// SOAK (endurance) TEST: moderate load for a long time to expose leaks (memory, connections,
// file descriptors), log/disk growth and slow degradation. Watch container memory in Grafana.
//   SOAK_DURATION=4h VUS=25 k6 run tests/performance/k6/soak.js
import { sleep } from 'k6';
import { thresholds, userJourney } from './lib/common.js';

export const options = {
  stages: [
    { duration: '5m', target: Number(__ENV.VUS || 25) },
    { duration: __ENV.SOAK_DURATION || '30m', target: Number(__ENV.VUS || 25) },
    { duration: '2m', target: 0 },
  ],
  thresholds: thresholds({ http_req_duration: ['p(95)<300', 'p(99)<1000'] }),
};
export default function () { userJourney(); sleep(Math.random() * 1.5 + 0.5); }
