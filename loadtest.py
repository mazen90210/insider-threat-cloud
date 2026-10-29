"""Simple load test (standard library only). Records the numbers needed for the report.

Usage:  python loadtest.py http://<DNS-or-IP>:5000/api/users 200 20
         (url, total requests, concurrent threads)
"""
import sys
import time
import statistics
import urllib.request
from concurrent.futures import ThreadPoolExecutor

url = sys.argv[1]
total = int(sys.argv[2]) if len(sys.argv) > 2 else 200
workers = int(sys.argv[3]) if len(sys.argv) > 3 else 20


def hit(_):
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            r.read()
            ok = r.status == 200
    except Exception:
        ok = False
    return time.perf_counter() - start, ok


t0 = time.perf_counter()
with ThreadPoolExecutor(max_workers=workers) as ex:
    results = list(ex.map(hit, range(total)))
elapsed = time.perf_counter() - t0

times = sorted(t * 1000 for t, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
if not times:
    sys.exit("All requests failed")
print(f"Requests: {total}  Concurrency: {workers}  Failed: {failed}")
print(f"Total time: {elapsed:.2f}s  Throughput: {total / elapsed:.1f} req/s")
print(f"Avg: {statistics.mean(times):.1f} ms  Median: {statistics.median(times):.1f} ms  "
      f"P95: {times[int(len(times) * 0.95) - 1]:.1f} ms  Max: {times[-1]:.1f} ms")
