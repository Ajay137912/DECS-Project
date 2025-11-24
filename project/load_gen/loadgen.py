import asyncio
import aiohttp
import time
import random
import argparse
import csv
from collections import Counter


class Stats:
    def __init__(self):
        self.latencies = []
        self.total_requests = 0
        self.successes = 0
        self.failures = 0

    def record(self, latency, success):
        self.total_requests += 1
        if success:
            self.successes += 1
            self.latencies.append(latency)
        else:
            self.failures += 1


def choose_key_uniform(keyspace_size):
    # Keys from 1..keyspace_size
    return random.randint(1, keyspace_size)


def build_popular_key_distribution(keyspace_size):
    """
    80-20 rule: 20% "hot" keys get 80% of traffic.
    We prebuild a list we can sample uniformly from.
    """
    hot_keys = int(0.2 * keyspace_size) or 1
    cold_keys = keyspace_size - hot_keys

    population = []
    # 80% of entries are hot keys
    hot_weight = 0.8
    cold_weight = 0.2

    hot_count = int(1000 * hot_weight)
    cold_count = int(1000 * cold_weight)

    for _ in range(hot_count):
        population.append(random.randint(1, hot_keys))

    for _ in range(cold_count):
        population.append(random.randint(hot_keys + 1, keyspace_size))

    return population


def choose_key_popular(population):
    return random.choice(population)


async def worker(session, base_url, workload, keyspace_size,
                 mixed_get_ratio, popular_population, stats, stop_event):
    """
    Repeatedly send requests until stop_event is set.
    """
    while not stop_event.is_set():
        try:
            # Choose workload
            if workload == "get_all":
                key = choose_key_uniform(keyspace_size)
                url = f"{base_url}/get"
                params = {"id": key}
                method = "GET"
                data = None

            elif workload == "put_all":
                key = choose_key_uniform(keyspace_size)
                url = f"{base_url}/set"
                params = {"id": key}
                value = f"val-{random.randint(1, 1_000_000)}"
                method = "POST"
                data = value

            elif workload == "get_popular":
                key = choose_key_popular(popular_population)
                url = f"{base_url}/get"
                params = {"id": key}
                method = "GET"
                data = None

            elif workload == "mixed":
                # Decide GET or PUT based on ratio
                r = random.random()
                if r < mixed_get_ratio:  # GET
                    key = choose_key_uniform(keyspace_size)
                    url = f"{base_url}/get"
                    params = {"id": key}
                    method = "GET"
                    data = None
                else:  # PUT
                    key = choose_key_uniform(keyspace_size)
                    url = f"{base_url}/set"
                    params = {"id": key}
                    value = f"val-{random.randint(1, 1_000_000)}"
                    method = "POST"
                    data = value
            else:
                raise ValueError(f"Unknown workload: {workload}")

            start = time.perf_counter()
            if method == "GET":
                async with session.get(url, params=params) as resp:
                    await resp.text()  # read body to completion
            else:
                async with session.post(url, params=params, data=data) as resp:
                    await resp.text()

            end = time.perf_counter()
            stats.record((end - start), True)

        except Exception as e:
            # You can optionally log e
            stats.record(0.0, False)


async def run_load_test(args):
    stats = Stats()
    stop_event = asyncio.Event()

    if args.workload == "get_popular":
        popular_population = build_popular_key_distribution(args.keyspace_size)
    else:
        popular_population = None

    timeout = aiohttp.ClientTimeout(total=None, connect=None, sock_read=None)
    connector = aiohttp.TCPConnector(limit=None)

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        workers = [
            asyncio.create_task(
                worker(
                    session,
                    args.base_url,
                    args.workload,
                    args.keyspace_size,
                    args.get_ratio,
                    popular_population,
                    stats,
                    stop_event,
                )
            )
            for _ in range(args.concurrency)
        ]

        start_time = time.time()
        await asyncio.sleep(args.duration)
        stop_event.set()
        await asyncio.gather(*workers, return_exceptions=True)
        end_time = time.time()

    test_duration = end_time - start_time
    throughput = stats.total_requests / test_duration if test_duration > 0 else 0.0
    avg_latency_ms = (
        (sum(stats.latencies) / len(stats.latencies)) * 1000
        if stats.latencies
        else 0.0
    )

    print("=== Load Test Summary ===")
    print(f"Workload       : {args.workload}")
    print(f"Concurrency    : {args.concurrency}")
    print(f"Duration (s)   : {test_duration:.2f}")
    print(f"Total requests : {stats.total_requests}")
    print(f"Successes      : {stats.successes}")
    print(f"Failures       : {stats.failures}")
    print(f"Throughput     : {throughput:.2f} req/s")
    print(f"Avg latency    : {avg_latency_ms:.2f} ms")

    # Save summary to CSV
    if args.output:
        with open(args.output, "a", newline="") as f:
            writer = csv.writer(f)
            # header only if file is empty
            f.seek(0, 2)
            if f.tell() == 0:
                writer.writerow(
                    [
                        "workload",
                        "concurrency",
                        "duration_s",
                        "total_requests",
                        "successes",
                        "failures",
                        "throughput_req_per_s",
                        "avg_latency_ms",
                    ]
                )
            writer.writerow(
                [
                    args.workload,
                    args.concurrency,
                    f"{test_duration:.2f}",
                    stats.total_requests,
                    stats.successes,
                    stats.failures,
                    f"{throughput:.2f}",
                    f"{avg_latency_ms:.2f}",
                ]
            )


def parse_args():
    parser = argparse.ArgumentParser(description="Key-Value Server Load Generator")
    parser.add_argument("--base-url", type=str, required=True,
                        help="Base URL, e.g. http://localhost:8080")
    parser.add_argument("--workload", type=str, required=True,
                        choices=["get_all", "put_all", "get_popular", "mixed"])
    parser.add_argument("--concurrency", type=int, required=True,
                        help="Number of concurrent workers")
    parser.add_argument("--duration", type=int, default=300,
                        help="Test duration in seconds (default 300s)")
    parser.add_argument("--keyspace-size", type=int, default=1000,
                        help="Number of distinct keys to use (default 1000)")
    parser.add_argument("--get-ratio", type=float, default=0.8,
                        help="Fraction of GETs in mixed workload (default 0.8)")
    parser.add_argument("--output", type=str, default=None,
                        help="CSV file to append results to")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_load_test(args))