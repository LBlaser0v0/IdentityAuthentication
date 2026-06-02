import secrets
from urllib.parse import urlencode

from config.settings import AUTH_SERVER_BASE, DEFAULT_CLIENT_ID, DEFAULT_REDIRECT_URI


def build_authorize_url(scope: str = "read:profile read:email"):
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": DEFAULT_CLIENT_ID,
        "redirect_uri": DEFAULT_REDIRECT_URI,
        "scope": scope,
        "state": state,
    }
    return f"{AUTH_SERVER_BASE}/authorize?{urlencode(params)}", state
