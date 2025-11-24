import csv
import matplotlib.pyplot as plt

VUS = []
TPS = []
AVG = []

with open("results_delete_only.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if not row["vus"]:
            continue
        VUS.append(int(row["vus"]))
        TPS.append(float(row["tps"]))
        AVG.append(float(row["avg_ms"]))

# ----- Plot Throughput -----
plt.figure(figsize=(8,5))
plt.plot(VUS, TPS, marker="o")
plt.title("Throughput vs Virtual Users (VUs)")
plt.xlabel("Virtual Users (VUs)")
plt.ylabel("Throughput (req/sec)")
plt.grid(True)
plt.tight_layout()
plt.savefig("throughput_plot.png")
print("Saved throughput_plot.png")

# ----- Plot Average Latency -----
plt.figure(figsize=(8,5))
plt.plot(VUS, AVG, marker="o", color="orange")
plt.title("Average Latency vs Virtual Users (VUs)")
plt.xlabel("Virtual Users (VUs)")
plt.ylabel("Average Latency (ms)")
plt.grid(True)
plt.tight_layout()
plt.savefig("latency_plot.png")
print("Saved latency_plot.png")
