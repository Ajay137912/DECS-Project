# Key-Value Store Server (C++ + PostgreSQL + k6 Load Testing)

This project is a simple high-performance **Key-Value Store** built in **C++**, backed by **PostgreSQL**, and exposed via a lightweight HTTP API using `cpp-httplib`.  
It includes an **LRU cache**, a **PostgreSQL connection pool**, and **k6 load-testing scripts** for GET, PUT, DELETE, and MIXED workloads.

---

## 🚀 Features
- Fast HTTP server using **cpp-httplib**
- PostgreSQL storage using **libpqxx**
- Built-in **connection pooling**
- **LRU in-memory cache** for fast GET responses
- Clean REST API: GET, POST/PUT, DELETE
- k6 scripts for performance benchmarking
- A full automation script (`run_all.sh`) that:
  - Runs all workloads
  - Captures CPU + Disk usage (vmstat, iostat)
  - Saves results to CSV
  - Exports k6 summary metrics

---

## 📦 Requirements

Install the following packages:

g++
libpqxx-dev
postgresql
k6
vmstat (from procps)
iostat (from sysstat)
jq


---

## API Endpoints
get, Insert, delete a value

## Load Testing
results_get_only.csv
results_put_only.csv
results_delete_only.csv
results_mixed.csv
each csv include:
vus,tps,avg_ms,p50_ms,p90_ms,p95_ms,p99_ms,cpu_util_pct,disk_util_pct

## Project Structure
server.cpp          → Main HTTP + DB server
dbpool.h            → PostgreSQL connection pool implementation
kvcache.h           → LRU cache
get_only.js         → GET workload benchmark
put_only.js         → PUT/POST workload benchmark
delete_only.js      → DELETE workload benchmark
mixed.js            → Mixed workload (GET/PUT/DELETE)
run_all.sh          → Automated benchmarking script
plot_results.py     → Python script to visualize performance
results*.csv        → Output from load tests
