import base64
import hashlib
import secrets
from urllib.parse import urlencode

from config.settings import AUTH_SERVER_BASE, DEFAULT_CLIENT_ID, DEFAULT_PKCE_METHOD, DEFAULT_REDIRECT_URI


def build_pkce_pair(method: str = DEFAULT_PKCE_METHOD):
    verifier = secrets.token_urlsafe(48)
    if method == "S256":
        digest = hashlib.sha256(verifier.encode("utf-8")).digest()
        challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    else:
        challenge = verifier
    return verifier, challenge, method


def build_authorize_url(scope: str = "read:profile read:email", use_pkce: bool = False):
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": DEFAULT_CLIENT_ID,
        "redirect_uri": DEFAULT_REDIRECT_URI,
        "scope": scope,
        "state": state,
    }
    pkce_payload = None
    if use_pkce:
        verifier, challenge, method = build_pkce_pair()
        params["code_challenge"] = challenge
        params["code_challenge_method"] = method
        pkce_payload = {
            "code_verifier": verifier,
            "code_challenge": challenge,
            "code_challenge_method": method,
        }
    return f"{AUTH_SERVER_BASE}/authorize?{urlencode(params)}", state, pkce_payload
