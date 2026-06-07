import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import AUTH_SERVER_PORT, CLIENT_APP_PORT, RESOURCE_SERVER_PORT, SERVER_HOST

WINDOWS_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
POSIX_PYTHON = ROOT / ".venv" / "bin" / "python"
PYTHON = POSIX_PYTHON if POSIX_PYTHON.exists() else WINDOWS_PYTHON

COMMANDS = [
    [str(PYTHON), "-m", "uvicorn", "auth_server.main:app", "--host", SERVER_HOST, "--port", str(AUTH_SERVER_PORT)],
    [str(PYTHON), "-m", "uvicorn", "client_app.main:app", "--host", SERVER_HOST, "--port", str(CLIENT_APP_PORT)],
    [str(PYTHON), "-m", "uvicorn", "resource_server.main:app", "--host", SERVER_HOST, "--port", str(RESOURCE_SERVER_PORT)],
]


def main():
    processes = []
    try:
        for command in COMMANDS:
            processes.append(subprocess.Popen(command, cwd=ROOT))
        print("all services started")
        print(f"auth server: http://{SERVER_HOST}:{AUTH_SERVER_PORT}")
        print(f"client app: http://{SERVER_HOST}:{CLIENT_APP_PORT}")
        print(f"resource server: http://{SERVER_HOST}:{RESOURCE_SERVER_PORT}")
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
