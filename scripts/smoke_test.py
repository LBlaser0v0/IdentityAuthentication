import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def wait_until_ready(url: str, timeout: float = 20.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = httpx.get(url, timeout=2.0)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main():
    targets = [
        "http://127.0.0.1:8000/",
        "http://127.0.0.1:8001/",
        "http://127.0.0.1:8002/",
    ]
    for url in targets:
        ok = wait_until_ready(url)
        print(url, "OK" if ok else "FAILED")
        if not ok:
            raise SystemExit(1)
    print("smoke test passed")


if __name__ == "__main__":
    main()
