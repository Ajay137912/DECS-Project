import http from 'k6/http';

const BASE = __ENV.BASE_URL || 'http://localhost:1234';
const DURATION = __ENV.DURATION || '40s';

export let options = {
  vus: __ENV.VUS ? parseInt(__ENV.VUS) : 1,
  duration: DURATION,
};

export default function () {
  // DELETE /delete?id=<id>
  const id = Math.floor(Math.random() * (parseInt(__ENV.KEYSPACE || '10000'))) + 1;
  const res = http.request('DELETE', `${BASE}/delete`, null, { params: { id: id } });
}
