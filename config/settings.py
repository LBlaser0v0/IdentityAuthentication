from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "app.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

JWT_SECRET = "course-project-demo-secret"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
AUTH_CODE_EXPIRE_MINUTES = 10

AUTH_SERVER_BASE = "http://127.0.0.1:8000"
CLIENT_APP_BASE = "http://127.0.0.1:8001"
RESOURCE_SERVER_BASE = "http://127.0.0.1:8002"

DEFAULT_CLIENT_ID = "course-client"
DEFAULT_CLIENT_SECRET = "course-client-secret"
DEFAULT_REDIRECT_URI = f"{CLIENT_APP_BASE}/callback"
