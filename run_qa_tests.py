import urllib.request
import json
import time
import os

def check_endpoint(url, name):
    print(f"Testing {name} ({url})...")
    start = time.time()
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read().decode('utf-8')
            elapsed = time.time() - start
            print(f"[{name}] SUCCESS - {response.status} (Took {elapsed:.2f}s)")
            return True, elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"[{name}] FAILED - {str(e)} (Took {elapsed:.2f}s)")
        return False, elapsed

if __name__ == "__main__":
    check_endpoint('http://localhost:3000/api/health', 'Health Check')
    check_endpoint('http://localhost:3000/api/system/status', 'System Status')
