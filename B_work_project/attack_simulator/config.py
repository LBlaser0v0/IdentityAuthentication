from dataclasses import dataclass
from pathlib import Path

from config.settings import (
    AUTH_SERVER_BASE,
    CLIENT_APP_BASE,
    DEFAULT_CLIENT_ID,
    DEFAULT_CLIENT_SECRET,
    DEFAULT_REDIRECT_URI,
    RESOURCE_SERVER_BASE,
)


@dataclass(frozen=True)
class SimulatorConfig:
    auth_server_base: str = AUTH_SERVER_BASE
    client_app_base: str = CLIENT_APP_BASE
    resource_server_base: str = RESOURCE_SERVER_BASE
    client_id: str = DEFAULT_CLIENT_ID
    client_secret: str = DEFAULT_CLIENT_SECRET
    redirect_uri: str = DEFAULT_REDIRECT_URI
    timeout_seconds: float = 10.0
    results_dir: Path = Path("attack_simulator/results")


DEFAULT_CONFIG = SimulatorConfig()

