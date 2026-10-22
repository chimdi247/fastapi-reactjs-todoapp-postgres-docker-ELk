// STRESS TEST: push beyond normal load to see how the system degrades and recovers.
// Thresholds are deliberately loose: we want to learn *where* it bends, not to fail early.
import { sleep } from 'k6';
import { thresholds, userJourney } from './lib/common.js';

export const options = {
  stages: [
    { duration: '2m', target: 50 },
    { duration: '3m', target: 100 },
    { duration: '3m', target: 200 },
    { duration: '3m', target: 300 },
    { duration: '3m', target: 0 },      // recovery: latency/errors should return to normal
  ],
  thresholds: thresholds({ http_req_failed: ['rate<0.10'], http_req_duration: ['p(95)<2000'] }),
};
export default function () { userJourney(); sleep(Math.random() * 0.5 + 0.2); }
