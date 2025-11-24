import http from 'k6/http';

const BASE = __ENV.BASE_URL || 'http://localhost:1234';
const DURATION = __ENV.DURATION || '40s';

// ratios: 0.7 GET, 0.2 PUT, 0.1 DELETE (change via env if desired)
const GET_RATIO = __ENV.GET_RATIO ? parseFloat(__ENV.GET_RATIO) : 0.7;
const PUT_RATIO = __ENV.PUT_RATIO ? parseFloat(__ENV.PUT_RATIO) : 0.2;
// delete ratio implied = 1 - GET_RATIO - PUT_RATIO

export let options = {
  vus: __ENV.VUS ? parseInt(__ENV.VUS) : 1,
  duration: DURATION,
};

export default function () {
  const keyspace = parseInt(__ENV.KEYSPACE || '10000');
  const id = Math.floor(Math.random() * keyspace) + 1;
  const r = Math.random();
  if (r < GET_RATIO) {
    http.get(`${BASE}/val`, { params: { id: id } });
  } else if (r < GET_RATIO + PUT_RATIO) {
    const payload = { id: String(id), val: `val-${__VU}-${Math.random().toString(36).slice(2,8)}` };
    http.post(`${BASE}/save`, payload);
  } else {
    http.request('DELETE', `${BASE}/delete`, null, { params: { id: id } });
  }
}
