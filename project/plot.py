import pandas as pd
import matplotlib.pyplot as plt
import sys

# 1. Get filename from command line, or use default
filename = sys.argv[1] if len(sys.argv) > 1 else 'benchmark.csv'

try:
    # 2. Read directly from the file
    df = pd.read_csv(filename)
except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    sys.exit(1)

# Calculate Error Rate for labeling
df['Error_Rate'] = (df['Fail_Count'] / (df['Success_Count'] + df['Fail_Count'])) * 100

# Setup the plot
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot Throughput (Left Y-Axis)
color = 'tab:blue'
ax1.set_xlabel('Virtual Users (Threads)')
ax1.set_ylabel('Throughput (req/sec)', color=color)
ax1.plot(df['Threads'], df['Throughput'], marker='o', color=color, linewidth=2, label='Throughput')
ax1.tick_params(axis='y', labelcolor=color)
ax1.grid(True, which='both', linestyle='--', alpha=0.5)

# Plot Latency (Right Y-Axis)
ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('P95 Latency (seconds)', color=color)
ax2.plot(df['Threads'], df['P95_Latency'], marker='x', linestyle='--', color=color, linewidth=2, label='P95 Latency')
ax2.tick_params(axis='y', labelcolor=color)

# Annotate Failure Points
for i, row in df.iterrows():
    if row['Fail_Count'] > 0:
        ax1.annotate(f"{row['Error_Rate']:.1f}% Fail", 
                     (row['Threads'], row['Throughput']), 
                     xytext=(0, -15), textcoords='offset points', 
                     ha='center', color='red', fontweight='bold')

plt.title(f'Scalability Test: Throughput vs Latency\nSource: {filename}')
fig.tight_layout()

# Show the plot
print("Displaying plot...")
plt.show()