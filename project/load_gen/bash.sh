#!/bin/bash

SCRIPT=$1  # get.js / set.js / mixed.js
URL="http://localhost:8080"

if [ -z "$SCRIPT" ]; then
  echo "Usage: ./run_benchmark_k6.sh get.js"
  exit 1
fi

echo "vus,throughput,avg,p50,p90,p95,p99" > results.csv

for VUS in 1 10 20 50 100 200 400 600 800 1000 
do
    echo "Running test with $VUS VUs..."

    OUT=$(k6 run --summary-export=summary.json --env VUS=$VUS $SCRIPT 2>&1)

    # Extract metrics from summary.json
    TPS=$(jq '.metrics.http_reqs.rate' summary.json)
    AVG=$(jq '.metrics.http_req_duration.avg' summary.json)
    P50=$(jq '.metrics.http_req_duration["p(50)"]' summary.json)
    P90=$(jq '.metrics.http_req_duration["p(90)"]' summary.json)
    P95=$(jq '.metrics.http_req_duration["p(95)"]' summary.json)
    P99=$(jq '.metrics.http_req_duration["p(99)"]' summary.json)

    echo "$VUS,$TPS,$AVG,$P50,$P90,$P95,$P99" >> results.csv
done