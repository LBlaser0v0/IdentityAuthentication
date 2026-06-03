from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import (
    AUTH_SERVER_BASE,
    CLIENT_APP_BASE,
    DEFAULT_CLIENT_ID,
    DEFAULT_CLIENT_SECRET,
    DEFAULT_REDIRECT_URI,
    ENABLE_PKCE,
    RESOURCE_SERVER_BASE,
)

print("[CONFIG CHECK]")
print(f"AUTH_SERVER_BASE={AUTH_SERVER_BASE}")
print(f"CLIENT_APP_BASE={CLIENT_APP_BASE}")
print(f"RESOURCE_SERVER_BASE={RESOURCE_SERVER_BASE}")
print(f"DEFAULT_CLIENT_ID={DEFAULT_CLIENT_ID}")
print(f"DEFAULT_REDIRECT_URI={DEFAULT_REDIRECT_URI}")
print(f"ENABLE_PKCE={ENABLE_PKCE}")
print("[OK] settings loaded")
print()
print("[NEXT STEPS]")
print("1. Run scripts/init_db.bat to rebuild database data when client_id or seed data changed.")
print("2. Run scripts/run_all.bat to start all three services.")
print("3. Open the client page and verify /profile, /email, /admin behavior.")
