#!/usr/bin/env bash
set -euo pipefail

# run_all.sh
# Replace your previous script with this file.
# Requires: k6, jq, vmstat (procps), iostat (sysstat)
# Usage: ./run_all.sh
# Configure BASE_URL, DURATION, KEYSPACE via environment if desired.

BASE_URL=${BASE_URL:-http://localhost:1234}
DURATION=${DURATION:-30s}         # k6 duration (string). We pass to script via env.
KEYSPACE=${KEYSPACE:-20000}

# VU list (as requested)
VUS_LIST=(1 25 50 100 250 500 800 1000 1300 1500 2000)

# workloads -> script filenames (ensure these files exist)
declare -A WORKLOAD_SCRIPTS=(
  #["get_only"]="get_only.js"
  #["put_only"]="put_only.js"
  #["delete_only"]="delete_only.js"
  #["mixed"]="mixed.js"
)

# Tools check
for tool in k6 jq vmstat iostat awk; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Error: required tool '$tool' not found in PATH. Install it and retry." >&2
    exit 1
  fi
done

# Verify k6 script files exist
for s in "${WORKLOAD_SCRIPTS[@]}"; do
  if [[ ! -f "$s" ]]; then
    echo "Missing k6 script: $s. Put it in current directory and retry." >&2
    exit 1
  fi
done

# Cleanup function to kill monitors if script aborted
_cleanup() {
  [[ -n "${CPU_PID:-}" ]] && kill "${CPU_PID}" 2>/dev/null || true
  [[ -n "${DISK_PID:-}" ]] && kill "${DISK_PID}" 2>/dev/null || true
}
trap _cleanup EXIT

TOTAL_WORKLOADS=${#WORKLOAD_SCRIPTS[@]}
WCOUNT=0

echo "Base URL: $BASE_URL"
echo "Duration: $DURATION"
echo "Keyspace: $KEYSPACE"
echo "VU steps: ${VUS_LIST[*]}"
echo

for workload in "${!WORKLOAD_SCRIPTS[@]}"; do
  WCOUNT=$((WCOUNT + 1))
  script=${WORKLOAD_SCRIPTS[$workload]}
  outcsv="results_${workload}.csv"

  echo "=================================================================="
  echo "[$WCOUNT/$TOTAL_WORKLOADS] Running workload: $workload (script: $script)"
  echo "Output CSV: $outcsv"
  echo "=================================================================="

  # create CSV header
  printf '%s\n' "vus,tps,avg_ms,p50_ms,p90_ms,p95_ms,p99_ms,cpu_util_pct,disk_util_pct" > "$outcsv"

  VCOUNT=0
  VTOTAL=${#VUS_LIST[@]}

  for VUS in "${VUS_LIST[@]}"; do
    VCOUNT=$((VCOUNT + 1))
    echo "  -> [$VCOUNT/$VTOTAL] VUs = $VUS"

    # start vmstat and iostat; redirect to files
    vmstat 1 > cpu.log 2>&1 &
    CPU_PID=$!

    iostat -dx 1 > disk.log 2>&1 &
    DISK_PID=$!

    # run k6 (we pass environment variables used by your k6 scripts)
    # capture k6 output to k6_run.log; summary exported to summary.json by --summary-export
    echo "    Running: k6 run --summary-export=summary.json --env VUS=$VUS --env BASE_URL=$BASE_URL --env KEYSPACE=$KEYSPACE --env DURATION=$DURATION $script"
    # run k6 but don't abort the entire script if k6 returns non-zero (we still want the monitors processed)
    k6 run --summary-export=summary.json --env VUS="$VUS" --env BASE_URL="$BASE_URL" --env KEYSPACE="$KEYSPACE" --env DURATION="$DURATION" "$script" > k6_run.log 2>&1 || true

    # stop monitors
    if [[ -n "${CPU_PID:-}" ]]; then
      kill "$CPU_PID" 2>/dev/null || true
      wait "$CPU_PID" 2>/dev/null || true
      unset CPU_PID
    fi
    if [[ -n "${DISK_PID:-}" ]]; then
      kill "$DISK_PID" 2>/dev/null || true
      wait "$DISK_PID" 2>/dev/null || true
      unset DISK_PID
    fi

    # compute MAX CPU util: 100 - min(idle) observed from vmstat logs
    # vmstat idle column is field 15 (on typical vmstat output)
    MIN_IDLE=$(awk 'NR>2 { if(min=="" || $15+0 < min+0) min=$15 } END { if(min=="") print 0; else print min }' cpu.log)
    # convert to number and compute 100 - min_idle, with two decimals
    if [[ -z "$MIN_IDLE" ]]; then
      CPU_UTIL_MAX="0.00"
    else
      CPU_UTIL_MAX=$(awk -v minidle="$MIN_IDLE" 'BEGIN { printf("%.2f", 100 - (minidle+0)) }')
    fi

    # compute MAX disk %util seen in iostat output (last column is %util)
    DISK_UTIL_MAX=$(awk '/^Device/ {next} /^[a-z]/ { if($NF+0 > max+0) max=$NF } END { if(max=="") print "0.00"; else printf("%.2f", max) }' disk.log)

    # parse summary.json, gracefully fallback if missing or missing fields
    if [[ -f summary.json ]]; then
      # some metrics could be missing; use jq with fallback 0
      TPS=$(jq -r '.metrics.http_reqs.rate // 0' summary.json)
      AVG_MS=$(jq -r '.metrics.http_req_duration.avg // 0' summary.json)
      P50_MS=$(jq -r '.metrics.http_req_duration["p(50)"] // 0' summary.json)
      P90_MS=$(jq -r '.metrics.http_req_duration["p(90)"] // 0' summary.json)
      P95_MS=$(jq -r '.metrics.http_req_duration["p(95)"] // 0' summary.json)
      P99_MS=$(jq -r '.metrics.http_req_duration["p(99)"] // 0' summary.json)
    else
      TPS=0; AVG_MS=0; P50_MS=0; P90_MS=0; P95_MS=0; P99_MS=0
    fi

    # append CSV line
    echo "${VUS},${TPS},${AVG_MS},${P50_MS},${P90_MS},${P95_MS},${P99_MS},${CPU_UTIL_MAX},${DISK_UTIL_MAX}" >> "$outcsv"

    # short cooldown (let system settle)
    sleep 2
  done

  echo "Saved results to $outcsv"
  echo
done

echo "All workloads complete."
