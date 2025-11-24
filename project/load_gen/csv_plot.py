import pandas as pd
import matplotlib.pyplot as plt
import sys

# 1. Check arguments
if len(sys.argv) < 2:
    print("❌ Error: No CSV file provided.")
    print("Usage: python3 csv_plot.py <csv_file>")
    sys.exit(1)

csv_file = sys.argv[1]

try:
    # 2. Read CSV
    df = pd.read_csv(csv_file)
    print(f"✅ Successfully loaded: {csv_file}")
    
    # Strip whitespace from column names just in case
    df.columns = df.columns.str.strip()
    
    print("Columns found:", df.columns.tolist())

    # 3. Setup the Plot
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # --- Plot Throughput (TPS) on Left Y-Axis ---
    color = 'tab:blue'
    ax1.set_xlabel('VUs (Virtual Users)')
    ax1.set_ylabel('Throughput (TPS)', color=color)
    # Changed 'throughput' to 'tps' to match your CSV
    ax1.plot(df["vus"], df["tps"], marker='o', color=color, label='TPS')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # --- Plot Latency (Avg) on Right Y-Axis ---
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    color = 'tab:red'
    ax2.set_ylabel('Avg Latency (ms)', color=color)
    # Changed 'latency' to 'avg_ms' to match your CSV
    ax2.plot(df["vus"], df["avg_ms"], marker='x', linestyle='--', color=color, label='Avg Latency')
    ax2.tick_params(axis='y', labelcolor=color)

    # Title and Layout
    plt.title(f'Load Test Results: {csv_file}')
    fig.tight_layout()  # otherwise the right y-label is slightly clipped

    # 4. Save the plot
    output_img = csv_file.replace('.csv', '.png')
    plt.savefig(output_img)
    print(f"📈 Plot saved to: {output_img}")
    
    # Show plot (optional, works if you have a display)
    # plt.show()

except KeyError as e:
    print(f"\n❌ Column name error: {e}")
    print(f"   Available columns are: {list(df.columns)}")
    print("   Please update the script to match these column names.")
except Exception as e:
    print(f"❌ An error occurred: {e}")