import http from "k6/http";
import { check } from "k6";

// <-- FIX: Tell k6 that 200, 404, AND 409 are all OK
http.setResponseCallback(http.expectedStatuses(200, 404, 409));

export const options = {
  stages: [
    { duration: "10s", target: 1000},
    { duration: "30s", target: 1000},
  ],
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
};

export default function () {
  const id = Math.floor(Math.random() * 1000) + 1;
  const val = "http_value*" + id; // Use a slightly more realistic value
  var res;

  const prob = Math.random();

  if (prob < 0.6) {
    // --- 1. GET Request ---

    res = http.get(`http://localhost:1234/val?id=${id}`);
    check(res, {
      "GET status is 200 or 404": (r) => r.status === 200 || r.status === 404,
    });
  } else if (prob < 0.9) {
    // --- 2. POST Request ---
    // This correctly sends data in the query string, which your server reads
    res = http.post(`http://localhost:1234/save?id=${id}&val=${val}`);
    check(res, {
      "set ok": (r) => r.status === 200,
    });
  } else {
    let res = http.del(`http://localhost:1234/delete?id=${id}`);
    check(res, {
      "set ok": (r) => r.status === 200 || r.status === 404,
    });
  }
}
