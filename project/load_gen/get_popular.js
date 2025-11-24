import http from 'k6/http';
import { sleep } from 'k6';

const BASE = __ENV.BASE_URL || 'http://localhost:1234';
const DURATION = __ENV.DURATION || '40s';

// k6 options: VUs and duration are supplied via env vars
export let options = {
  vus: __ENV.VUS ? parseInt(__ENV.VUS) : 1,
  duration: DURATION,
};

// Always pick keys only from 1..3000 (hot popular range)
const HOT_KEY_MAX = 3000;

export default function () {
  const key = Math.floor(Math.random() * HOT_KEY_MAX) + 1;

  http.get(`${BASE}/val`, {
    params: { id: key }
  });

  // No sleep → closed-loop load
}
