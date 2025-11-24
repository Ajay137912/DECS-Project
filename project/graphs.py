import requests
import time
import random
import threading
import numpy as np
import csv
import sys
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor, wait

# ================= CONFIGURATION =================
# The Target Server
BASE_URL = "http://localhost:1234"
# BASE_URL = "http://10.64.147.158:8080" # Use this if running against remote

# Test Settings
VUS_LIST = [100,200,500,1000, 1500,2000,3000]
DURATION_PER_TEST = 5  # Seconds per test
OUTPUT_CSV = "results.csv"
OUTPUT_IMAGE = "benchmark_graph.png"

# Request Mix
GET_PROBABILITY = 0.7 
# =================================================

# Global thread-safe counter for unique IDs
global_counter = 0
counter_lock = threading.Lock()

def get_next_id():
    global global_counter
    with counter_lock:
        global_counter += 1
        return global_counter

def run_worker(duration, results_list):
    """
    Simulates a single Virtual User (VU).
    Loops until duration expires.
    """
    session = requests.Session() # Use session for Keep-Alive
    start_time = time.time()
    end_time = start_time + duration
    
    latencies = []

    while time.time() < end_time:
        req_start = time.time()
        try:
            if random.random() < GET_PROBABILITY:
                # --- GET Request ---
                resp = session.get(f"{BASE_URL}/val?id=100")
                _ = resp.content 
            else:
                # --- SET Request ---
                current_id = get_next_id()
                resp = session.post(f"{BASE_URL}/save?id={current_id}&val=hello_1234")
                _ = resp.content

            # Record latency in milliseconds
            req_end = time.time()
            latencies.append((req_end - req_start) * 1000)

        except requests.RequestException:
            pass
    
    results_list.extend(latencies)

def calculate_metrics(vus, latencies, duration):
    if not latencies:
        return [vus, 0, 0, 0, 0, 0, 0]

    count = len(latencies)
    tps = count / duration
    avg = np.mean(latencies)
    p50 = np.percentile(latencies, 50)
    p90 = np.percentile(latencies, 90)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)

    return [vus, tps, avg, p50, p90, p95, p99]

def generate_graph():
    print("📊 Generating graph...")
    
    vus = []
    tps = []
    p50 = []
    p95 = []
    p99 = []

    # Read Data
    try:
        with open(OUTPUT_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vus.append(int(row['vus']))
                tps.append(float(row['throughput']))
                p50.append(float(row['p50']))
                p95.append(float(row['p95']))
                p99.append(float(row['p99']))
    except FileNotFoundError:
        print("Error: CSV file not found. Run benchmark first.")
        return

    # Create Plot
    fig, ax1 = plt.subplots(figsize=(12, 7))

    # --- Left Y-Axis: Throughput (Bar Chart) ---
    color = 'tab:blue'
    ax1.set_xlabel('Virtual Users (VUs)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Throughput (Req/Sec)', color=color, fontsize=12, fontweight='bold')
    bars = ax1.bar(list(map(str, vus)), tps, color=color, alpha=0.6, label='Throughput')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                 f'{int(height)}',
                 ha='center', va='bottom', fontsize=9)

    # --- Right Y-Axis: Latency (Line Chart) ---
    ax2 = ax1.twinx()  
    
    # Plot P50, P95, P99
    ax2.set_ylabel('Latency (ms)', color='tab:red', fontsize=12, fontweight='bold')
    
    l1, = ax2.plot(list(map(str, vus)), p50, color='green', marker='o', linestyle='--', linewidth=2, label='P50 Latency')
    l2, = ax2.plot(list(map(str, vus)), p95, color='orange', marker='s', linestyle='-', linewidth=2, label='P95 Latency')
    l3, = ax2.plot(list(map(str, vus)), p99, color='red', marker='^', linestyle='-', linewidth=2, label='P99 Latency')

    ax2.tick_params(axis='y', labelcolor='tab:red')

    # Title and Layout
    plt.title(f'Load Test Results: Throughput vs Latency\n({DURATION_PER_TEST}s per test)', fontsize=14)
    
    # Combine legends
    lines = [bars, l1, l2, l3]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')

    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE)
    print(f"✅ Graph saved to {OUTPUT_IMAGE}")
    plt.show()

def main():
    print(f"🚀 Starting Benchmark on {BASE_URL}")
    print(f"💾 Saving data to {OUTPUT_CSV}")
    print("-" * 60)

    with open(OUTPUT_CSV, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["vus", "throughput", "avg", "p50", "p90", "p95", "p99"])

        for vus in VUS_LIST:
            print(f"Running test with {vus} VUs for {DURATION_PER_TEST}s...", end=" ", flush=True)
            
            all_latencies = []
            
            with ThreadPoolExecutor(max_workers=vus) as executor:
                futures = []
                for _ in range(vus):
                    futures.append(executor.submit(run_worker, DURATION_PER_TEST, all_latencies))
                wait(futures)

            metrics = calculate_metrics(vus, all_latencies, DURATION_PER_TEST)
            writer.writerow(metrics)
            
            tps = metrics[1]
            p95 = metrics[5]
            print(f"Done! TPS: {tps:.2f} | P95: {p95:.2f}ms")
            time.sleep(1)

    print("-" * 60)
    print("✅ Benchmark Complete.")
    
    # Call the graph generator automatically
    generate_graph()

if __name__ == "__main__":
    main()