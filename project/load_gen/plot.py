import csv
import sys  # <--- Import sys
from collections import defaultdict
import matplotlib.pyplot as plt

def read_results(path):
    data = []
    try:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Basic error handling for empty lines or headers
                if not row.get("concurrency"): continue
                
                row["concurrency"] = int(row["concurrency"])
                row["throughput_req_per_s"] = float(row["throughput_req_per_s"])
                row["avg_latency_ms"] = float(row["avg_latency_ms"])
                data.append(row)
    except FileNotFoundError:
        print(f"Error: File '{path}' not found.")
        sys.exit(1)
    return data

# ... (Keep group_by_workload, plot_throughput, and plot_latency EXACTLY the same) ...
def group_by_workload(data):
    grouped = defaultdict(list)
    for row in data:
        grouped[row["workload"]].append(row)
    for w in grouped:
        grouped[w].sort(key=lambda r: r["concurrency"])
    return grouped

def plot_throughput(grouped):
    plt.figure()
    for workload, rows in grouped.items():
        xs = [r["concurrency"] for r in rows]
        ys = [r["throughput_req_per_s"] for r in rows]
        plt.plot(xs, ys, marker="o", label=workload)
    plt.xlabel("Concurrency (threads/tasks)")
    plt.ylabel("Throughput (requests/sec)")
    plt.title("Throughput vs Load Level")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("throughput_vs_load.png")

def plot_latency(grouped):
    plt.figure()
    for workload, rows in grouped.items():
        xs = [r["concurrency"] for r in rows]
        ys = [r["avg_latency_ms"] for r in rows]
        plt.plot(xs, ys, marker="o", label=workload)
    plt.xlabel("Concurrency (threads/tasks)")
    plt.ylabel("Average response time (ms)")
    plt.title("Response Time vs Load Level")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("latency_vs_load.png")

if __name__ == "__main__":
    # Get filename from command line, default to 'results.csv'
    filename = "results.csv"
    if len(sys.argv) > 1:
        filename = sys.argv[1]

    print(f"Plotting data from: {filename}")
    data = read_results(filename)
    
    if not data:
        print("No data found in CSV.")
    else:
        grouped = group_by_workload(data)
        plot_throughput(grouped)
        plot_latency(grouped)
        print("Saved: throughput_vs_load.png, latency_vs_load.png")