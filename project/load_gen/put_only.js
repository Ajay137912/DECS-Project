import http from 'k6/http';

const BASE = __ENV.BASE_URL || 'http://localhost:1234';
const DURATION = __ENV.DURATION || '40s';

export let options = {
  vus: __ENV.VUS ? parseInt(__ENV.VUS) : 1,
  duration: DURATION,
};

export default function () {
  // POST /save with form data id and val
  const id = Math.floor(Math.random() * (parseInt(__ENV.KEYSPACE || '10000'))) + 1;
  const payload = { id: String(id), val: `val-${__VU}-${Math.random().toString(36).slice(2,8)}` };
  const res = http.post(`${BASE}/save`, payload);
}
