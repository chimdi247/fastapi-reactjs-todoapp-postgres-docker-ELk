// LOAD TEST: expected production traffic. Ramp up, hold steady, ramp down.
//   k6 run tests/performance/k6/load.js            (VUS=20 DURATION=5m by default)
import { sleep } from 'k6';
import { thresholds, userJourney } from './lib/common.js';

const VUS = Number(__ENV.VUS || 20);
const HOLD = __ENV.DURATION || '5m';

export const options = {
  stages: [
    { duration: '1m', target: VUS },    // ramp up
    { duration: HOLD, target: VUS },    // steady state
    { duration: '30s', target: 0 },     // ramp down
  ],
  thresholds: thresholds(),
};
export default function () { userJourney(); sleep(Math.random() * 1 + 0.5); }
