import http from "k6/http";
import { check } from "k6";

http.setResponseCallback(http.expectedStatuses(200, 404));

export const options = {
  // Define the "stages" of the test
  stages: [
    // Ramp up from 0 to 500 VUs over 1 minute
    { duration: "10s", target: 1000},

    // Hold at 500 VUs for 30 seconds to see if it's stable
    { duration: "30s", target: 1000},
  ],
  // Define failure thresholds
  thresholds: {
    // Fail the test if more than 1% of requests error out
    http_req_failed: ["rate<0.01"],

    // Fail if the 95th percentile response time is over 500ms
    http_req_duration: ["p(95)<500"],
  },
};

// The main test function. Each VU runs this in a loop.
export default function () {
  // Generate a random ID to test the cache-miss path
  //const id = Math.floor(Math.random() * 1000) + 1;

  

  const res = http.get(`http://localhost:1234/val?id=1`)
  // Check if the request was successful
  check(res, {
    "status is 200 or 404": (r) => r.status === 200 || r.status === 404,
  });
}
