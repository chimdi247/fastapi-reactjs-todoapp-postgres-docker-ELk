// PERFORMANCE SMOKE: 1 VU for 30 s - proves the scripts and the system work before a big run.
import { sleep } from 'k6';
import { thresholds, userJourney } from './lib/common.js';

export const options = { vus: 1, duration: '30s', thresholds: thresholds() };
export default function () { userJourney(); sleep(1); }
