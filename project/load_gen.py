#!/usr/bin/env python3
# python3 load_gen.py --host localhost --thread-steps 10,50,100,200,500,1000 --duration 30 --csv benchmark.csv
# taskset -c 3-11 python3 load_gen.py --host localhost --port 1234 --workload get_all --key-space 10000 --thread-steps 10,50,100,200,250,350 --csv getpop_o.csv
"""
Automated Benchmark Runner.
Runs the load test multiple times with different thread counts and logs all results to CSV.

Usage:
  python3 benchmark.py --host localhost --port 1234 --thread-steps 10,50,100,200,500 --duration 20 --csv benchmark_results.csv
"""

import argparse
import threading
import time
import random
import requests
import sys
import statistics
import csv
import os
from urllib.parse import urljoin

# ---- Config / CLI ----
parser = argparse.ArgumentParser(description="Automated Load Test Benchmark")
parser.add_argument("--host", required=True, help="Server host (IP or hostname)")
parser.add_argument("--port", type=int, default=1234, help="Server port")
parser.add_argument("--thread-steps", type=str, default="10,50,100", help="Comma-separated list of thread counts to test (e.g. '10,50,100')")
parser.add_argument("--duration", type=int, default=20, help="Duration of EACH test run in seconds")
parser.add_argument("--workload", choices=["put_all", "get_all", "get_popular", "mixed"], default="mixed")
parser.add_argument("--csv", type=str, default="benchmark.csv", help="CSV file to save results")
parser.add_argument("--key-space", type=int, default=10000, help="Number of distinct keys")
parser.add_argument("--popular-size", type=int, default=10, help="Number of keys in 'popular' set")
parser.add_argument("--timeout", type=float, default=5.0, help="Request timeout")

args = parser.parse_args()

BASE = f"http://{args.host}:{args.port}/"
GET_PATH = "val"
POST_PATH = "save"
DEL_PATH = "delete"

# ---- Global State (Reset for each run) ----
stop_event = threading.Event()
stats_lock = threading.Lock()
total_success = 0
total_fail = 0
response_times = []

# ---- Core Functions ----
def now_s():
    return time.monotonic()

def record_result(success: bool, resp_time: float):
    global total_success, total_fail, response_times
    with stats_lock:
        if success:
            total_success += 1
            response_times.append(resp_time)
        else:
            total_fail += 1

def client_thread_fn(tid: int, id_start: int):
    session = requests.Session()
    local_counter = 0
    rng = random.Random(tid + int(time.time()))
    popular_keys = [id_start + i for i in range(args.popular_size)]

    while not stop_event.is_set():
        local_counter += 1
        
        # Workload Selection
        if args.workload == "put_all": op = "write"
        elif args.workload == "get_all": op = "read"
        elif args.workload == "get_popular": op = "read_popular"
        else: # mixed
            r = rng.random()
            if r < 0.7: op = "read"
            elif r < 0.9: op = "write"
            else: op = "delete"

        # Key Selection
        if op == "read_popular":
            key = rng.choice(popular_keys)
        else:
            key = id_start + ((tid * 1000000 + local_counter) % args.key_space)

        success = False
        resp_time = 0.0
        t0 = now_s()
        
        try:
            if op in ("read", "read_popular"):
                url = urljoin(BASE, GET_PATH)
                r = session.get(url, params={"id": str(key)}, timeout=args.timeout)
                resp_time = now_s() - t0
                success = (r.status_code in (200, 404))
            
            elif op == "write":
                url = urljoin(BASE, POST_PATH)
                payload = {"id": str(key), "val": f"val_{tid}_{local_counter}"}
                r = session.post(url, data=payload, timeout=args.timeout)
                resp_time = now_s() - t0
                success = (r.status_code in (200, 409))
            
            elif op == "delete":
                url = urljoin(BASE, DEL_PATH)
                r = session.delete(url, params={"id": str(key)}, timeout=args.timeout)
                resp_time = now_s() - t0
                success = (r.status_code in (200, 404))
        except requests.exceptions.RequestException:
            success = False
            resp_time = now_s() - t0
        
        record_result(success, resp_time)

def run_single_test(num_threads):
    global total_success, total_fail, response_times, stop_event
    
    # 1. Reset State
    stop_event.clear()
    with stats_lock:
        total_success = 0
        total_fail = 0
        response_times = []

    print(f"--> Running: {num_threads} threads for {args.duration}s...")

    # 2. Start Threads
    threads = []
    start_time = now_s()
    for i in range(num_threads):
        t = threading.Thread(target=client_thread_fn, args=(i+1, 1), daemon=True)
        threads.append(t)
        t.start()

    # 3. Wait
    time.sleep(args.duration)
    stop_event.set()

    # 4. Join
    for t in threads:
        t.join(timeout=2.0)
    
    elapsed = now_s() - start_time

    # 5. Calculate Metrics
    with stats_lock:
        succ = total_success
        fail = total_fail
        rts = list(response_times)

    total_req = succ + fail
    throughput = succ / elapsed if elapsed > 0 else 0.0
    avg_lat = statistics.mean(rts) if rts else 0.0
    p50 = statistics.median(rts) if rts else 0.0
    p95 = statistics.quantiles(rts, n=20)[-1] if rts and len(rts) >= 20 else 0.0

    print(f"    Done. Throughput: {throughput:.2f} req/s | P95: {p95:.4f}s")

    return {
        "timestamp": time.strftime("%H:%M:%S"),
        "threads": num_threads,
        "throughput": throughput,
        "p95": p95,
        "success": succ,
        "fail": fail
    }

def main():
    # Parse thread steps (e.g., "10,50,100")
    steps = [int(x) for x in args.thread_steps.split(",")]
    
    print(f"=== Starting Benchmark Suite ===")
    print(f"Host: {args.host}:{args.port}")
    print(f"Workload: {args.workload}")
    print(f"Steps (VUs): {steps}\n")

    # Initialize CSV
    file_exists = os.path.isfile(args.csv)
    with open(args.csv, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Workload", "Threads", "Throughput", "P95_Latency", "Success_Count", "Fail_Count"])

    # Run Loop
    for n_threads in steps:
        result = run_single_test(n_threads)
        
        # Save to CSV immediately
        with open(args.csv, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                result["timestamp"], args.workload, result["threads"], 
                f"{result['throughput']:.2f}", f"{result['p95']:.6f}", 
                result["success"], result["fail"]
            ])
        
        # Cooldown to let server recover/drain
        print("    Cooling down (5s)...\n")
        time.sleep(5)

    print(f"=== Benchmark Complete. Results saved to {args.csv} ===")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)