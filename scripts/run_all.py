import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"

COMMANDS = [
    [str(PYTHON), "-m", "uvicorn", "auth_server.main:app", "--host", "127.0.0.1", "--port", "8000"],
    [str(PYTHON), "-m", "uvicorn", "client_app.main:app", "--host", "127.0.0.1", "--port", "8001"],
    [str(PYTHON), "-m", "uvicorn", "resource_server.main:app", "--host", "127.0.0.1", "--port", "8002"],
]


def main():
    processes = []
    try:
        for command in COMMANDS:
            processes.append(subprocess.Popen(command, cwd=ROOT))
        print("all services started")
        print("auth server: http://127.0.0.1:8000")
        print("client app: http://127.0.0.1:8001")
        print("resource server: http://127.0.0.1:8002")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("stopping services...")
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            process.wait(timeout=5)


if __name__ == "__main__":
    main()
